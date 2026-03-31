import { useEffect, useState } from "react";
import { ChatPage } from "./features/chat/ChatPage";
import { AdminPage } from "./features/admin/AdminPage";

type Page = "chat" | "admin";

function getPage(): Page {
  return window.location.hash === "#admin" ? "admin" : "chat";
}

export default function App() {
  const [page, setPage] = useState<Page>(getPage);

  useEffect(() => {
    const onHash = () => setPage(getPage());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  return (
    <>
      <nav className="app-nav">
        <a
          href="#chat"
          className={`app-nav__link${page === "chat" ? " app-nav__link--active" : ""}`}
        >
          Chat
        </a>
        <a
          href="#admin"
          className={`app-nav__link${page === "admin" ? " app-nav__link--active" : ""}`}
        >
          Admin
        </a>
      </nav>
      {page === "chat" ? <ChatPage /> : <AdminPage />}
    </>
  );
}
