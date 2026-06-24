import { useState } from "react";
import { ClipboardCheck, UserPlus, MapPin, CalendarClock, ChevronRight } from "lucide-react";

type Personal = {
  id: string;
  nombre: string;
  rol: string;
};

type ReservaOp = {
  id: string;
  cliente: string;
  evento: string;
  fecha: string;
  direccion: string;
  estado: "CONFIRMADA" | "EN_CAMINO" | "EN_PROGRESO" | "FINALIZADA";
  personalAsignado: string | null;
};

export function OperacionesScreen() {
  const [personalMock] = useState<Personal[]>([
    { id: "p1", nombre: "Juan Pérez", rol: "Animador Principal" },
    { id: "p2", nombre: "Ana López", rol: "DJ" },
    { id: "p3", nombre: "Carlos Ruiz", rol: "Fotógrafo" },
  ]);

  const [reservas, setReservas] = useState<ReservaOp[]>([
    {
      id: "RES-001",
      cliente: "María García",
      evento: "Fiesta Infantil 5 años",
      fecha: "2026-07-20 15:00",
      direccion: "Av. Las Flores 123, Surco",
      estado: "CONFIRMADA",
      personalAsignado: null,
    },
    {
      id: "RES-002",
      cliente: "Pedro Sánchez",
      evento: "Matrimonio",
      fecha: "2026-07-22 20:00",
      direccion: "Local El Rosedal, La Molina",
      estado: "EN_CAMINO",
      personalAsignado: "p2",
    }
  ]);

  const handleEstadoChange = (id: string, nuevoEstado: ReservaOp["estado"]) => {
    // Aquí el backend hará un UPDATE en tabla 'reserva' (campo estado)
    // Y un INSERT en tabla 'notificacion' para avisar al cliente
    console.log(`[BACKEND MOCK] INSERT INTO notificacion (reserva_id, mensaje) VALUES ('${id}', 'El estado cambió a ${nuevoEstado}')`);
    setReservas(reservas.map(r => r.id === id ? { ...r, estado: nuevoEstado } : r));
  };

  const handlePersonalChange = (id: string, personalId: string) => {
    // Aquí el backend hará un INSERT/UPDATE en tabla puente 'detalle_reserva_personal'
    console.log(`[BACKEND MOCK] INSERT INTO detalle_reserva_personal (detalle_reserva_id, personal_id) VALUES ('...', '${personalId}')`);
    setReservas(reservas.map(r => r.id === id ? { ...r, personalAsignado: personalId } : r));
  };

  const getStatusColor = (estado: string) => {
    switch (estado) {
      case "CONFIRMADA": return "bg-slate-100 text-slate-600 border border-slate-200/60";
      case "EN_CAMINO": return "bg-orange-100 text-orange-600 border border-orange-200";
      case "EN_PROGRESO": return "bg-purple-100 text-purple-600 border border-purple-200";
      case "FINALIZADA": return "bg-emerald-100 text-emerald-600 border border-emerald-200";
      default: return "bg-slate-100 text-slate-600";
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-display font-bold text-slate-900 tracking-tight">Operaciones y Despacho</h2>
          <p className="text-slate-500 mt-1">Gestiona el estado de tus reservas y asigna personal a los eventos en tiempo real.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {reservas.map((reserva) => (
          <div key={reserva.id} className="bg-white rounded-2xl border border-slate-100/80 shadow-sm overflow-hidden flex flex-col">
            <div className="p-6 border-b border-slate-50 flex-1 space-y-5">
              <div className="flex justify-between items-start">
                <div>
                  <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">{reserva.id}</span>
                  <h3 className="font-bold text-slate-900 leading-tight mt-1">{reserva.evento}</h3>
                  <p className="text-xs text-slate-500 mt-0.5">{reserva.cliente}</p>
                </div>
                <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${getStatusColor(reserva.estado)}`}>
                  {reserva.estado.replace("_", " ")}
                </span>
              </div>

              <div className="space-y-2.5 text-sm text-slate-500">
                <div className="flex items-center gap-2.5">
                  <CalendarClock size={16} className="text-slate-400" />
                  <span>{reserva.fecha}</span>
                </div>
                <div className="flex items-center gap-2.5">
                  <MapPin size={16} className="text-slate-400" />
                  <span className="truncate">{reserva.direccion}</span>
                </div>
              </div>

              {/* Asignación de Personal (Dispatch) */}
              <div className="pt-4">
                <label className="text-xs font-semibold text-slate-700 flex items-center gap-1.5 mb-2">
                  <UserPlus size={14} className="text-slate-400" /> Asignar Personal
                </label>
                <select 
                  className="w-full text-sm border border-slate-200 rounded-xl shadow-sm focus:border-purple-500 focus:ring-1 focus:ring-purple-500 bg-slate-50 text-slate-700 p-2.5 outline-none cursor-pointer disabled:opacity-50 transition-colors"
                  value={reserva.personalAsignado || ""}
                  onChange={(e) => handlePersonalChange(reserva.id, e.target.value)}
                  disabled={reserva.estado === "FINALIZADA"}
                >
                  <option value="" disabled className="bg-white text-slate-500">Seleccione un empleado...</option>
                  {personalMock.map(p => (
                    <option key={p.id} value={p.id} className="bg-white">{p.nombre} ({p.rol})</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Acciones de Cambio de Estado */}
            <div className="bg-white p-6 pt-0">
              <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-3">Cambiar Estado Operativo</label>
              <div className="flex gap-2 overflow-x-auto">
                {reserva.estado === "CONFIRMADA" && (
                  <button 
                    onClick={() => handleEstadoChange(reserva.id, "EN_CAMINO")}
                    className="flex-1 text-sm font-medium bg-white border border-slate-200 text-slate-700 px-4 py-2.5 rounded-xl shadow-sm hover:bg-slate-50 flex items-center justify-center gap-1.5 transition-colors whitespace-nowrap"
                  >
                    En Camino <ChevronRight size={16} className="text-slate-400" />
                  </button>
                )}
                {reserva.estado === "EN_CAMINO" && (
                  <button 
                    onClick={() => handleEstadoChange(reserva.id, "EN_PROGRESO")}
                    className="flex-1 text-sm font-medium bg-purple-600 text-white px-4 py-2.5 rounded-xl shadow-md shadow-purple-600/20 hover:bg-purple-700 flex items-center justify-center gap-1.5 transition-colors whitespace-nowrap"
                  >
                    Iniciar Show <ChevronRight size={16} className="text-white/70" />
                  </button>
                )}
                {reserva.estado === "EN_PROGRESO" && (
                  <button 
                    onClick={() => handleEstadoChange(reserva.id, "FINALIZADA")}
                    className="flex-1 text-sm font-medium bg-emerald-500 text-white px-4 py-2.5 rounded-xl shadow-md shadow-emerald-500/20 hover:bg-emerald-600 flex items-center justify-center gap-1.5 transition-colors whitespace-nowrap"
                  >
                    <ClipboardCheck size={16} /> Finalizar
                  </button>
                )}
                {reserva.estado === "FINALIZADA" && (
                  <div className="w-full text-center text-sm font-medium text-emerald-600 py-2.5 flex items-center justify-center gap-1.5 bg-emerald-50 rounded-xl border border-emerald-100">
                    <ClipboardCheck size={16} /> Evento Concluido
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}

        {/* Empty state card similar to screenshot */}
        <div className="bg-white rounded-2xl border border-slate-100/60 shadow-sm flex flex-col justify-center items-center p-8 text-center min-h-[300px]">
          <div className="w-12 h-12 bg-slate-50 rounded-xl flex items-center justify-center mb-4">
            <ClipboardCheck size={24} className="text-slate-300" />
          </div>
          <h3 className="font-bold text-slate-900 mb-2">No hay más reservas pendientes</h3>
          <p className="text-sm text-slate-500 leading-relaxed max-w-[200px]">Las nuevas reservas confirmadas aparecerán aquí automáticamente.</p>
        </div>
      </div>
    </div>
  );
}
