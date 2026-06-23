import { useEffect, useState } from "react";
import { ArrowLeft, Loader2, ReceiptText, CalendarOff } from "lucide-react";
import { fetchMisReservas } from "../api";
import { money } from "../lib/format";
import type { MisReservasItem } from "../types";

type ReservasScreenProps = {
  onBack: () => void;
};

function formatReservationCode(reservationId: number) {
  const year = new Date().getFullYear();
  return `FEST-${year}-${String(reservationId).padStart(4, "0")}`;
}

export function ReservasScreen({ onBack }: ReservasScreenProps) {
  const [reservas, setReservas] = useState<MisReservasItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    fetchMisReservas()
      .then((data) => {
        if (mounted) setReservas(data);
      })
      .catch((err) => {
        if (mounted) setError(err.message);
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <main className="reservas-screen">
      <div className="reservas-header-actions">
        <button className="icon-button" type="button" onClick={onBack}>
          <ArrowLeft size={20} />
          <span>Volver</span>
        </button>
        <h2>Historial de Reservas</h2>
      </div>

      {loading ? (
        <div className="empty-state">
          <Loader2 className="spin" size={32} />
          <p>Cargando tus reservas...</p>
        </div>
      ) : error ? (
        <div className="empty-state">
          <p className="inline-error">{error}</p>
          <button className="primary-action" type="button" onClick={() => window.location.reload()}>
            Reintentar
          </button>
        </div>
      ) : reservas.length === 0 ? (
        <div className="empty-state">
          <CalendarOff size={48} opacity={0.3} />
          <p>Aún no tienes reservas registradas.</p>
          <button className="primary-action" type="button" onClick={onBack}>
            Explorar opciones
          </button>
        </div>
      ) : (
        <div className="reservas-list">
          {reservas.map((reserva) => (
            <div className="receipt-card" key={reserva.reserva_id}>
              <div className="receipt-header">
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                  <ReceiptText size={16} />
                  <span>Reserva {formatReservationCode(reserva.reserva_id)}</span>
                </div>
                <span className={`status-badge status-${reserva.estado.toLowerCase()}`}>
                  {reserva.estado}
                </span>
              </div>
              <div className="receipt-body">
                <div className="receipt-row">
                  <span>Evento</span>
                  <strong>{reserva.nombre_evento}</strong>
                </div>
                <div className="receipt-row">
                  <span>Proveedor</span>
                  <strong>{reserva.nombre_empresa}</strong>
                </div>
                <div className="receipt-row">
                  <span>Fecha y hora</span>
                  <strong>{reserva.fecha_evento_inicio.replace("T", " ")}</strong>
                </div>
                <div className="receipt-row">
                  <span>Dirección</span>
                  <strong>{reserva.direccion || "Por confirmar"}</strong>
                </div>

                {reserva.detalles.length > 0 && (
                  <>
                    <hr className="receipt-divider" />
                    {reserva.detalles.map((detail, idx) => (
                      <div className="receipt-row" key={`${detail.nombre}-${idx}`}>
                        <span>
                          {detail.nombre}
                          {detail.cantidad > 1 ? ` x${detail.cantidad}` : ""}
                        </span>
                        <strong>{money.format(detail.subtotal)}</strong>
                      </div>
                    ))}
                  </>
                )}

                <hr className="receipt-divider" />
                <div className="receipt-row receipt-total">
                  <span>Total</span>
                  <strong>{money.format(reserva.monto_total)}</strong>
                </div>
                <div className="receipt-row receipt-green">
                  <span>Adelanto pagado</span>
                  <strong>{money.format(reserva.monto_adelanto)}</strong>
                </div>
                <div className="receipt-row receipt-orange">
                  <span>Saldo pendiente</span>
                  <strong>{money.format(reserva.monto_pendiente)}</strong>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}
