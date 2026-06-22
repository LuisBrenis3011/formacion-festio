import { useState, useEffect, type FormEvent, type KeyboardEvent } from "react";
import { Star, Loader2, MessageSquare } from "lucide-react";
import { fetchResenas, crearResena } from "../api";
import { useAuth } from "../hooks/useAuth";
import type { ResenaPublicaOut } from "../types";

type ReviewsSectionProps = {
  proveedorId: number;
};

export function ReviewsSection({ proveedorId }: ReviewsSectionProps) {
  const [resenas, setResenas] = useState<ResenaPublicaOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [calificacion, setCalificacion] = useState(5);
  const [comentario, setComentario] = useState("");
  const { isAuthenticated, openAuthModal } = useAuth();

  useEffect(() => {
    setLoading(true);
    fetchResenas(proveedorId)
      .then(setResenas)
      .catch((err) => console.error("Error cargando reseñas:", err))
      .finally(() => setLoading(false));
  }, [proveedorId]);

  const submitReview = async () => {
    if (!comentario.trim()) return;

    if (!isAuthenticated) {
      openAuthModal("login");
      return;
    }

    try {
      setSubmitting(true);
      const nueva = await crearResena({
        proveedor_id: proveedorId,
        calificacion,
        comentario: comentario.trim(),
      });
      setResenas([nueva, ...resenas]);
      setComentario("");
      setCalificacion(5);
    } catch (err) {
      console.error("Error al enviar reseña:", err);
      alert("Hubo un error al enviar tu reseña. Por favor intenta nuevamente.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    void submitReview();
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    e.stopPropagation();
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void submitReview();
    }
  };

  return (
    <div className="reviews-section" onKeyDown={(e) => e.stopPropagation()}>
      <h4 className="reviews-title">
        <MessageSquare size={16} />
        Reseñas de clientes
      </h4>

      <form className="review-form" onSubmit={handleSubmit}>
        <div className="review-stars-input">
          {[1, 2, 3, 4, 5].map((star) => (
            <button
              type="button"
              key={star}
              className={`star-btn ${star <= calificacion ? "active" : ""}`}
              onClick={() => setCalificacion(star)}
            >
              <Star size={16} fill={star <= calificacion ? "currentColor" : "none"} />
            </button>
          ))}
        </div>
        <div className="review-input-group">
          <textarea
            placeholder="Escribe tu reseña y presiona Enter..."
            value={comentario}
            onChange={(e) => setComentario(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={submitting}
            rows={2}
          />
          <button 
            type="submit" 
            disabled={submitting || !comentario.trim()}
            className="submit-review-btn"
          >
            {submitting ? <Loader2 size={14} className="spin" /> : "Enviar"}
          </button>
        </div>
      </form>

      <div className="reviews-list">
        {loading ? (
          <div className="reviews-loading">Cargando reseñas...</div>
        ) : resenas.length === 0 ? (
          <div className="reviews-empty">Aún no hay reseñas para este proveedor.</div>
        ) : (
          resenas.map((r) => (
            <div key={r.id} className="review-item">
              <div className="review-header">
                <span className="review-author">{r.nombre_usuario}</span>
                <span className="review-date">
                  {new Date(r.fecha).toLocaleDateString()}
                </span>
              </div>
              <div className="review-stars">
                {[...Array(5)].map((_, i) => (
                  <Star
                    key={i}
                    size={12}
                    fill={i < r.calificacion ? "#eab308" : "none"}
                    color={i < r.calificacion ? "#eab308" : "#cbd5e1"}
                  />
                ))}
              </div>
              {r.comentario && <p className="review-text">{r.comentario}</p>}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
