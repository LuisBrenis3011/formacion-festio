import { useState } from "react";
import { Check, ChevronRight, Star, MessageSquare } from "lucide-react";
import { money } from "@/lib/format";
import { ReviewsSection } from "./reviews-section";
import type { ProveedorRecomendado } from "../types";

type ProviderCardProps = {
  provider: ProveedorRecomendado;
  onSelect: () => void;
  disabled?: boolean;
  featured?: boolean;
  rank?: number;
};

function renderStars(rating: number) {
  const full = Math.round(rating);
  return Array.from({ length: 5 }, (_, i) => (
    <Star
      key={i}
      size={13}
      className={i < full ? "star-filled" : "star-empty"}
      fill={i < full ? "#f59e0b" : "none"}
      stroke={i < full ? "#f59e0b" : "#d1d5db"}
    />
  ));
}

export function ProviderCard({
  provider,
  onSelect,
  disabled = false,
  featured = false,
  rank = 0,
}: ProviderCardProps) {
  const [showReviews, setShowReviews] = useState(false);

  const rating = provider.calificacion_promedio;
  const items = provider.paquete.incluye;

  const badgeText = featured
    ? rank === 0
      ? "Más popular"
      : "Mejor valorado"
    : null;

  return (
    <div
      className={`provider-card${featured ? " featured" : ""}${disabled ? " disabled" : ""}`}
      onClick={onSelect}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onSelect();
        }
      }}
    >
      {badgeText && (
        <span className={`card-badge ${rank === 0 ? "badge-popular" : "badge-rated"}`}>
          {badgeText}
        </span>
      )}

      <h3 className="card-package-name">{provider.paquete.nombre}</h3>

      <span className="card-company">
        {provider.nombre_empresa}
        {provider.distrito && ` · ${provider.distrito}`}
      </span>

      {rating != null && rating > 0 ? (
        <div className="card-rating">
          <span className="card-stars">{renderStars(rating)}</span>
          {rating.toFixed(1)}
        </div>
      ) : (
        <div className="card-rating empty">
          Nuevo proveedor
        </div>
      )}

      {items.length > 0 && (
        <div className="card-includes">
          <span className="card-includes-label">Incluye</span>
          <ul className="card-includes-list">
            {items.slice(0, 4).map((item) => (
              <li key={item.servicio_producto_id}>
                <Check size={14} className="check" />
                {item.nombre}
                {item.cantidad > 1 && <span className="qty">×{item.cantidad}</span>}
              </li>
            ))}
            {items.length > 4 && (
              <li className="card-more">+{items.length - 4} más</li>
            )}
          </ul>
        </div>
      )}

      <div className="card-footer">
        <div>
          <span className="card-price-label">Precio base</span>
          <span className="card-price-value">{money.format(provider.paquete.precio_base)}</span>
        </div>
        <div className="card-actions-wrapper">
          <button 
            type="button" 
            className="btn-ver-resenas"
            aria-expanded={showReviews}
            aria-label={showReviews ? "Ocultar reseñas" : "Ver reseñas"}
            onClick={(e) => {
              e.stopPropagation();
              setShowReviews((current) => !current);
            }}
          >
            <MessageSquare size={14} /> Reseñas
          </button>
          <button className="card-cta" type="button" tabIndex={-1}>
            Ver paquete <ChevronRight size={16} />
          </button>
        </div>
      </div>

      {showReviews && (
        <div
          className="card-reviews-container"
          onClick={(e) => e.stopPropagation()}
          onKeyDown={(e) => e.stopPropagation()}
        >
          <ReviewsSection proveedorId={provider.proveedor_id} />
        </div>
      )}
    </div>
  );
}
