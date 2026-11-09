import { useEffect, useRef, useState } from "react";
import { api, streamDeals } from "../api.js";
import { MARKET } from "../money.js";
import { haptic } from "../telegram.js";

const STATUS = { active: "", sold: "ПРОДАНО", skipped: "пропущено", gone: "снято" };

export function DealRow({ d }) {
  return (
    <a className={`row status-${d.status}`} href={`#/alert/${d.id}`}>
      <div className="row-main">
        <strong>
          {d.collection}
          {d.number != null ? ` #${d.number}` : ""}
        </strong>
        <span className="hint">
          {[d.model, d.backdrop].filter(Boolean).join(" · ")} · {MARKET[d.market]}
        </span>
      </div>
      <div className="row-side">
        <span>{d.price_ton} TON</span>
        {d.profit_ton && (
          <span className="profit">
            ~{d.profit_ton}
            {d.estimate ? "*" : ""}
          </span>
        )}
        {STATUS[d.status] && <span className="badge">{STATUS[d.status]}</span>}
      </div>
    </a>
  );
}

export default function Feed({ me }) {
  const [deals, setDeals] = useState([]);
  const [error, setError] = useState("");
  const [live, setLive] = useState(false);
  const lastId = useRef(0);

  useEffect(() => {
    if (!me) return undefined;
    const ctrl = new AbortController();
    let stopped = false;
    api
      .deals()
      .then((list) => {
        setDeals(list);
        lastId.current = list[0]?.id || 0;
        const loop = async () => {
          while (!stopped) {
            try {
              setLive(true);
              await streamDeals(
                lastId.current,
                (d) => {
                  lastId.current = Math.max(lastId.current, d.id);
                  setDeals((prev) => [d, ...prev.filter((x) => x.id !== d.id)]);
                  haptic("light");
                },
                ctrl.signal,
              );
            } catch {
              if (stopped) return;
            }
            setLive(false);
            await new Promise((r) => setTimeout(r, 3000));
          }
        };
        loop();
      })
      .catch((e) => setError(e.message));
    return () => {
      stopped = true;
      ctrl.abort();
    };
  }, [me]);

  return (
    <section>
      <h1>
        Сделки <span className="hint small">{live ? "● онлайн" : "○ переподключение"}</span>
      </h1>
      <p className="hint small">* прибыль — оценка: комиссии маркетов не проверены.</p>
      {error && <p className="error">{error}</p>}
      {!error && deals.length === 0 && (
        <p className="hint">Пока пусто. Сделки появятся, когда сработает включённый пресет.</p>
      )}
      <div className="list">
        {deals.map((d) => (
          <DealRow key={d.id} d={d} />
        ))}
      </div>
    </section>
  );
}
