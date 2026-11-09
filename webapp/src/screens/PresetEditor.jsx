import { useEffect, useState } from "react";
import { api } from "../api.js";
import { go } from "../router.js";
import { MARKET, nanoToTon, pctToBps, tonToNano } from "../money.js";
import { backButton, confirm, haptic } from "../telegram.js";

const list = (s) =>
  s
    .split(",")
    .map((x) => x.trim())
    .filter(Boolean);
const join = (a) => (a || []).join(", ");
const bpsText = (b) => (b == null ? "" : String(b / 100));
const pmText = (pm) => (pm == null ? "" : String(pm / 10));
const intOrNull = (s) => (String(s).trim() === "" ? null : Number.parseInt(s, 10));

function toForm(p) {
  const f = p?.filter || {};
  return {
    name: p?.name || "",
    enabled: p?.enabled ?? true,
    priority: String(p?.priority ?? 0),
    markets: f.markets || [],
    collections: join(f.collections),
    models: join(f.models),
    backdrops: join(f.backdrops),
    symbols: join(f.symbols),
    maxModelRarity: pmText(f.max_model_rarity_pm),
    maxBackdropRarity: pmText(f.max_backdrop_rarity_pm),
    numberMin: f.number?.min ?? "",
    numberMax: f.number?.max ?? "",
    digits: f.number?.max_distinct_digits ?? "",
    monochrome: f.monochrome_only || false,
    priceMin: nanoToTon(f.min_price_nano),
    priceMax: nanoToTon(f.max_price_nano),
    discount: bpsText(f.min_discount_bps),
    profit: nanoToTon(f.min_profit_nano),
    roi: bpsText(f.min_roi_bps),
    comparables: f.min_comparables ?? "",
    confidence: f.min_confidence || "med",
    exclude: { auctions: true, premarket: true, locked: true, bundles: true, too_good: true, ...f.exclude },
  };
}

function toPayload(v) {
  const money = { priceMin: tonToNano(v.priceMin), priceMax: tonToNano(v.priceMax), profit: tonToNano(v.profit) };
  const bad = Object.entries(money).filter(([, x]) => x === undefined).map(([k]) => k);
  if (bad.length) throw new Error("Суммы — числа в TON, до 9 знаков после точки.");
  const pm = (s) => (String(s).trim() === "" ? null : Math.round(Number(s) * 10));
  return {
    name: v.name.trim(),
    enabled: v.enabled,
    priority: intOrNull(v.priority) ?? 0,
    filter: {
      markets: v.markets,
      collections: list(v.collections),
      models: list(v.models),
      backdrops: list(v.backdrops),
      symbols: list(v.symbols),
      max_model_rarity_pm: pm(v.maxModelRarity),
      max_backdrop_rarity_pm: pm(v.maxBackdropRarity),
      number: {
        min: intOrNull(v.numberMin),
        max: intOrNull(v.numberMax),
        max_distinct_digits: intOrNull(v.digits),
      },
      monochrome_only: v.monochrome,
      min_price_nano: money.priceMin,
      max_price_nano: money.priceMax,
      min_discount_bps: pctToBps(v.discount),
      min_profit_nano: money.profit,
      min_roi_bps: pctToBps(v.roi),
      min_comparables: intOrNull(v.comparables),
      min_confidence: v.confidence,
      exclude: v.exclude,
    },
  };
}

function Field({ id, label, hint, ...props }) {
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <input id={id} name={id} {...props} />
      {hint && <small className="hint">{hint}</small>}
    </div>
  );
}

