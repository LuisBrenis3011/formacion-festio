import { useState } from "react";
import { CalendarDays, Plus, Trash2, CalendarOff } from "lucide-react";

type Bloqueo = {
  id: string;
  // Mapea a la tabla: ocupacion_global_proveedor (campos: fecha_inicio, fecha_fin)
  fecha: string; 
  motivo: string;
};

export function CalendarioScreen() {
  // Estado que simula la tabla: ocupacion_global_proveedor
  const [bloqueos, setBloqueos] = useState<Bloqueo[]>([
    { id: "1", fecha: "2026-07-15", motivo: "Mantenimiento de equipos" },
    { id: "2", fecha: "2026-07-28", motivo: "Feriado Nacional" },
  ]);

  const [fecha, setFecha] = useState("");
  const [motivo, setMotivo] = useState("");

  const handleAdd = (e: React.FormEvent) => {
    e.preventDefault();
    if (!fecha) return;
    setBloqueos([...bloqueos, { id: Date.now().toString(), fecha, motivo: motivo || "No especificado" }]);
    setFecha("");
    setMotivo("");
  };

  const handleRemove = (id: string) => {
    setBloqueos(bloqueos.filter(b => b.id !== id));
  };

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-display font-bold text-slate-900 tracking-tight">Gestión de Calendario</h2>
          <p className="text-slate-500 mt-1">Bloquea fechas para que no puedan ser reservadas por el Asistente Virtual.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Formulario de Bloqueo */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100/60 lg:col-span-1 h-fit">
          <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-6 flex items-center gap-2">
            <CalendarOff size={18} className="text-purple-600" />
            Nuevo Bloqueo Manual
          </h3>
          <form onSubmit={handleAdd} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Fecha a bloquear</label>
              <input 
                type="date" 
                value={fecha}
                onChange={(e) => setFecha(e.target.value)}
                className="w-full px-4 py-2.5 bg-white border border-slate-200 text-slate-900 rounded-xl focus:ring-1 focus:ring-purple-500 focus:border-purple-500 outline-none transition-colors shadow-sm"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Motivo (Opcional)</label>
              <input 
                type="text" 
                placeholder="Ej. Vacaciones, Mantenimiento..."
                value={motivo}
                onChange={(e) => setMotivo(e.target.value)}
                className="w-full px-4 py-2.5 bg-white border border-slate-200 text-slate-900 rounded-xl focus:ring-1 focus:ring-purple-500 focus:border-purple-500 outline-none placeholder-slate-400 transition-colors shadow-sm"
              />
            </div>
            <button 
              type="submit"
              className="w-full flex justify-center items-center gap-2 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2.5 rounded-xl font-medium transition-colors shadow-md shadow-purple-600/20 mt-2"
            >
              <Plus size={18} />
              Agregar Bloqueo
            </button>
          </form>
        </div>

        {/* Lista de Bloqueos */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100/60 lg:col-span-2 overflow-hidden">
          <div className="px-6 py-5 border-b border-slate-100 flex justify-between items-center">
            <h3 className="font-bold text-slate-900 flex items-center gap-2">
              <CalendarDays size={18} className="text-purple-600" />
              Fechas Bloqueadas Próximamente
            </h3>
          </div>
          
          <div>
            {bloqueos.length === 0 ? (
              <div className="text-center py-12">
                <div className="w-12 h-12 bg-slate-50 rounded-xl flex items-center justify-center mx-auto mb-4">
                  <CalendarDays className="h-6 w-6 text-slate-300" />
                </div>
                <h3 className="text-lg font-bold text-slate-900">Calendario Libre</h3>
                <p className="text-sm text-slate-500 mt-1">No tienes ninguna fecha bloqueada actualmente.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-slate-50/50 border-b border-slate-100">
                      <th className="py-4 px-6 font-semibold text-xs text-slate-500 uppercase tracking-wider">Fecha</th>
                      <th className="py-4 px-6 font-semibold text-xs text-slate-500 uppercase tracking-wider">Motivo</th>
                      <th className="py-4 px-6 font-semibold text-xs text-slate-500 uppercase tracking-wider text-right">Acción</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {bloqueos.sort((a,b) => a.fecha.localeCompare(b.fecha)).map(b => (
                      <tr key={b.id} className="hover:bg-slate-50/50 transition-colors">
                        <td className="py-4 px-6 font-medium text-slate-900">{b.fecha}</td>
                        <td className="py-4 px-6 text-slate-500 text-sm">{b.motivo}</td>
                        <td className="py-4 px-6 text-right">
                          <button 
                            onClick={() => handleRemove(b.id)}
                            className="text-slate-400 hover:text-red-500 p-2 rounded-lg transition-colors hover:bg-red-50"
                            title="Eliminar bloqueo"
                          >
                            <Trash2 size={18} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
