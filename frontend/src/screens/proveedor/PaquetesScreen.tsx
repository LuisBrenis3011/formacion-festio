import { useEffect, useState } from "react";
import { paquetesProveedorService } from "../../services/paquetesProveedorService";
import { inventarioService } from "../../services/inventarioService";
import { catalogoService } from "../../services/catalogoService";
import type { 
  Paquete, 
  ServicioProducto, 
  Categoria, 
  Tematica, 
  ProveedorPaqueteCreate,
  DetallePaqueteCreate
} from "../../types";

export function PaquetesScreen() {
  const [paquetes, setPaquetes] = useState<Paquete[]>([]);
  const [servicios, setServicios] = useState<ServicioProducto[]>([]);
  const [categorias, setCategorias] = useState<Categoria[]>([]);
  const [tematicas, setTematicas] = useState<Tematica[]>([]);
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  
  // Estado para armar la composición
  const [compoSeleccionada, setCompoSeleccionada] = useState<DetallePaqueteCreate[]>([]);
  const [servicioSeleccionadoId, setServicioSeleccionadoId] = useState<number>(0);
  const [cantidadSeleccionada, setCantidadSeleccionada] = useState<number>(1);

  const [form, setForm] = useState<ProveedorPaqueteCreate>({
    categoria_id: 0,
    tematica_id: null,
    nombre: "",
    descripcion: "",
    precio_base: 0,
    detalles: [],
  });

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [paqData, srvData, catData] = await Promise.all([
        paquetesProveedorService.listar(),
        inventarioService.listar(),
        catalogoService.listarCategorias(),
      ]);
      setPaquetes(paqData);
      setServicios(srvData);
      setCategorias(catData);
      if (catData.length > 0) {
        setForm(prev => ({ ...prev, categoria_id: catData[0].id }));
        cargarTematicas(catData[0].id);
      }
      if (srvData.length > 0) {
        setServicioSeleccionadoId(srvData[0].id);
      }
    } catch (err: any) {
      setError(err.message || "Error al cargar paquetes");
    } finally {
      setLoading(false);
    }
  }

  async function cargarTematicas(catId: number) {
    try {
      const temas = await catalogoService.listarTematicas(catId);
      setTematicas(temas);
      setForm(prev => ({ ...prev, tematica_id: temas.length > 0 ? temas[0].id : null }));
    } catch (e) {
      console.error(e);
    }
  }

  const handleCategoriaChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const catId = Number(e.target.value);
    setForm(prev => ({ ...prev, categoria_id: catId }));
    cargarTematicas(catId);
  };

  const agregarServicioACosposicion = () => {
    if (!servicioSeleccionadoId || cantidadSeleccionada < 1) return;
    
    // Evitar duplicados (actualizar cantidad)
    const existente = compoSeleccionada.find(d => d.servicio_producto_id === servicioSeleccionadoId);
    if (existente) {
      setCompoSeleccionada(compoSeleccionada.map(d => 
        d.servicio_producto_id === servicioSeleccionadoId 
          ? { ...d, cantidad_incluida: d.cantidad_incluida + cantidadSeleccionada }
          : d
      ));
    } else {
      setCompoSeleccionada([...compoSeleccionada, {
        servicio_producto_id: servicioSeleccionadoId,
        cantidad_incluida: cantidadSeleccionada
      }]);
    }
  };

  const quitarServicio = (id: number) => {
    setCompoSeleccionada(compoSeleccionada.filter(d => d.servicio_producto_id !== id));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (compoSeleccionada.length === 0) {
      alert("Debes incluir al menos un servicio en el paquete");
      return;
    }

    setSaving(true);
    try {
      const payload = {
        ...form,
        detalles: compoSeleccionada,
      };
      await paquetesProveedorService.crear(payload);
      setIsModalOpen(false);
      loadData();
      
      // Reset form
      setForm({
        ...form,
        nombre: "",
        descripcion: "",
        precio_base: 0,
        detalles: [],
      });
      setCompoSeleccionada([]);
      
    } catch (err: any) {
      alert(err.message || "Error al guardar el paquete");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("¿Seguro que deseas eliminar este paquete?")) return;
    try {
      await paquetesProveedorService.eliminar(id);
      loadData();
    } catch (err: any) {
      alert(err.message || "Error al eliminar");
    }
  };

  if (loading) return <div>Cargando paquetes...</div>;
  if (error) return <div className="text-red-500">{error}</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-display font-bold text-gray-900">Mis Paquetes Armados</h1>
        <button
          onClick={() => setIsModalOpen(true)}
          className="bg-primary text-white px-4 py-2 rounded-lg hover:bg-primary/90 transition-colors shadow-sm font-medium"
        >
          + Armar Paquete Nuevo
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {paquetes.length === 0 ? (
          <div className="col-span-full bg-white rounded-xl shadow-sm border border-gray-100 p-8 text-center text-gray-500">
            No tienes paquetes armados. Empieza combinando tus servicios de inventario.
          </div>
        ) : (
          paquetes.map((p) => {
            const cat = categorias.find(c => c.id === p.categoria_id);
            return (
              <div key={p.id} className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden flex flex-col">
                <div className="p-6 flex-1">
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-xs font-semibold uppercase tracking-wider text-primary bg-primary/10 px-2 py-1 rounded">
                      {cat?.nombre}
                    </span>
                    <span className="font-bold text-gray-900">S/ {p.precio_base}</span>
                  </div>
                  <h3 className="text-xl font-bold text-gray-900 mb-2">{p.nombre}</h3>
                  <p className="text-sm text-gray-500 line-clamp-2 mb-4">{p.descripcion}</p>
                  
                  <div className="space-y-2">
                    <h4 className="text-xs font-semibold text-gray-500 uppercase">Incluye:</h4>
                    <ul className="text-sm text-gray-600 space-y-1">
                      {p.detalles.map(d => (
                        <li key={d.id} className="flex items-center space-x-2">
                          <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
                          <span>{d.cantidad_incluida}x {d.servicio_nombre}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
                <div className="bg-gray-50 px-6 py-3 border-t border-gray-100 flex justify-end">
                  <button onClick={() => handleDelete(p.id)} className="text-red-600 hover:text-red-900 text-sm font-medium">
                    Eliminar
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-4xl overflow-hidden flex flex-col max-h-[90vh]">
            <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center bg-gray-50">
              <h3 className="text-lg font-medium text-gray-900">Armar Nuevo Paquete</h3>
              <button onClick={() => setIsModalOpen(false)} className="text-gray-400 hover:text-gray-500 text-2xl">&times;</button>
            </div>
            
            <form onSubmit={handleSubmit} className="p-6 overflow-y-auto grid grid-cols-1 md:grid-cols-2 gap-8">
              {/* Columna Izquierda: Datos del Paquete */}
              <div className="space-y-4">
                <h4 className="font-semibold text-gray-900 border-b pb-2">Información Principal</h4>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700">Nombre del Paquete</label>
                  <input
                    type="text"
                    required
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm p-2 border"
                    value={form.nombre}
                    onChange={(e) => setForm({ ...form, nombre: e.target.value })}
                  />
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Categoría</label>
                    <select
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm p-2 border"
                      value={form.categoria_id}
                      onChange={handleCategoriaChange}
                      required
                    >
                      {categorias.map(c => (
                        <option key={c.id} value={c.id}>{c.nombre}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Temática (Opcional)</label>
                    <select
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm p-2 border"
                      value={form.tematica_id || ""}
                      onChange={(e) => setForm({ ...form, tematica_id: e.target.value ? Number(e.target.value) : null })}
                    >
                      <option value="">-- Sin Temática --</option>
                      {tematicas.map(t => (
                        <option key={t.id} value={t.id}>{t.nombre}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Precio Total (S/)</label>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    required
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm p-2 border"
                    value={form.precio_base || ""}
                    onChange={(e) => setForm({ ...form, precio_base: Number(e.target.value) })}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Descripción Corta</label>
                  <textarea
                    rows={3}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm p-2 border"
                    value={form.descripcion || ""}
                    onChange={(e) => setForm({ ...form, descripcion: e.target.value })}
                  />
                </div>
              </div>

              {/* Columna Derecha: Composición */}
              <div className="space-y-4">
                <h4 className="font-semibold text-gray-900 border-b pb-2 flex justify-between">
                  <span>Composición del Paquete</span>
                  <span className="text-sm font-normal text-gray-500">({compoSeleccionada.length} items)</span>
                </h4>
                
                <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                  <div className="flex space-x-2">
                    <div className="flex-1">
                      <select
                        className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm p-2 border"
                        value={servicioSeleccionadoId}
                        onChange={(e) => setServicioSeleccionadoId(Number(e.target.value))}
                      >
                        {servicios.map(s => (
                          <option key={s.id} value={s.id}>{s.nombre} (S/{s.precio_unitario})</option>
                        ))}
                      </select>
                    </div>
                    <div className="w-20">
                      <input
                        type="number"
                        min="1"
                        className="block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm p-2 border"
                        value={cantidadSeleccionada}
                        onChange={(e) => setCantidadSeleccionada(Number(e.target.value))}
                      />
                    </div>
                    <button
                      type="button"
                      onClick={agregarServicioACosposicion}
                      className="bg-gray-800 text-white px-3 py-2 rounded-md hover:bg-gray-700 font-medium"
                    >
                      Añadir
                    </button>
                  </div>
                </div>

                {compoSeleccionada.length === 0 ? (
                  <p className="text-sm text-gray-500 italic py-4 text-center">
                    Aún no has añadido servicios al paquete.
                  </p>
                ) : (
                  <ul className="space-y-2 max-h-[200px] overflow-y-auto pr-2">
                    {compoSeleccionada.map(d => {
                      const srv = servicios.find(s => s.id === d.servicio_producto_id);
                      return (
                        <li key={d.servicio_producto_id} className="flex justify-between items-center bg-white p-3 border border-gray-200 rounded-md shadow-sm">
                          <div>
                            <span className="font-semibold text-primary">{d.cantidad_incluida}x</span>
                            <span className="ml-2 text-sm font-medium text-gray-900">{srv?.nombre}</span>
                          </div>
                          <button
                            type="button"
                            onClick={() => quitarServicio(d.servicio_producto_id)}
                            className="text-red-500 hover:text-red-700 text-xl font-bold"
                          >
                            &times;
                          </button>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>

              <div className="col-span-full pt-4 flex justify-end space-x-3 border-t border-gray-200 mt-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={saving || compoSeleccionada.length === 0}
                  className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary hover:bg-primary/90 disabled:opacity-50"
                >
                  {saving ? "Guardando..." : "Guardar Paquete"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