export default function PresetEditor({ id }) {
  const [v, setV] = useState(toForm(null));
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const set = (k) => (e) => setV({ ...v, [k]: e.target.type === "checkbox" ? e.target.checked : e.target.value });

  useEffect(() => backButton(() => go("/presets")), []);
  useEffect(() => {
    if (id) api.presets().then((all) => setV(toForm(all.find((p) => p.id === id)))).catch((e) => setError(e.message));
  }, [id]);

  const submit = async (e) => {
    e.preventDefault();
    if (!e.currentTarget.reportValidity()) return;
    setError("");
    try {
      const payload = toPayload(v);
      setSaving(true);
      if (id) await api.updatePreset(id, payload);
      else await api.createPreset(payload);
      haptic("success");
      go("/presets");
    } catch (err) {
      haptic("error");
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const remove = async () => {
    if (!(await confirm("Удалить пресет?"))) return;
    await api.deletePreset(id);
    go("/presets");
  };

  const toggleMarket = (m) =>
    setV({ ...v, markets: v.markets.includes(m) ? v.markets.filter((x) => x !== m) : [...v.markets, m] });

  return (
    <form onSubmit={submit} noValidate>
      <h1>{id ? "Пресет" : "Новый пресет"}</h1>
      <Field id="name" label="Название" required maxLength={64} value={v.name} onChange={set("name")} />
      <Field id="priority" label="Приоритет" type="number" inputMode="numeric" step="1" value={v.priority} onChange={set("priority")} hint="Больше — важнее" />
      <label className="check"><input type="checkbox" checked={v.enabled} onChange={set("enabled")} /> Включён</label>

      <fieldset>
        <legend>Маркеты (пусто — все)</legend>
        {Object.entries(MARKET).map(([m, title]) => (
          <label className="check" key={m}>
            <input type="checkbox" checked={v.markets.includes(m)} onChange={() => toggleMarket(m)} /> {title}
          </label>
        ))}
      </fieldset>

      <fieldset>
        <legend>Подарок</legend>
        <Field id="collections" label="Коллекции" value={v.collections} onChange={set("collections")} hint="Через запятую" />
        <Field id="models" label="Модели" value={v.models} onChange={set("models")} />
        <Field id="backdrops" label="Фоны" value={v.backdrops} onChange={set("backdrops")} />
        <Field id="symbols" label="Символы" value={v.symbols} onChange={set("symbols")} />
        <Field id="maxModelRarity" label="Редкость модели не выше, %" type="text" inputMode="decimal" pattern="\d+([.,]\d)?" value={v.maxModelRarity} onChange={set("maxModelRarity")} hint="Для MRKT редкость неизвестна — такие лоты не пройдут" />
        <Field id="maxBackdropRarity" label="Редкость фона не выше, %" type="text" inputMode="decimal" pattern="\d+([.,]\d)?" value={v.maxBackdropRarity} onChange={set("maxBackdropRarity")} />
        <Field id="numberMin" label="Номер от" type="number" inputMode="numeric" min="0" value={v.numberMin} onChange={set("numberMin")} />
        <Field id="numberMax" label="Номер до" type="number" inputMode="numeric" min="0" value={v.numberMax} onChange={set("numberMax")} />
        <Field id="digits" label="Не больше разных цифр в номере" type="number" inputMode="numeric" min="1" max="10" value={v.digits} onChange={set("digits")} hint="3 — «красивые» номера" />
        <label className="check"><input type="checkbox" checked={v.monochrome} onChange={set("monochrome")} /> Только монохром</label>
      </fieldset>

      <fieldset>
        <legend>Цена и выгода</legend>
        <Field id="priceMin" label="Цена с комиссией от, TON" type="text" inputMode="decimal" pattern="\d+([.,]\d{1,9})?" value={v.priceMin} onChange={set("priceMin")} />
        <Field id="priceMax" label="Цена с комиссией до, TON" type="text" inputMode="decimal" pattern="\d+([.,]\d{1,9})?" value={v.priceMax} onChange={set("priceMax")} />
        <Field id="discount" label="Ниже флора минимум, %" type="text" inputMode="decimal" pattern="\d+([.,]\d{1,2})?" value={v.discount} onChange={set("discount")} />
        <Field id="profit" label="Прибыль минимум, TON" type="text" inputMode="decimal" pattern="-?\d+([.,]\d{1,9})?" value={v.profit} onChange={set("profit")} hint="Оценка: комиссии не проверены" />
        <Field id="roi" label="ROI минимум, %" type="text" inputMode="decimal" pattern="-?\d+([.,]\d{1,2})?" value={v.roi} onChange={set("roi")} />
        <Field id="comparables" label="Сопоставимых минимум" type="number" inputMode="numeric" min="1" value={v.comparables} onChange={set("comparables")} />
        <div className="field">
          <label htmlFor="confidence">Доверие к флору не ниже</label>
          <select id="confidence" value={v.confidence} onChange={set("confidence")}>
            <option value="low">низкое</option>
            <option value="med">среднее</option>
            <option value="high">высокое</option>
          </select>
        </div>
      </fieldset>

      <fieldset>
        <legend>Исключить</legend>
        {[["auctions", "Аукционы"], ["premarket", "Пре-маркет"], ["locked", "Заблокированные"], ["bundles", "Пакеты"], ["too_good", "Слишком дёшево (< 25% флора)"]].map(([k, t]) => (
          <label className="check" key={k}>
            <input type="checkbox" checked={v.exclude[k]} onChange={(e) => setV({ ...v, exclude: { ...v.exclude, [k]: e.target.checked } })} /> {t}
          </label>
        ))}
      </fieldset>

      <fieldset>
        <legend>Режим</legend>
        <p className="hint">Только наблюдение. «С подтверждением» и «Авто» станут доступны после проверки комиссий и Этапа 7.</p>
      </fieldset>

      {error && <p className="error" role="alert">{error}</p>}
      <button className="button" type="submit" disabled={saving}>{saving ? "Сохраняю…" : "Сохранить"}</button>
      {id && <button className="button danger" type="button" onClick={remove}>Удалить</button>}
    </form>
  );
}
