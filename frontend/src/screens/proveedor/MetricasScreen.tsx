import { LineChart, Star, Award, MessageSquare } from "lucide-react";

export function MetricasScreen() {
  const calificacionPromedio = 4.8;
  const totalResenas = 124;

  // Mapea a: GROUP BY paquete.id sobre tabla detalle_reserva cruzado con paquete
  const topPaquetes = [
    { nombre: "Show Infantil Premium", ventas: 45, porcentaje: 100 },
    { nombre: "Paquete Básico Animación", ventas: 28, porcentaje: 62 },
    { nombre: "Hora Loca Temática", ventas: 15, porcentaje: 33 },
  ];

  // Mapea a: SELECT de tabla 'resena' cruzada con 'reserva' o 'detalle_reserva'
  const resenasRecientes = [
    { id: 1, cliente: "María G.", estrellas: 5, comentario: "Excelente servicio, muy puntuales y los niños la pasaron genial.", fecha: "Hace 2 días" },
    { id: 2, cliente: "Pedro S.", estrellas: 4, comentario: "Muy buen show, aunque llegaron con la hora justa.", fecha: "Hace 1 semana" },
    { id: 3, cliente: "Ana L.", estrellas: 5, comentario: "100% recomendados, la animación fue de primera.", fecha: "Hace 2 semanas" },
  ];

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-display font-bold text-slate-900 tracking-tight">Market Analytics</h2>
          <p className="text-slate-500 mt-1">Review your service performance and customer satisfaction.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Panel de Calificación */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100/60 flex flex-col justify-center items-center text-center">
          <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-6 w-full text-left">Market Rating</h3>
          <div className="p-4 bg-yellow-50 rounded-full mb-4">
            <Star size={40} className="text-yellow-400 fill-current" />
          </div>
          <h3 className="text-5xl font-bold text-slate-900">{calificacionPromedio} <span className="text-xl text-slate-400">/ 5</span></h3>
          <p className="text-xs text-slate-400 mt-2 font-medium">Based on {totalResenas} verified reviews</p>
          <div className="flex mt-3 gap-1">
            {[1, 2, 3, 4, 5].map(i => (
              <Star key={i} size={20} className={i <= Math.round(calificacionPromedio) ? "text-yellow-400 fill-current" : "text-slate-200"} />
            ))}
          </div>
        </div>

        {/* Top Productos / Paquetes */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100/60 lg:col-span-2">
          <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-6 flex items-center gap-2">
            <Award size={18} className="text-purple-600" />
            Top 3 Best Selling Packages
          </h3>
          <div className="space-y-6">
            {topPaquetes.map((item, index) => (
              <div key={index}>
                <div className="flex justify-between text-sm font-medium mb-2">
                  <span className="text-slate-700">{item.nombre}</span>
                </div>
                <div className="w-full bg-purple-100 rounded-full h-3 overflow-hidden">
                  <div 
                    className="bg-purple-600 h-3 rounded-full" 
                    style={{ width: `${item.porcentaje}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Reseñas Recientes */}
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100/60">
        <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-6 flex items-center gap-2">
          <MessageSquare size={18} className="text-purple-600" />
          Recent Customer Reviews
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {resenasRecientes.map(resena => (
            <div key={resena.id} className="p-5 border border-slate-100/60 rounded-xl bg-white shadow-sm hover:shadow-md transition-shadow">
              <div className="flex justify-between items-start mb-2">
                <span className="font-semibold text-sm text-slate-900">{resena.cliente}</span>
                <span className="text-[10px] text-slate-400 font-medium uppercase tracking-wider">{resena.fecha}</span>
              </div>
              <div className="flex gap-0.5 mb-3">
                {[1, 2, 3, 4, 5].map(i => (
                  <Star key={i} size={14} className={i <= resena.estrellas ? "text-yellow-400 fill-current" : "text-slate-200"} />
                ))}
              </div>
              <p className="text-sm text-slate-500 italic leading-relaxed">"{resena.comentario}"</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
