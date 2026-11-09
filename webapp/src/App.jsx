import { useEffect, useState } from "react";
import { api } from "./api.js";
import { inTelegram, ready } from "./telegram.js";
import Feed from "./screens/Feed.jsx";
import DealCard from "./screens/DealCard.jsx";
import Presets from "./screens/Presets.jsx";
import PresetEditor from "./screens/PresetEditor.jsx";
import Settings from "./screens/Settings.jsx";

function useHashRoute() {
  const [hash, setHash] = useState(window.location.hash || "#/");
  useEffect(() => {
    const on = () => setHash(window.location.hash || "#/");
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, []);
  return hash.replace(/^#/, "");
}

const TABS = [
  ["/", "Сделки"],
  ["/presets", "Пресеты"],
  ["/settings", "Режим"],
];

export default function App() {
  const route = useHashRoute();
  const [me, setMe] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    ready();
    if (!inTelegram()) {
      setError("Откройте приложение из бота в Telegram.");
      return;
    }
    api.me().then(setMe).catch((e) => setError(e.message));
  }, []);

  let screen;
  let m;
  if ((m = route.match(/^\/alert\/(\d+)/))) screen = <DealCard id={m[1]} />;
  else if (route === "/presets/new") screen = <PresetEditor />;
  else if ((m = route.match(/^\/presets\/(\d+)/))) screen = <PresetEditor id={Number(m[1])} />;
  else if (route.startsWith("/presets")) screen = <Presets />;
  else if (route.startsWith("/settings")) screen = <Settings me={me} onChange={setMe} />;
  else screen = <Feed me={me} />;

  const top = "/" + (route.split("/")[1] || "");
  const activeTab = top === "/alert" ? "/" : top;

  return (
    <div className="app">
      {me && (
        <div className="banner" role="status">
          Режим наблюдения · покупки выключены
          {me.panic ? " · 🛑 Panic" : me.paused ? " · ⏸ Пауза" : ""}
        </div>
      )}
      {error ? <p className="error">{error}</p> : screen}
      <nav className="tabs" aria-label="Разделы">
        {TABS.map(([path, title]) => (
          <a key={path} href={`#${path}`} aria-current={activeTab === path ? "page" : undefined}>
            {title}
          </a>
        ))}
      </nav>
    </div>
  );
}
