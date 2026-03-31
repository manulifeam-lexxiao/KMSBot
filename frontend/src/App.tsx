import { BrowserRouter, Routes, Route, NavLink, Navigate } from "react-router-dom";
import { ChatPage } from "./features/chat/ChatPage";
import { AdminPage } from "./features/admin/AdminPage";

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-shell">
        <aside className="sidebar">
          <div className="sidebar__brand">
            <div className="sidebar__logo-mark">
              <svg viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">
                <path d="M2 2h5v5H2zM9 2h5v5H9zM2 9h5v5H2zM9 9h5v5H9z" />
              </svg>
            </div>
            <span className="sidebar__name">KMSBot</span>
          </div>

          <nav className="sidebar__nav">
            <NavLink
              to="/chat"
              className={({ isActive }) =>
                `sidebar__link${isActive ? " sidebar__link--active" : ""}`
              }
            >
              <svg
                className="sidebar__link-icon"
                viewBox="0 0 16 16"
                fill="currentColor"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path d="M14 1H2a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h2v3l3-3h7a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1zm-1 8H5.83L4 10.83V9H2V2h11v7z" />
              </svg>
              Chat
            </NavLink>

            <NavLink
              to="/admin"
              className={({ isActive }) =>
                `sidebar__link${isActive ? " sidebar__link--active" : ""}`
              }
            >
              <svg
                className="sidebar__link-icon"
                viewBox="0 0 16 16"
                fill="currentColor"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path d="M7.5 1a.5.5 0 0 1 .5.5v.55a5.5 5.5 0 0 1 2.44 1.01l.39-.39a.5.5 0 0 1 .71.71l-.39.39A5.5 5.5 0 0 1 12.16 6H12.5a.5.5 0 0 1 0 1h-.34a5.5 5.5 0 0 1-1.01 2.44l.39.39a.5.5 0 0 1-.71.71l-.39-.39A5.5 5.5 0 0 1 8 11.16V11.5a.5.5 0 0 1-1 0v-.34A5.5 5.5 0 0 1 4.56 10.1l-.39.39a.5.5 0 0 1-.71-.71l.39-.39A5.5 5.5 0 0 1 2.84 7H2.5a.5.5 0 0 1 0-1h.34A5.5 5.5 0 0 1 3.85 3.56l-.39-.39a.5.5 0 0 1 .71-.71l.39.39A5.5 5.5 0 0 1 7 2.05V1.5a.5.5 0 0 1 .5-.5zM8 4a3.5 3.5 0 1 0 0 7A3.5 3.5 0 0 0 8 4zm0 1.5a2 2 0 1 1 0 4 2 2 0 0 1 0-4z" />
              </svg>
              Admin
            </NavLink>
          </nav>

          <div className="sidebar__footer">
            <span className="sidebar__footer-text">v0.1.0</span>
          </div>
        </aside>

        <main className="app-content">
          <Routes>
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/admin" element={<AdminPage />} />
            <Route path="*" element={<Navigate to="/chat" replace />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
