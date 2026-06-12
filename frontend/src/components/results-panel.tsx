import { ArrowLeft, Sparkles } from "lucide-react";
import { ProviderCard } from "./provider-card";
import type { ProveedorRecomendado, RecomendacionResponse } from "../types";

type ResultsPanelProps = {
  recommendation: RecomendacionResponse;
  onSelectProvider: (provider: ProveedorRecomendado) => void;
  loadingDetail: boolean;
  onGoHome: () => void;
};

export function ResultsPanel({
  recommendation,
  onSelectProvider,
  loadingDetail,
  onGoHome,
}: ResultsPanelProps) {
  const principales = recommendation.resultados_principales;
  const otras = recommendation.otras_opciones;
  const tipoEvento =
    recommendation.estado_conversacion?.tipo_evento ?? "tu evento";
  const totalCount = principales.length + otras.length;

  return (
    <div className="results-panel">
      <div className="results-top-bar">
        <button className="ghost-button" type="button" onClick={onGoHome}>
          <ArrowLeft size={16} />
          Inicio
        </button>
      </div>

      <div className="results-header">
        <span className="results-eyebrow">
          <Sparkles size={14} />
          Resultados
        </span>
        <h2 className="results-title">
          Paquetes para{" "}
          <span className="highlight">{tipoEvento.toLowerCase()}</span>
        </h2>
        <p className="results-subtitle">
          {totalCount} {totalCount === 1 ? "opción encontrada" : "opciones encontradas"}
        </p>
      </div>

      {principales.length > 0 && (
        <div className="results-section">
          <span className="results-section-title">✨ Mejores coincidencias</span>
          <div className="results-grid">
            {principales.map((provider, i) => (
              <ProviderCard
                key={provider.proveedor_id}
                provider={provider}
                onSelect={() => onSelectProvider(provider)}
                disabled={loadingDetail}
                featured
                rank={i}
              />
            ))}
          </div>
        </div>
      )}

      {otras.length > 0 && (
        <div className="results-section">
          <span className="results-section-title">Otras alternativas</span>
          <div className="results-grid">
            {otras.map((provider, i) => (
              <ProviderCard
                key={provider.proveedor_id}
                provider={provider}
                onSelect={() => onSelectProvider(provider)}
                disabled={loadingDetail}
                rank={i}
              />
            ))}
          </div>
        </div>
      )}

      {principales.length === 0 && otras.length === 0 && (
        <div style={{ textAlign: "center", padding: "60px 20px", color: "var(--muted)" }}>
          <p style={{ fontSize: "1.1rem", fontWeight: 700 }}>
            No encontramos opciones para esta búsqueda.
          </p>
        </div>
      )}
    </div>
  );
}
