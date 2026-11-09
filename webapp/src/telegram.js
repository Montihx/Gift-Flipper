// Обёртка над официальным telegram-web-app.js (подключён в index.html).
// Скрипт сам выставляет CSS-переменные --tg-theme-* из themeParams.
const tg = typeof window !== "undefined" ? window.Telegram?.WebApp : undefined;

export const initData = () => tg?.initData || "";
export const inTelegram = () => Boolean(tg?.initData);

export function ready() {
  tg?.ready();
  tg?.expand();
}

export function haptic(kind = "light") {
  const h = tg?.HapticFeedback;
  if (!h) return;
  if (kind === "success" || kind === "error" || kind === "warning") h.notificationOccurred(kind);
  else h.impactOccurred(kind);
}

export function backButton(onClick) {
  const b = tg?.BackButton;
  if (!b) return () => {};
  b.onClick(onClick);
  b.show();
  return () => {
    b.offClick(onClick);
    b.hide();
  };
}

export function mainButton(text, onClick) {
  const b = tg?.MainButton;
  if (!b) return () => {};
  b.setText(text);
  b.onClick(onClick);
  b.show();
  return () => {
    b.offClick(onClick);
    b.hide();
  };
}

export function confirm(message) {
  return new Promise((resolve) => {
    if (tg?.showConfirm) tg.showConfirm(message, resolve);
    else resolve(window.confirm(message));
  });
}

export function openLink(url) {
  if (url?.startsWith("https://t.me/") && tg?.openTelegramLink) tg.openTelegramLink(url);
  else if (tg?.openLink) tg.openLink(url);
  else window.open(url, "_blank", "noopener");
}
