import { useEffect, useState } from "react";
import { inventarioService } from "../../services/inventarioService";
import { catalogoService } from "../../services/catalogoService";
import type { ServicioProducto, Categoria, ProveedorServicioCreate } from "../../types";

export function InventarioScreen() {
  const [servicios, setServicios] = useState<ServicioProducto[]>([]);
  const [categorias, setCategorias] = useState<Categoria[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<ProveedorServicioCreate>({
    categoria_id: 0,
    nombre: "",
    tipo: "SERVICIO",
    requiere_persona: false,
    precio_unitario: 0,
    stock_maximo_simultaneo: 1,
    duracion_base_horas: null,
  });

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    try {
      const [srvData, catData] = await Promise.all([
        inventarioService.listar(),
        catalogoService.listarCategorias(),
      ]);
      setServicios(srvData);
      setCategorias(catData);
      if (catData.length > 0) {
        setForm(prev => ({ ...prev, categoria_id: catData[0].id }));
      }
    } catch (err: any) {
      setError(err.message || "Error al cargar datos");
    } finally {
      setLoading(false);
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await inventarioService.crear(form);
      setIsModalOpen(false);
      loadData();
      // Reset form
      setForm({
        ...form,
        nombre: "",
        precio_unitario: 0,
        stock_maximo_simultaneo: 1,
        duracion_base_horas: null,
      });
    } catch (err: any) {
      alert(err.message || "Error al guardar");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("¿Seguro que deseas eliminar este servicio?")) return;
    try {
      await inventarioService.eliminar(id);
      loadData();
    } catch (err: any) {
      alert(err.message || "Error al eliminar");
    }
  };

  if (loading) return <div>Cargando inventario...</div>;
  if (error) return <div className="text-red-500">{error}</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-display font-bold text-gray-900">Mi Inventario</h1>
        <button
          onClick={() => setIsModalOpen(true)}
          className="bg-primary text-white px-4 py-2 rounded-lg hover:bg-primary/90 transition-colors shadow-sm font-medium"
        >
          + Agregar Servicio/Producto
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nombre</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Categoría</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tipo</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Precio</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Stock Max.</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {servicios.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                  No tienes servicios en tu inventario aún.
                </td>
              </tr>
            ) : (
              servicios.map((s) => {
                const cat = categorias.find((c) => c.id === s.categoria_id);
                return (
                  <tr key={s.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{s.nombre}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{cat?.nombre}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${s.tipo === 'SERVICIO' ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800'}`}>
                        {s.tipo}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">S/ {s.precio_unitario}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{s.stock_maximo_simultaneo}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button onClick={() => handleDelete(s.id)} className="text-red-600 hover:text-red-900">
                        Eliminar
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center bg-gray-50">
              <h3 className="text-lg font-medium text-gray-900">Nuevo Item de Inventario</h3>
              <button onClick={() => setIsModalOpen(false)} className="text-gray-400 hover:text-gray-500 text-2xl">&times;</button>
            </div>
            
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Nombre</label>
                  <input
                    type="text"
                    required
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm p-2 border"
                    value={form.nombre}
                    onChange={(e) => setForm({ ...form, nombre: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Categoría</label>
                  <select
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm p-2 border"
                    value={form.categoria_id}
                    onChange={(e) => setForm({ ...form, categoria_id: Number(e.target.value) })}
                    required
                  >
                    {categorias.map(c => (
                      <option key={c.id} value={c.id}>{c.nombre}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Tipo</label>
                  <select
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm p-2 border"
                    value={form.tipo}
                    onChange={(e) => setForm({ ...form, tipo: e.target.value as "SERVICIO" | "PRODUCTO" })}
                  >
                    <option value="SERVICIO">Servicio</option>
                    <option value="PRODUCTO">Producto</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Precio Unitario (S/)</label>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    required
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm p-2 border"
                    value={form.precio_unitario || ""}
                    onChange={(e) => setForm({ ...form, precio_unitario: Number(e.target.value) })}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Stock Máximo Simultáneo</label>
                  <input
                    type="number"
                    min="1"
                    required
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm p-2 border"
                    value={form.stock_maximo_simultaneo || ""}
                    onChange={(e) => setForm({ ...form, stock_maximo_simultaneo: Number(e.target.value) })}
                  />
                  <p className="mt-1 text-xs text-gray-500">Importante: define tu capacidad real para el motor de IA.</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Duración base (Horas, opcional)</label>
                  <input
                    type="number"
                    min="0"
                    step="0.5"
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm p-2 border"
                    value={form.duracion_base_horas || ""}
                    onChange={(e) => setForm({ ...form, duracion_base_horas: Number(e.target.value) || null })}
                  />
                </div>
              </div>

              <div className="flex items-center mt-4">
                <input
                  id="requiere_persona"
                  type="checkbox"
                  className="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded"
                  checked={form.requiere_persona}
                  onChange={(e) => setForm({ ...form, requiere_persona: e.target.checked })}
                />
                <label htmlFor="requiere_persona" className="ml-2 block text-sm text-gray-900">
                  Requiere presencia de una persona (Ej: Animador, DJ)
                </label>
              </div>

              <div className="pt-4 flex justify-end space-x-3 border-t border-gray-200 mt-6">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary hover:bg-primary/90 disabled:opacity-50"
                >
                  {saving ? "Guardando..." : "Guardar Item"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
