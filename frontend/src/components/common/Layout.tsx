import { Link, useLocation } from "react-router-dom";
import { useAuthStore } from "../../store/authStore";

const navItems = [
  { path: "/", label: "Dashboard" },
  { path: "/portfolios", label: "Portfolios" },
  { path: "/debtors", label: "Debtors" },
  { path: "/court-cases", label: "Court Cases" },
  { path: "/analytics", label: "Analytics" },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const logout = useAuthStore((s) => s.logout);

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="w-64 bg-primary-900 text-white flex flex-col">
        <div className="p-6 border-b border-primary-700">
          <h1 className="text-xl font-bold">CourtCRM Pro</h1>
          <p className="text-sm text-primary-100 mt-1">NPL Management</p>
        </div>
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`block px-4 py-2 rounded-lg transition-colors ${
                location.pathname === item.path
                  ? "bg-primary-700 text-white"
                  : "text-primary-100 hover:bg-primary-700/50"
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="p-4 border-t border-primary-700">
          <button
            onClick={logout}
            className="w-full px-4 py-2 text-sm text-primary-100 hover:text-white hover:bg-primary-700/50 rounded-lg transition-colors"
          >
            Log out
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 p-8 overflow-auto">{children}</main>
    </div>
  );
}
