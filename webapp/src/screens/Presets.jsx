import { useEffect, useState } from "react";
import { api } from "../api.js";
import { haptic } from "../telegram.js";

export default function Presets() {
  const [items, setItems] = useState(null);
  const [error, setError] = useState("");

  const load = () => api.presets().then(setItems).catch((e) => setError(e.message));
  useEffect(() => {
    load();
  }, []);

  const toggle = async (p) => {
    try {
      await api.updatePreset(p.id, { enabled: !p.enabled });
      haptic("light");
      load();
    } catch (e) {
      setError(e.message);
    }
  };

  return (
    <section>
      <h1>Пресеты</h1>
      {error && <p className="error">{error}</p>}
      {items && items.length === 0 && <p className="hint">Нет пресетов — создайте первый.</p>}
      <div className="list">
        {(items || []).map((p) => (
          <div className="row" key={p.id}>
            <a className="row-main" href={`#/presets/${p.id}`}>
              <strong>{p.name}</strong>
              <span className="hint">
                приоритет {p.priority} · режим {p.mode}
              </span>
            </a>
            <label className="switch">
              <input
                type="checkbox"
                checked={p.enabled}
                onChange={() => toggle(p)}
                aria-label={`Включить пресет ${p.name}`}
              />
              <span>{p.enabled ? "вкл" : "выкл"}</span>
            </label>
          </div>
        ))}
      </div>
      <a className="button" href="#/presets/new">
        Новый пресет
      </a>
    </section>
  );
}
