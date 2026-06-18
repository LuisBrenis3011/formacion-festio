import { useState, useEffect } from "react";
import { Filter, Check, Building2, Tags } from "lucide-react";
import { listarProveedores, listarCategorias } from "../api";
import type { Categoria, ChatFilters, ProveedorPerfil } from "../types";

type FilterPanelProps = {
  filters: ChatFilters;
  onChange: (filters: ChatFilters) => void;
};

export function FilterPanel({ filters, onChange }: FilterPanelProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [proveedores, setProveedores] = useState<ProveedorPerfil[]>([]);
  const [categorias, setCategorias] = useState<Categoria[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && proveedores.length === 0) {
      setLoading(true);
      setError(null);
      Promise.all([listarProveedores(), listarCategorias()])
        .then(([provData, catData]) => {
          setProveedores(provData);
          setCategorias(catData);
        })
        .catch((err) => {
          console.error("Error cargando filtros:", err);
          setError("No se pudieron cargar los filtros.");
        })
        .finally(() => setLoading(false));
    }
  }, [isOpen, proveedores.length]);

  const toggleProveedor = (id: number) => {
    const nextIds = filters.proveedor_ids.includes(id)
      ? filters.proveedor_ids.filter((fid) => fid !== id)
      : [...filters.proveedor_ids, id];
    onChange({ ...filters, proveedor_ids: nextIds });
  };

  const toggleCategoria = (id: number) => {
    const nextIds = filters.categoria_ids.includes(id)
      ? filters.categoria_ids.filter((fid) => fid !== id)
      : [...filters.categoria_ids, id];
    onChange({ ...filters, categoria_ids: nextIds });
  };

  const clearFilters = () => {
    onChange({ proveedor_ids: [], categoria_ids: [] });
  };

  const activeCount = filters.proveedor_ids.length + filters.categoria_ids.length;

  return (
    <div className="filter-panel-wrapper">
      <button 
        type="button" 
        className={`filter-toggle-btn ${activeCount > 0 ? "active" : ""}`}
        onClick={() => setIsOpen(!isOpen)}
      >
        <Filter size={16} />
        <span>Filtros opcionales {activeCount > 0 && `(${activeCount})`}</span>
      </button>

      {isOpen && (
        <div className="filter-panel-content">
          <div className="filter-header">
            <h4>Ajustar Búsqueda</h4>
            {activeCount > 0 && (
              <button type="button" onClick={clearFilters} className="clear-filters-btn">
                Limpiar
              </button>
            )}
          </div>

          {loading ? (
            <div className="filter-loading">Cargando filtros...</div>
          ) : error ? (
            <div className="filter-loading error">{error}</div>
          ) : (
            <div className="filter-sections">
              <div className="filter-section">
                <div className="filter-section-title">
                  <Tags size={14} /> Categorías
                </div>
                <div className="filter-chips">
                  {categorias.map((cat) => {
                    const active = filters.categoria_ids.includes(cat.id);
                    return (
                      <button
                        key={`cat-${cat.id}`}
                        type="button"
                        className={`filter-chip ${active ? "active" : ""}`}
                        onClick={() => toggleCategoria(cat.id)}
                      >
                        {active && <Check size={12} />}
                        {cat.nombre}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="filter-section">
                <div className="filter-section-title">
                  <Building2 size={14} /> Empresas / Proveedores
                </div>
                <div className="filter-chips">
                  {proveedores.map((prov) => {
                    const active = filters.proveedor_ids.includes(prov.id);
                    return (
                      <button
                        key={`prov-${prov.id}`}
                        type="button"
                        className={`filter-chip ${active ? "active" : ""}`}
                        onClick={() => toggleProveedor(prov.id)}
                      >
                        {active && <Check size={12} />}
                        {prov.nombre_empresa}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
