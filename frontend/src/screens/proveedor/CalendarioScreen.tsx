import { useState } from "react";
import { CalendarDays, Plus, Trash2, CalendarOff } from "lucide-react";

type Bloqueo = {
  id: string;
  fecha: string;
  motivo: string;
};

export function CalendarioScreen() {
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
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-2xl font-display font-bold text-gray-900">Gestión de Calendario</h2>
          <p className="text-gray-500 mt-1">Bloquea fechas para que no puedan ser reservadas por el Asistente Virtual.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Formulario de Bloqueo */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 lg:col-span-1 h-fit">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <CalendarOff size={18} />
            Nuevo Bloqueo Manual
          </h3>
          <form onSubmit={handleAdd} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Fecha a bloquear</label>
              <input 
                type="date" 
                value={fecha}
                onChange={(e) => setFecha(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Motivo (Opcional)</label>
              <input 
                type="text" 
                placeholder="Ej. Vacaciones, Mantenimiento..."
                value={motivo}
                onChange={(e) => setMotivo(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
              />
            </div>
            <button 
              type="submit"
              className="w-full flex justify-center items-center gap-2 bg-primary text-white px-4 py-2 rounded-lg hover:bg-primary/90 font-medium transition-colors"
            >
              <Plus size={18} />
              Agregar Bloqueo
            </button>
          </form>
        </div>

        {/* Lista de Bloqueos */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 lg:col-span-2">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <CalendarDays size={18} />
            Fechas Bloqueadas Próximamente
          </h3>
          
          {bloqueos.length === 0 ? (
            <div className="text-center py-10">
              <CalendarDays className="mx-auto h-12 w-12 text-gray-300 mb-3" />
              <h3 className="text-lg font-medium text-gray-900">Calendario Libre</h3>
              <p className="text-gray-500">No tienes ninguna fecha bloqueada actualmente.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="py-3 px-4 font-semibold text-sm text-gray-500">Fecha</th>
                    <th className="py-3 px-4 font-semibold text-sm text-gray-500">Motivo</th>
                    <th className="py-3 px-4 font-semibold text-sm text-gray-500 text-right">Acción</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {bloqueos.sort((a,b) => a.fecha.localeCompare(b.fecha)).map(b => (
                    <tr key={b.id} className="hover:bg-gray-50/50">
                      <td className="py-3 px-4 text-gray-900 font-medium">{b.fecha}</td>
                      <td className="py-3 px-4 text-gray-600">{b.motivo}</td>
                      <td className="py-3 px-4 text-right">
                        <button 
                          onClick={() => handleRemove(b.id)}
                          className="text-red-500 hover:text-red-700 hover:bg-red-50 p-2 rounded-md transition-colors"
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
  );
}
