import { Link, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";

export function ProveedorLayout() {
  const location = useLocation();
  const { user, logout } = useAuth();

  const navItems = [
    { name: "Dashboard", path: "/proveedor/dashboard", icon: "📊" },
    { name: "Inventario", path: "/proveedor/inventario", icon: "📦" },
    { name: "Mis Paquetes", path: "/proveedor/paquetes", icon: "🎁" },
    { name: "Mi Perfil", path: "/proveedor/perfil", icon: "⚙️" },
  ];

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-64 bg-white shadow-md flex flex-col">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-2xl font-display font-bold text-gray-900">
            Festio <span className="text-primary">B2B</span>
          </h2>
          <p className="text-sm text-gray-500 mt-1">{user?.nombre_empresa || user?.nombre}</p>
        </div>

        <nav className="flex-1 px-4 py-6 space-y-2">
          {navItems.map((item) => (
            <Link
              key={item.name}
              to={item.path}
              className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                location.pathname.startsWith(item.path)
                  ? "bg-primary/10 text-primary font-medium"
                  : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
              }`}
            >
              <span className="text-xl">{item.icon}</span>
              <span>{item.name}</span>
            </Link>
          ))}
        </nav>

        <div className="p-4 border-t border-gray-200">
          <button
            onClick={logout}
            className="flex items-center space-x-3 px-4 py-3 w-full rounded-lg text-red-600 hover:bg-red-50 transition-colors"
          >
            <span className="text-xl">🚪</span>
            <span>Cerrar Sesión</span>
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto bg-gray-50 p-8">
        <div className="max-w-6xl mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
