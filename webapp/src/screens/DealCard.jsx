import { useEffect, useState } from "react";
import { api } from "../api.js";
import { go } from "../router.js";
import { BASIS, CONF, MARKET, pct } from "../money.js";
import { backButton, openLink } from "../telegram.js";

function Sparkline({ points }) {
  if (points.length < 2) return <p className="hint">Мало продаж для графика ({points.length}).</p>;
  const ys = points.map((p) => Number(p.price_ton));
  const min = Math.min(...ys);
  const max = Math.max(...ys);
  const w = 300;
  const h = 80;
  const d = ys
    .map((y, i) => {
      const x = (i / (ys.length - 1)) * w;
      const yy = max === min ? h / 2 : h - ((y - min) / (max - min)) * (h - 8) - 4;
      return `${i ? "L" : "M"}${x.toFixed(1)},${yy.toFixed(1)}`;
    })
    .join(" ");
  return (
    <figure className="chart">
      <svg viewBox={`0 0 ${w} ${h}`} role="img" aria-label={`Продажи: от ${min} до ${max} TON`}>
        <path d={d} fill="none" stroke="currentColor" strokeWidth="2" />
      </svg>
      <figcaption className="hint small">
        {points.length} продаж за 7 дней · {min}–{max} TON
      </figcaption>
    </figure>
  );
}

export default function DealCard({ id }) {
  const [card, setCard] = useState(null);
  const [sales, setSales] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => backButton(() => go("/")), []);
  useEffect(() => {
    api.deal(id).then(setCard).catch((e) => setError(e.message));
    api.dealSales(id).then(setSales).catch(() => setSales([]));
  }, [id]);

  if (error) return <p className="error">{error}</p>;
  if (!card) return <p className="hint">Загрузка…</p>;
  const d = card.deal || {};
  const x = d.listing || {};
  const rar = x.rarity_pm || {};
  const r = (pm) => (pm == null ? "" : ` (${(pm / 10).toFixed(1)}%)`);

  return (
    <section>
      <h1>
        {x.collection}
        {x.number != null ? ` #${x.number}` : ""}
      </h1>
      <p className="hint">
        {MARKET[x.market]} · статус: {card.status}
      </p>
      <dl className="grid">
        <dt>Модель</dt>
        <dd>{x.model || "—"}{r(rar.model)}</dd>
        <dt>Фон</dt>
        <dd>{x.backdrop || "—"}{r(rar.backdrop)}</dd>
        <dt>Символ</dt>
        <dd>{x.symbol || "—"}{r(rar.symbol)}</dd>
        <dt>Цена</dt>
        <dd>{x.price?.ton} TON</dd>
        <dt>С комиссией</dt>
        <dd>{d.all_in?.ton} TON</dd>
        <dt>Ниже флора</dt>
        <dd>{pct(d.discount_bps)}</dd>
        <dt>Прибыль</dt>
        <dd>
          ~{d.profit?.ton ?? "—"} TON ({pct(d.roi_bps)})
          {d.estimate && <span className="hint small"> оценка, комиссии не проверены</span>}
        </dd>
      </dl>
      {(d.too_good || d.locked || d.cheaper_elsewhere || d.tg_above_value) && (
        <ul className="warnings">
          {d.too_good && <li>Цена ниже 25% флора — вероятная ловушка.</li>}
          {d.locked && <li>Подарок заблокирован для перепродажи.</li>}
          {d.cheaper_elsewhere && (
            <li>
              Дешевле на {MARKET[d.cheaper_elsewhere]}:{" "}
              {d.cheapest_elsewhere?.[d.cheaper_elsewhere]?.ton} TON с комиссией.
            </li>
          )}
          {d.tg_above_value && <li>Выше средней и последней продажи по оценке Telegram.</li>}
        </ul>
      )}
      <h2>Цены на маркетах</h2>
      <table className="markets">
        <thead>
          <tr>
            <th scope="col">Маркет</th>
            <th scope="col">Флор</th>
            <th scope="col">Продажа</th>
            <th scope="col">Чистыми</th>
          </tr>
        </thead>
        <tbody>
          {(d.options || []).map((o) => (
            <tr key={o.market} className={d.best?.market === o.market ? "best" : ""}>
              <th scope="row">{MARKET[o.market]}</th>
              <td>
                {o.floor.ton}
                <div className="hint small">
                  {BASIS[o.basis]}, {CONF[o.confidence]}, {o.comparables} шт.
                </div>
              </td>
              <td>
                {o.resale.ton}
                {o.capped_by_sales && <div className="hint small">медиана {o.sales_count} продаж</div>}
              </td>
              <td>{o.net.ton}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <h2>Продажи</h2>
      <Sparkline points={sales} />
      {x.url && (
        <button type="button" className="button" onClick={() => openLink(x.url)}>
          Открыть на маркете
        </button>
      )}
      <p className="hint small">Кнопки «Купить» нет: включается только после Этапа 7.</p>
    </section>
  );
}
