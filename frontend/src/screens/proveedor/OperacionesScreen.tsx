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
    setReservas(reservas.map(r => r.id === id ? { ...r, estado: nuevoEstado } : r));
  };

  const handlePersonalChange = (id: string, personalId: string) => {
    setReservas(reservas.map(r => r.id === id ? { ...r, personalAsignado: personalId } : r));
  };

  const getStatusColor = (estado: string) => {
    switch (estado) {
      case "CONFIRMADA": return "bg-blue-100 text-blue-800";
      case "EN_CAMINO": return "bg-orange-100 text-orange-800";
      case "EN_PROGRESO": return "bg-purple-100 text-purple-800";
      case "FINALIZADA": return "bg-green-100 text-green-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-2xl font-display font-bold text-gray-900">Operaciones y Despacho</h2>
          <p className="text-gray-500 mt-1">Gestiona el estado de tus reservas y asigna personal a los eventos.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {reservas.map((reserva) => (
          <div key={reserva.id} className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden flex flex-col">
            <div className="p-5 border-b border-gray-100 flex-1 space-y-4">
              <div className="flex justify-between items-start">
                <div>
                  <span className="text-xs font-bold text-gray-400 uppercase">{reserva.id}</span>
                  <h3 className="font-semibold text-gray-900 leading-tight">{reserva.evento}</h3>
                  <p className="text-sm text-gray-500 mt-0.5">{reserva.cliente}</p>
                </div>
                <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${getStatusColor(reserva.estado)}`}>
                  {reserva.estado.replace("_", " ")}
                </span>
              </div>

              <div className="space-y-2 text-sm text-gray-600">
                <div className="flex items-center gap-2">
                  <CalendarClock size={16} className="text-gray-400" />
                  <span>{reserva.fecha}</span>
                </div>
                <div className="flex items-center gap-2">
                  <MapPin size={16} className="text-gray-400" />
                  <span className="truncate">{reserva.direccion}</span>
                </div>
              </div>

              {/* Asignación de Personal (Dispatch) */}
              <div className="pt-3 border-t border-gray-100">
                <label className="text-xs font-medium text-gray-700 flex items-center gap-1.5 mb-1.5">
                  <UserPlus size={14} /> Asignar Personal
                </label>
                <select 
                  className="w-full text-sm border-gray-300 rounded-md shadow-sm focus:border-primary focus:ring-primary bg-gray-50 p-2 border"
                  value={reserva.personalAsignado || ""}
                  onChange={(e) => handlePersonalChange(reserva.id, e.target.value)}
                  disabled={reserva.estado === "FINALIZADA"}
                >
                  <option value="" disabled>Seleccione un empleado...</option>
                  {personalMock.map(p => (
                    <option key={p.id} value={p.id}>{p.nombre} ({p.rol})</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Acciones de Cambio de Estado */}
            <div className="bg-gray-50 p-4">
              <label className="text-xs font-medium text-gray-500 block mb-2">Cambiar Estado Operativo</label>
              <div className="flex gap-2 overflow-x-auto pb-1">
                {reserva.estado === "CONFIRMADA" && (
                  <button 
                    onClick={() => handleEstadoChange(reserva.id, "EN_CAMINO")}
                    className="flex-1 text-xs font-medium bg-white border border-gray-200 text-gray-700 px-3 py-2 rounded shadow-sm hover:bg-gray-100 flex items-center justify-center gap-1 transition-colors whitespace-nowrap"
                  >
                    En Camino <ChevronRight size={14} />
                  </button>
                )}
                {reserva.estado === "EN_CAMINO" && (
                  <button 
                    onClick={() => handleEstadoChange(reserva.id, "EN_PROGRESO")}
                    className="flex-1 text-xs font-medium bg-white border border-gray-200 text-gray-700 px-3 py-2 rounded shadow-sm hover:bg-gray-100 flex items-center justify-center gap-1 transition-colors whitespace-nowrap"
                  >
                    Iniciar Show <ChevronRight size={14} />
                  </button>
                )}
                {reserva.estado === "EN_PROGRESO" && (
                  <button 
                    onClick={() => handleEstadoChange(reserva.id, "FINALIZADA")}
                    className="flex-1 text-xs font-medium bg-primary text-white px-3 py-2 rounded shadow-sm hover:bg-primary/90 flex items-center justify-center gap-1 transition-colors whitespace-nowrap"
                  >
                    <ClipboardCheck size={14} /> Finalizar
                  </button>
                )}
                {reserva.estado === "FINALIZADA" && (
                  <div className="w-full text-center text-xs font-medium text-green-700 py-1.5 flex items-center justify-center gap-1">
                    <ClipboardCheck size={14} /> Evento Concluido
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
