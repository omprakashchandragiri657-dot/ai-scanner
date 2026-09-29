import { useState } from "react";
import type { User } from "./types";
import { currency } from "./format";

interface Props {
  user: User;
  balanceCents: number;
  onSignOut: () => void;
}

export default function App({ user, balanceCents, onSignOut }: Props) {
  const [tab, setTab] = useState<"overview" | "history">("overview");

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>FairShare</h1>
        <span>{user.name}</span>
        <button type="button" onClick={onSignOut}>
          Sign out
        </button>
      </header>
      <nav>
        <button
          type="button"
          className={tab === "overview" ? "active" : ""}
          onClick={() => setTab("overview")}
        >
          Overview
        </button>
        <button
          type="button"
          className={tab === "history" ? "active" : ""}
          onClick={() => setTab("history")}
        >
          History
        </button>
      </nav>
      <section>
        <p>Balance: {currency(balanceCents)}</p>
      </section>
    </div>
  );
}
