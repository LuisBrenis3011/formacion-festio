import { LineChart, Star, Award, MessageSquare } from "lucide-react";

export function MetricasScreen() {
  const calificacionPromedio = 4.8;
  const totalResenas = 124;

  const topPaquetes = [
    { nombre: "Show Infantil Premium", ventas: 45, porcentaje: 100 },
    { nombre: "Paquete Básico Animación", ventas: 28, porcentaje: 62 },
    { nombre: "Hora Loca Temática", ventas: 15, porcentaje: 33 },
  ];

  const resenasRecientes = [
    { id: 1, cliente: "María G.", estrellas: 5, comentario: "Excelente servicio, muy puntuales y los niños la pasaron genial.", fecha: "Hace 2 días" },
    { id: 2, cliente: "Pedro S.", estrellas: 4, comentario: "Muy buen show, aunque llegaron con la hora justa.", fecha: "Hace 1 semana" },
    { id: 3, cliente: "Ana L.", estrellas: 5, comentario: "100% recomendados, la animación fue de primera.", fecha: "Hace 2 semanas" },
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-2xl font-display font-bold text-gray-900">Inteligencia de Negocio</h2>
          <p className="text-gray-500 mt-1">Analiza el rendimiento de tus paquetes y la satisfacción de tus clientes.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Panel de Calificación */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex flex-col justify-center items-center text-center">
          <div className="p-4 bg-yellow-50 rounded-full mb-4">
            <Star size={40} className="text-yellow-400 fill-current" />
          </div>
          <h3 className="text-4xl font-bold text-gray-900">{calificacionPromedio} <span className="text-xl text-gray-400">/ 5</span></h3>
          <p className="text-sm text-gray-500 mt-2 font-medium">Basado en {totalResenas} reseñas verificadas</p>
          <div className="flex mt-3 gap-1">
            {[1, 2, 3, 4, 5].map(i => (
              <Star key={i} size={20} className={i <= Math.round(calificacionPromedio) ? "text-yellow-400 fill-current" : "text-gray-200"} />
            ))}
          </div>
        </div>

        {/* Top Productos / Paquetes */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 lg:col-span-2">
          <h3 className="font-semibold text-gray-900 mb-6 flex items-center gap-2">
            <Award size={18} className="text-primary" />
            Top 3 Paquetes Más Vendidos
          </h3>
          <div className="space-y-5">
            {topPaquetes.map((item, index) => (
              <div key={index}>
                <div className="flex justify-between text-sm font-medium mb-1.5">
                  <span className="text-gray-700">{item.nombre}</span>
                  <span className="text-gray-500">{item.ventas} reservas</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-2.5">
                  <div 
                    className="bg-primary h-2.5 rounded-full transition-all duration-500" 
                    style={{ width: `${item.porcentaje}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Reseñas Recientes */}
      <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
        <h3 className="font-semibold text-gray-900 mb-6 flex items-center gap-2">
          <MessageSquare size={18} className="text-blue-500" />
          Reseñas Recientes de Clientes
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {resenasRecientes.map(resena => (
            <div key={resena.id} className="p-5 border border-gray-100 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors">
              <div className="flex justify-between items-start mb-3">
                <span className="font-semibold text-sm text-gray-900">{resena.cliente}</span>
                <span className="text-xs text-gray-500">{resena.fecha}</span>
              </div>
              <div className="flex gap-0.5 mb-3">
                {[1, 2, 3, 4, 5].map(i => (
                  <Star key={i} size={14} className={i <= resena.estrellas ? "text-yellow-400 fill-current" : "text-gray-300"} />
                ))}
              </div>
              <p className="text-sm text-gray-600 italic">"{resena.comentario}"</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
