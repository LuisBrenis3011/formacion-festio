import { CheckCircle2, Home, ReceiptText } from "lucide-react";
import { money } from "../lib/format";
import type {
  CheckoutReservaResponse,
  EventDraft,
  PreReservaResponse,
  ProveedorRecomendado,
} from "../types";

type SuccessScreenProps = {
  confirmation: CheckoutReservaResponse;
  preReserva: PreReservaResponse | null;
  provider: ProveedorRecomendado | null;
  eventDraft: EventDraft;
  onBack: () => void;
};

function formatReservationCode(reservationId: number) {
  const year = new Date().getFullYear();
  return `FEST-${year}-${String(reservationId).padStart(4, "0")}`;
}

function formatEventDate(draft: EventDraft) {
  if (!draft.fecha) return "Por confirmar";
  const time = draft.horaInicio ? ` · ${draft.horaInicio}` : "";
  return `${draft.fecha}${time}`;
}

export function SuccessScreen({
  confirmation,
  preReserva,
  provider,
  eventDraft,
  onBack,
}: SuccessScreenProps) {
  const reservationCode = formatReservationCode(confirmation.reserva_id);
  const details = preReserva?.detalles ?? [];

  return (
    <main className="success-screen">
      <section className="success-card">
        <div className="success-icon">
          <CheckCircle2 size={34} />
        </div>
        <span>Reserva confirmada</span>
        <h1>Tu evento ya está separado</h1>
        <p>Guarda este comprobante para coordinar con el proveedor.</p>

        <div className="reservation-banner">
          <ReceiptText size={22} />
          <div>
            <small>Número de reserva</small>
            <strong>{reservationCode}</strong>
          </div>
        </div>

        <div className="receipt-card">
          <div className="receipt-header">
            <ReceiptText size={16} />
            Detalle del evento
          </div>
          <div className="receipt-body">
            <div className="receipt-row">
              <span>Proveedor</span>
              <strong>{provider?.nombre_empresa ?? "Proveedor asignado"}</strong>
            </div>
            <div className="receipt-row">
              <span>Paquete</span>
              <strong>{provider?.paquete.nombre ?? `Reserva #${confirmation.reserva_id}`}</strong>
            </div>
            <div className="receipt-row">
              <span>Fecha y hora</span>
              <strong>{formatEventDate(eventDraft)}</strong>
            </div>
            <div className="receipt-row">
              <span>Dirección</span>
              <strong>{eventDraft.direccion || "Por confirmar"}</strong>
            </div>

            {details.length > 0 && (
              <>
                <hr className="receipt-divider" />
                {details.map((detail) => (
                  <div
                    className="receipt-row"
                    key={`${detail.paquete_id ?? detail.servicio_producto_id}-${detail.nombre}`}
                  >
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
              <strong>{money.format(confirmation.monto_total)}</strong>
            </div>
            <div className="receipt-row receipt-green">
              <span>Adelanto pagado</span>
              <strong>{money.format(confirmation.monto_adelanto)}</strong>
            </div>
            <div className="receipt-row receipt-orange">
              <span>Saldo en local</span>
              <strong>{money.format(confirmation.monto_pendiente)}</strong>
            </div>
            <div className="receipt-row">
              <span>Comprobante</span>
              <strong>SIM-{confirmation.pago_id}</strong>
            </div>
          </div>
        </div>

        <div className="success-actions">
          <button className="primary-action" type="button" onClick={onBack}>
            <Home size={18} />
            Volver al chat
          </button>
        </div>
      </section>
    </main>
  );
}
