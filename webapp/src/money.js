// Деньги на клиенте: ввод в TON → nanoTON без float (строковая арифметика).
const NANO = 9;

export function tonToNano(text) {
  const s = String(text ?? "").trim().replace(",", ".");
  if (s === "") return null;
  if (!/^\d+(\.\d{1,9})?$/.test(s)) return undefined; // некорректный ввод
  const [int, frac = ""] = s.split(".");
  return Number(BigInt(int) * 10n ** BigInt(NANO) + BigInt(frac.padEnd(NANO, "0")));
}

export function nanoToTon(nano) {
  if (nano === null || nano === undefined || nano === "") return "";
  const n = BigInt(nano);
  const int = n / 10n ** BigInt(NANO);
  const frac = (n % 10n ** BigInt(NANO)).toString().padStart(NANO, "0").replace(/0+$/, "");
  return frac ? `${int}.${frac}` : `${int}`;
}

export const pct = (bps) => (bps === null || bps === undefined ? "—" : `${(bps / 100).toFixed(1)}%`);
export const pctToBps = (text) => {
  const s = String(text ?? "").trim().replace(",", ".");
  if (s === "") return null;
  const v = Number(s);
  return Number.isFinite(v) ? Math.round(v * 100) : undefined;
};

export const MARKET = { portals: "Portals", mrkt: "MRKT", tonnel: "Tonnel" };
export const CONF = { high: "высокое", med: "среднее", low: "низкое" };
export const BASIS = { model_backdrop: "модель+фон", model: "модель", collection: "коллекция" };
