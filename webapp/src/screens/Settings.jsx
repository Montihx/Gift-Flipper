import { useState } from "react";
import { api } from "../api.js";
import { MARKET } from "../money.js";
import { confirm, haptic } from "../telegram.js";

export default function Settings({ me, onChange }) {
  const [error, setError] = useState("");
  if (!me) return <p className="hint">Загрузка…</p>;

  const apply = async (state) => {
    try {
      const st = await api.setState(state);
      onChange({ ...me, ...st });
      haptic(state.panic ? "warning" : "light");
    } catch (e) {
      setError(e.message);
    }
  };
  const panic = async () => {
    if (await confirm("Panic: все пресеты в наблюдение и остановить уведомления?")) apply({ panic: true });
  };

  return (
    <section>
      <h1>Режим</h1>
      <dl className="grid">
        <dt>Покупки</dt>
        <dd>выключены (DRY_RUN={String(me.dry_run)})</dd>
        <dt>Уведомления</dt>
        <dd>{me.panic ? "Panic" : me.paused ? "на паузе" : "включены"}</dd>
      </dl>
      {me.paused || me.panic ? (
        <button className="button" type="button" onClick={() => apply({ panic: false })}>▶️ Продолжить</button>
      ) : (
        <button className="button" type="button" onClick={() => apply({ paused: true })}>⏸ Пауза</button>
      )}
      <button className="button danger" type="button" onClick={panic}>🛑 Panic</button>
      {error && <p className="error">{error}</p>}

      <h2>Комиссии</h2>
      <table className="markets">
        <thead>
          <tr><th scope="col">Маркет</th><th scope="col">Покупка</th><th scope="col">Продажа</th><th scope="col">Вывод</th></tr>
        </thead>
        <tbody>
          {Object.entries(me.fees).map(([m, f]) => (
            <tr key={m}>
              <th scope="row">{MARKET[m]}{f.verified ? "" : " *"}</th>
              <td>{f.buy_bps / 100}%</td>
              <td>{f.sell_bps / 100}%</td>
              <td>{f.withdraw_ton}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="hint small">* не проверено: прибыль везде — оценка. Режимы с покупкой включаются только после таблицы проверенных комиссий.</p>
    </section>
  );
}
