import { useEffect, useState } from "react";
import { proveedorService } from "../../services/proveedorService";
import type { DashboardStats } from "../../types";
import { Link } from "react-router-dom";

export function DashboardScreen() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadStats() {
      try {
        const data = await proveedorService.getMiDashboard();
        setStats(data);
      } catch (err: any) {
        setError(err.message || "Error al cargar las estadísticas");
      } finally {
        setLoading(false);
      }
    }
    loadStats();
  }, []);

  if (loading) return <div>Cargando estadísticas...</div>;
  if (error) return <div className="text-red-500">{error}</div>;
  if (!stats) return null;

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-display font-bold text-gray-900">Dashboard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Card: Inventario */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex flex-col items-center justify-center space-y-2">
          <span className="text-4xl">📦</span>
          <h3 className="text-lg font-medium text-gray-500">Servicios Activos</h3>
          <p className="text-4xl font-bold text-gray-900">{stats.total_servicios}</p>
          <Link to="/proveedor/inventario" className="text-primary hover:underline text-sm mt-2">
            Gestionar inventario →
          </Link>
        </div>

        {/* Card: Paquetes */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex flex-col items-center justify-center space-y-2">
          <span className="text-4xl">🎁</span>
          <h3 className="text-lg font-medium text-gray-500">Paquetes Armados</h3>
          <p className="text-4xl font-bold text-gray-900">{stats.total_paquetes}</p>
          <Link to="/proveedor/paquetes" className="text-primary hover:underline text-sm mt-2">
            Gestionar paquetes →
          </Link>
        </div>

        {/* Card: Reservas */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex flex-col items-center justify-center space-y-2">
          <span className="text-4xl">📅</span>
          <h3 className="text-lg font-medium text-gray-500">Total Reservas</h3>
          <p className="text-4xl font-bold text-gray-900">{stats.total_reservas}</p>
        </div>
      </div>
    </div>
  );
}
