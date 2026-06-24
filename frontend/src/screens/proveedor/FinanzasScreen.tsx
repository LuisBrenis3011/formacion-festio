import { Wallet, TrendingUp, Clock, CreditCard, ArrowDownRight, ArrowUpRight } from "lucide-react";
import { money } from "../../lib/format";

// Representa un cruce entre tabla 'reserva', 'pago_transaccion' y 'comprobante'
type Transaccion = {
  id: string; // pago_transaccion.id
  reservaId: string;
  fecha: string;
  tipo: "Adelanto" | "Saldo Final"; // Representa pago_transaccion.tipo_transaccion
  monto: number; // pago_transaccion.monto
  estado: "Completado" | "Pendiente"; // pago_transaccion.estado
};

export function FinanzasScreen() {
  const metricas = {
    // Mapea a SUM(monto_adelanto) + SUM de saldos pagados
    ingresosMes: 4500,
    // Mapea a SUM(monto_pendiente) de la tabla 'reserva'
    monto_pendiente: 1200,
    totalGanado: 12500,
    crecimiento: 12.5
  };

  const transacciones: Transaccion[] = [
    { id: "TRX-001", reservaId: "RES-001", fecha: "2026-07-10", tipo: "Adelanto", monto: 500, estado: "Completado" },
    { id: "TRX-002", reservaId: "RES-002", fecha: "2026-07-12", tipo: "Adelanto", monto: 800, estado: "Completado" },
    { id: "TRX-003", reservaId: "RES-001", fecha: "2026-07-20", tipo: "Saldo Final", monto: 500, estado: "Pendiente" },
    { id: "TRX-004", reservaId: "RES-002", fecha: "2026-07-22", tipo: "Saldo Final", monto: 700, estado: "Pendiente" },
  ];

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-display font-bold text-slate-900 tracking-tight">Welcome back, EYM Eventos</h2>
          <p className="text-slate-500 mt-1">Here's what's happening with your business today.</p>
        </div>
      </div>

      {/* Tarjetas de Resumen */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100/60">
          <div className="flex items-center gap-2 mb-4">
            <div className="p-1.5 bg-emerald-100/50 rounded-full">
              <TrendingUp size={16} className="text-emerald-500" />
            </div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Monthly Income</p>
          </div>
          <div>
            <h3 className="text-4xl font-bold text-slate-900 tracking-tight mb-2">S/ {money.format(metricas.ingresosMes).replace('S/ ', '')}</h3>
            <span className="text-xs font-medium text-emerald-600 flex items-center">
              <ArrowUpRight size={14} className="mr-1" /> {metricas.crecimiento}% vs last month
            </span>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100/60">
          <div className="flex items-center gap-2 mb-4">
            <div className="p-1.5 bg-orange-100/50 rounded-full">
              <Clock size={16} className="text-orange-500" />
            </div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Pending Balance</p>
          </div>
          <div>
            <h3 className="text-4xl font-bold text-slate-900 tracking-tight mb-2">S/ {money.format(metricas.monto_pendiente).replace('S/ ', '')}</h3>
            <span className="inline-block px-2 py-0.5 bg-orange-100 text-orange-600 text-xs font-medium rounded">
              Action Required
            </span>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100/60">
          <div className="flex items-center gap-2 mb-4">
            <div className="p-1.5 bg-blue-100/50 rounded-full">
              <Wallet size={16} className="text-blue-500" />
            </div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Earned</p>
          </div>
          <div>
            <h3 className="text-4xl font-bold text-slate-900 tracking-tight mb-2">S/ {money.format(metricas.totalGanado).replace('S/ ', '')}</h3>
            <span className="text-xs font-medium text-slate-400">
              Historical
            </span>
          </div>
        </div>
      </div>

      {/* Tabla de Transacciones */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-100/60 overflow-hidden">
        <div className="px-6 py-5 border-b border-slate-100 flex justify-between items-center">
          <h3 className="font-bold text-slate-900 flex items-center gap-2">
            Recent Transactions
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/50 border-b border-slate-100">
                <th className="py-4 px-6 font-semibold text-xs text-slate-500 uppercase tracking-wider">Transaction ID</th>
                <th className="py-4 px-6 font-semibold text-xs text-slate-500 uppercase tracking-wider">Related Booking</th>
                <th className="py-4 px-6 font-semibold text-xs text-slate-500 uppercase tracking-wider">Date</th>
                <th className="py-4 px-6 font-semibold text-xs text-slate-500 uppercase tracking-wider">Type</th>
                <th className="py-4 px-6 font-semibold text-xs text-slate-500 uppercase tracking-wider text-right">Amount</th>
                <th className="py-4 px-6 font-semibold text-xs text-slate-500 uppercase tracking-wider text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {transacciones.map(t => (
                <tr key={t.id} className="hover:bg-slate-50/50 transition-colors">
                  <td className="py-4 px-6 font-medium text-slate-900 text-sm">{t.id}</td>
                  <td className="py-4 px-6 text-sm text-slate-500">{t.reservaId}</td>
                  <td className="py-4 px-6 text-sm text-slate-500">{t.fecha}</td>
                  <td className="py-4 px-6 text-sm">
                    <span className="flex items-center gap-1.5 text-slate-700">
                      {t.tipo === "Adelanto" ? <ArrowDownRight size={14} className="text-emerald-500" /> : <Clock size={14} className="text-orange-500" />}
                      {t.tipo}
                    </span>
                  </td>
                  <td className="py-4 px-6 text-sm font-semibold text-slate-900 text-right">S/ {money.format(t.monto).replace('S/ ', '')}</td>
                  <td className="py-4 px-6 text-sm text-center">
                    <span className={`px-2.5 py-1 rounded-md text-xs font-medium ${
                      t.estado === "Completado" 
                        ? "bg-emerald-50 text-emerald-600" 
                        : "bg-orange-50 text-orange-600"
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
