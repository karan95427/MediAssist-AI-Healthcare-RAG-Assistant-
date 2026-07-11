import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

type NavbarProps = {
  theme: "light" | "dark";
  onToggleTheme: () => void;
};

const navItems = [
  { label: "Chat", to: "/chat" },
  { label: "Upload", to: "/upload" },
  { label: "Dashboard", to: "/dashboard" },
];

function Navbar({ theme, onToggleTheme }: NavbarProps) {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/90 backdrop-blur dark:border-slate-800 dark:bg-slate-950/90">
      <div className="mx-auto flex h-[76px] max-w-7xl items-center justify-between gap-3 px-3 sm:px-5">
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-emerald-500 text-base font-bold text-white shadow-sm">
            MA
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-slate-950 dark:text-white">MediAssist AI</p>
            <p className="truncate text-xs text-slate-500 dark:text-slate-400">{user?.email ?? "Healthcare assistant"}</p>
          </div>
        </div>

        <nav className="hidden items-center rounded-full border border-slate-200 bg-slate-100 p-1 dark:border-slate-800 dark:bg-slate-900 sm:flex">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `rounded-full px-4 py-2 text-sm font-medium transition ${
                  isActive
                    ? "bg-white text-slate-950 shadow-sm dark:bg-slate-800 dark:text-white"
                    : "text-slate-600 hover:text-slate-950 dark:text-slate-400 dark:hover:text-white"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onToggleTheme}
            className="h-10 rounded-full border border-slate-200 px-3 text-sm font-medium text-slate-700 transition hover:border-emerald-300 hover:text-emerald-700 dark:border-slate-800 dark:text-slate-200 dark:hover:border-emerald-500 dark:hover:text-emerald-300"
            aria-label="Toggle color theme"
          >
            {theme === "dark" ? "Light" : "Dark"}
          </button>
          <button
            type="button"
            onClick={handleLogout}
            className="h-10 rounded-full bg-slate-950 px-4 text-sm font-semibold text-white transition hover:bg-slate-800 dark:bg-white dark:text-slate-950 dark:hover:bg-slate-200"
          >
            Logout
          </button>
        </div>
      </div>
    </header>
  );
}

export default Navbar;
