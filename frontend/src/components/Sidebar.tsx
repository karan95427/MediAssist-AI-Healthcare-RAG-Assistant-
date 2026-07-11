import { NavLink } from "react-router-dom";

const navItems = [
  { label: "Dashboard", to: "/dashboard" },
  { label: "Chat", to: "/chat" },
  { label: "Upload Documents", to: "/upload" },
];

function Sidebar() {
  return (
    <aside className="flex w-full flex-col rounded-3xl bg-white p-6 shadow-panel lg:w-72">
      <div className="mb-8">
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-brand-600">MediAssist AI</p>
        <h1 className="mt-2 text-2xl font-semibold text-slate-900">Clinical Workspace</h1>
      </div>

      <nav className="space-y-2">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `block rounded-2xl px-4 py-3 text-sm font-medium transition ${
                isActive ? "bg-brand-600 text-white" : "text-slate-600 hover:bg-brand-50 hover:text-brand-700"
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}

export default Sidebar;
