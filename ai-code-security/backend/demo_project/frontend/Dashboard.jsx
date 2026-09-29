import { useEffect, useState } from "react";
import { getHealth, listExpenses } from "./api";
import { formatCurrency } from "./utils";

export default function Dashboard({ session, onLogout, announcement }) {
  const [expenses, setExpenses] = useState([]);
  const [status, setStatus] = useState("loading");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        await getHealth();
        const data = await listExpenses();
        if (!cancelled) {
          setExpenses(data);
          setStatus("ready");
        }
      } catch (err) {
        if (!cancelled) setStatus("error");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const total = expenses.reduce((sum, item) => sum + item.amount_cents, 0);

  return (
    <main className="dashboard">
      <header>
        <h1>FairShare</h1>
        <button type="button" onClick={onLogout}>Sign out</button>
      </header>
      {announcement}
      {status === "loading" && <p>Loading expenses…</p>}
      {status === "error" && <p className="error">Could not load expenses.</p>}
      {status === "ready" && (
        <>
          <p>Total: {formatCurrency(total)}</p>
          <ul>
            {expenses.map((item) => (
              <li key={item.id}>
                {item.description} — {formatCurrency(item.amount_cents)}
              </li>
            ))}
          </ul>
        </>
      )}
      <footer>Signed in as {session.email}</footer>
    </main>
  );
}
