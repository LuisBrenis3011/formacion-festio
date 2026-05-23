import { CheckCircle2 } from "lucide-react";
import { money } from "../lib/format";
import type { CheckoutReservaResponse } from "../types";

type SuccessScreenProps = {
  confirmation: CheckoutReservaResponse;
  onBack: () => void;
};

export function SuccessScreen({ confirmation, onBack }: SuccessScreenProps) {
  return (
    <main className="success-screen">
      <section className="success-card">
        <CheckCircle2 size={54} />
        <span>Reserva confirmada</span>
        <h1>Tu evento ya está separado</h1>
        <div className="success-grid">
          <div>
            <small>Comprobante</small>
            <strong>SIM-{confirmation.pago_id}</strong>
          </div>
          <div>
            <small>Reserva</small>
            <strong>#{confirmation.reserva_id}</strong>
          </div>
          <div>
            <small>Adelanto pagado</small>
            <strong>{money.format(confirmation.monto_adelanto)}</strong>
          </div>
          <div>
            <small>Saldo en local</small>
            <strong>{money.format(confirmation.monto_pendiente)}</strong>
          </div>
        </div>
        <button className="primary-action" type="button" onClick={onBack}>
          Volver al chat
        </button>
      </section>
    </main>
  );
}
