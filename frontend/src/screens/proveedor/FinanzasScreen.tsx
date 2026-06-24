import { Wallet, TrendingUp, Clock, CreditCard, ArrowDownRight, ArrowUpRight } from "lucide-react";
import { money } from "../../lib/format";

type Transaccion = {
  id: string;
  reservaId: string;
  fecha: string;
  tipo: "Adelanto" | "Saldo Final";
  monto: number;
  estado: "Completado" | "Pendiente";
};

export function FinanzasScreen() {
  // Datos mockeados
  const metricas = {
    ingresosMes: 4500,
    saldoPendiente: 1200,
    totalGanado: 12500,
    crecimiento: 12.5 // porcentaje
  };

  const transacciones: Transaccion[] = [
    { id: "TRX-001", reservaId: "RES-001", fecha: "2026-07-10", tipo: "Adelanto", monto: 500, estado: "Completado" },
    { id: "TRX-002", reservaId: "RES-002", fecha: "2026-07-12", tipo: "Adelanto", monto: 800, estado: "Completado" },
    { id: "TRX-003", reservaId: "RES-001", fecha: "2026-07-20", tipo: "Saldo Final", monto: 500, estado: "Pendiente" },
    { id: "TRX-004", reservaId: "RES-002", fecha: "2026-07-22", tipo: "Saldo Final", monto: 700, estado: "Pendiente" },
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-2xl font-display font-bold text-gray-900">Módulo Financiero</h2>
          <p className="text-gray-500 mt-1">Controla tus ingresos, adelantos recibidos y saldos por cobrar.</p>
        </div>
      </div>

      {/* Tarjetas de Resumen */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex items-center space-x-4">
          <div className="p-3 bg-green-100 text-green-600 rounded-lg">
            <TrendingUp size={24} />
          </div>
          <div>
            <p className="text-sm font-medium text-gray-500">Ingresos del Mes</p>
            <div className="flex items-baseline gap-2">
              <h3 className="text-2xl font-bold text-gray-900">{money.format(metricas.ingresosMes)}</h3>
              <span className="text-xs font-semibold text-green-600 flex items-center">
                <ArrowUpRight size={14} /> {metricas.crecimiento}%
              </span>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex items-center space-x-4">
          <div className="p-3 bg-orange-100 text-orange-600 rounded-lg">
            <Clock size={24} />
          </div>
          <div>
            <p className="text-sm font-medium text-gray-500">Saldo Pendiente (Por cobrar)</p>
            <h3 className="text-2xl font-bold text-gray-900">{money.format(metricas.saldoPendiente)}</h3>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex items-center space-x-4">
          <div className="p-3 bg-blue-100 text-blue-600 rounded-lg">
            <Wallet size={24} />
          </div>
          <div>
            <p className="text-sm font-medium text-gray-500">Total Ganado (Histórico)</p>
            <h3 className="text-2xl font-bold text-gray-900">{money.format(metricas.totalGanado)}</h3>
          </div>
        </div>
      </div>

      {/* Tabla de Transacciones */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="px-6 py-5 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
          <h3 className="font-semibold text-gray-900 flex items-center gap-2">
            <CreditCard size={18} />
            Historial de Transacciones (Adelantos y Pagos)
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-white border-b border-gray-200">
                <th className="py-4 px-6 font-semibold text-sm text-gray-500">ID Transacción</th>
                <th className="py-4 px-6 font-semibold text-sm text-gray-500">Reserva Asoc.</th>
                <th className="py-4 px-6 font-semibold text-sm text-gray-500">Fecha</th>
                <th className="py-4 px-6 font-semibold text-sm text-gray-500">Concepto</th>
                <th className="py-4 px-6 font-semibold text-sm text-gray-500 text-right">Monto</th>
                <th className="py-4 px-6 font-semibold text-sm text-gray-500 text-center">Estado</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {transacciones.map(t => (
                <tr key={t.id} className="hover:bg-gray-50/50 transition-colors">
                  <td className="py-4 px-6 font-medium text-gray-900 text-sm">{t.id}</td>
                  <td className="py-4 px-6 text-sm text-gray-500">{t.reservaId}</td>
                  <td className="py-4 px-6 text-sm text-gray-500">{t.fecha}</td>
                  <td className="py-4 px-6 text-sm">
                    <span className="flex items-center gap-1.5 text-gray-700">
                      {t.tipo === "Adelanto" ? <ArrowDownRight size={14} className="text-green-500" /> : <Clock size={14} className="text-orange-500" />}
                      {t.tipo}
                    </span>
                  </td>
                  <td className="py-4 px-6 text-sm font-semibold text-gray-900 text-right">{money.format(t.monto)}</td>
                  <td className="py-4 px-6 text-sm text-center">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${
                      t.estado === "Completado" ? "bg-green-100 text-green-700" : "bg-orange-100 text-orange-700"
                    }`}>
                      {t.estado}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
