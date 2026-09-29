import { useState } from "react";
import Login from "./Login";
import Dashboard from "./Dashboard";

export default function App() {
  const [session, setSession] = useState(null);
  const [commentHtml, setCommentHtml] = useState("");

  if (!session) {
    return <Login onLogin={setSession} />;
  }

  return (
    <Dashboard
      session={session}
      onLogout={() => setSession(null)}
      announcement={
        <div dangerouslySetInnerHTML={{ __html: commentHtml }} />
      }
    />
  );
}
