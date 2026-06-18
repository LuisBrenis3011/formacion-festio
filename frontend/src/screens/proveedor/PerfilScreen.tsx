import { useEffect, useState } from "react";
import { proveedorService } from "../../services/proveedorService";
import type { ProveedorPerfil } from "../../types";

export function PerfilScreen() {
  const [perfil, setPerfil] = useState<ProveedorPerfil | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const [form, setForm] = useState<Partial<ProveedorPerfil>>({});

  useEffect(() => {
    async function loadPerfil() {
      try {
        const data = await proveedorService.getMiPerfil();
        setPerfil(data);
        setForm({
          nombre_empresa: data.nombre_empresa,
          descripcion: data.descripcion || "",
          distrito: data.distrito,
          capacidad_humana_total: data.capacidad_humana_total,
        });
      } catch (err: any) {
        setError(err.message || "Error al cargar perfil");
      } finally {
        setLoading(false);
      }
    }
    loadPerfil();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const updated = await proveedorService.updateMiPerfil(form);
      setPerfil(updated);
      setSuccessMsg("Perfil actualizado correctamente");
      setTimeout(() => setSuccessMsg(null), 3000);
    } catch (err: any) {
      setError(err.message || "Error al guardar el perfil");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div>Cargando perfil...</div>;
  if (!perfil) return <div className="text-red-500">No se pudo cargar el perfil</div>;

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-3xl font-display font-bold text-gray-900">Mi Perfil Público</h1>

      <div className="bg-white shadow-sm rounded-xl border border-gray-100 overflow-hidden">
        <div className="p-6 border-b border-gray-100 bg-gray-50 flex justify-between items-center">
          <div>
            <h2 className="text-xl font-bold text-gray-900">{perfil.nombre_empresa}</h2>
            <p className="text-sm text-gray-500">RUC: {perfil.ruc} | Estado: {perfil.estado_verificacion}</p>
          </div>
          <div className="text-right">
            <span className="text-2xl">⭐</span>
            <span className="font-bold text-lg ml-1">{perfil.calificacion_promedio}</span>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {error && <div className="p-3 bg-red-50 text-red-600 rounded-md text-sm">{error}</div>}
          {successMsg && <div className="p-3 bg-green-50 text-green-700 rounded-md text-sm font-medium">{successMsg}</div>}

          <div>
            <label className="block text-sm font-medium text-gray-700">Nombre de Empresa Comercial</label>
            <input
              type="text"
              required
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm p-2 border"
              value={form.nombre_empresa || ""}
              onChange={(e) => setForm({ ...form, nombre_empresa: e.target.value })}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Descripción / Biografía</label>
            <textarea
              rows={4}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm p-2 border"
              value={form.descripcion || ""}
              onChange={(e) => setForm({ ...form, descripcion: e.target.value })}
              placeholder="Cuéntale a los clientes sobre tu experiencia y la calidad de tus servicios..."
            />
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700">Distrito Principal</label>
              <input
                type="text"
                required
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm p-2 border"
                value={form.distrito || ""}
                onChange={(e) => setForm({ ...form, distrito: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Capacidad Humana Total</label>
              <input
                type="number"
                min="0"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm p-2 border"
                value={form.capacidad_humana_total || 0}
                onChange={(e) => setForm({ ...form, capacidad_humana_total: Number(e.target.value) })}
              />
              <p className="mt-1 text-xs text-gray-500">Máximo de personal simultáneo.</p>
            </div>
          </div>

          <div className="pt-4 flex justify-end border-t border-gray-100">
            <button
              type="submit"
              disabled={saving}
              className="px-6 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary hover:bg-primary/90 disabled:opacity-50"
            >
              {saving ? "Guardando..." : "Guardar Cambios"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
