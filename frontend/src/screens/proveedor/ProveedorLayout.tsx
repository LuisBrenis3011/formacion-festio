import { Link, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";

import { LayoutDashboard, Box, Package, User, CalendarDays, ClipboardCheck, Wallet, LineChart, LogOut, HelpCircle } from "lucide-react";

export function ProveedorLayout() {
  const location = useLocation();
  const { user, logout } = useAuth();

  const navItems = [
    { name: "Dashboard", path: "/proveedor/dashboard", icon: <LayoutDashboard size={20} /> },
    { name: "Analytics", path: "/proveedor/metricas", icon: <LineChart size={20} /> },
    { name: "Event Logistics", path: "/proveedor/operaciones", icon: <ClipboardCheck size={20} /> },
    { name: "Client Portal", path: "/proveedor/calendario", icon: <User size={20} /> },
    { name: "Integrations", path: "/proveedor/paquetes", icon: <Box size={20} /> },
    { name: "Settings", path: "/proveedor/perfil", icon: <Wallet size={20} /> },
  ];

  return (
    <div className="flex h-screen bg-slate-50 text-slate-900 font-sans">
      {/* Sidebar Light */}
      <aside className="w-64 bg-white border-r border-slate-200 flex flex-col z-10 py-6">
        <div className="px-6 pb-6">
          <h2 className="text-xl font-display font-bold text-purple-700 tracking-tight">
            EventFlow Pro
          </h2>
          <p className="text-[10px] text-slate-500 font-semibold uppercase mt-0.5 tracking-wider">Enterprise Tier</p>
        </div>

        <nav className="flex-1 px-4 space-y-1">
          {navItems.map((item) => {
            const isActive = location.pathname.startsWith(item.path);
            return (
              <Link
                key={item.name}
                to={item.path}
                className={`flex items-center space-x-3 px-4 py-2.5 rounded-xl transition-all duration-200 ${
                  isActive
                    ? "bg-purple-600 text-white font-medium shadow-md shadow-purple-600/20"
                    : "text-slate-500 hover:bg-slate-50 hover:text-slate-900"
                }`}
              >
                <span className={`${isActive ? "text-white" : "text-slate-400"}`}>{item.icon}</span>
                <span className="text-sm">{item.name}</span>
              </Link>
            );
          })}
        </nav>

        <div className="px-4 mt-8">
          <button className="w-full bg-purple-600 hover:bg-purple-700 text-white py-2.5 rounded-xl text-sm font-medium transition-colors shadow-md shadow-purple-600/20 mb-4">
            Create New Event
          </button>
        </div>

        <div className="px-4 space-y-1 pt-4 border-t border-slate-100">
          <Link to="/help" className="flex items-center space-x-3 px-4 py-2.5 rounded-xl text-slate-500 hover:bg-slate-50 hover:text-slate-900 transition-colors">
            <HelpCircle size={20} className="text-slate-400" />
            <span className="text-sm">Help Center</span>
          </Link>
          <button
            onClick={logout}
            className="flex items-center space-x-3 px-4 py-2.5 w-full rounded-xl text-red-500 hover:bg-red-50 hover:text-red-600 transition-colors"
          >
            <LogOut size={20} />
            <span className="text-sm">Logout</span>
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto bg-slate-50 relative z-0">
        <div className="max-w-6xl mx-auto p-8 relative z-10">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
