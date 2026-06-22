import { useState } from "react";
import { CreditCard, Smartphone, Banknote } from "lucide-react";

export type PaymentDetailsData = {
  // Tarjeta
  banco?: string;
  tipoTarjeta?: string;
  numeroTarjeta?: string;
  cvv?: string;
  nombreTitular?: string;
  fechaVencimiento?: string;
  // Yape / Plin
  numeroCelular?: string;
  codigoAprobacion?: string;
};

type PaymentDetailsFormProps = {
  metodoPago: string;
  details: PaymentDetailsData;
  onChange: (details: PaymentDetailsData) => void;
};

export function PaymentDetailsForm({ metodoPago, details, onChange }: PaymentDetailsFormProps) {
  const update = (field: keyof PaymentDetailsData, value: string) => {
    onChange({ ...details, [field]: value });
  };

  if (metodoPago === "TARJETA") {
    return (
      <div className="payment-details-section">
        <div className="payment-details-title">
          <CreditCard size={14} />
          Datos de la tarjeta
        </div>
        <div className="payment-details-fields">
          <label>
            <span>Banco</span>
            <select
              value={details.banco ?? ""}
              onChange={(e) => update("banco", e.target.value)}
              required
            >
              <option value="">Seleccionar...</option>
              <option value="BCP">BCP</option>
              <option value="BBVA">BBVA</option>
              <option value="INTERBANK">Interbank</option>
              <option value="SCOTIABANK">Scotiabank</option>
              <option value="BN">Banco de la Nación</option>
              <option value="OTRO">Otro</option>
            </select>
          </label>
          <label>
            <span>Tipo de tarjeta</span>
            <select
              value={details.tipoTarjeta ?? ""}
              onChange={(e) => update("tipoTarjeta", e.target.value)}
              required
            >
              <option value="">Seleccionar...</option>
              <option value="DEBITO">Débito (Ahorro)</option>
              <option value="CREDITO">Crédito</option>
            </select>
          </label>
          <label className="wide-field">
            <span>Número de tarjeta</span>
            <input
              type="text"
              inputMode="numeric"
              placeholder="1234 5678 9012 3456"
              maxLength={19}
              value={details.numeroTarjeta ?? ""}
              onChange={(e) => {
                const raw = e.target.value.replace(/\D/g, "").slice(0, 16);
                const formatted = raw.replace(/(\d{4})(?=\d)/g, "$1 ");
                update("numeroTarjeta", formatted);
              }}
              required
            />
          </label>
          <label>
            <span>Nombre del titular</span>
            <input
              type="text"
              placeholder="Como aparece en la tarjeta"
              value={details.nombreTitular ?? ""}
              onChange={(e) => update("nombreTitular", e.target.value)}
              required
            />
          </label>
          <label>
            <span>Fecha vencimiento</span>
            <input
              type="text"
              placeholder="MM/AA"
              maxLength={5}
              value={details.fechaVencimiento ?? ""}
              onChange={(e) => {
                let raw = e.target.value.replace(/\D/g, "").slice(0, 4);
                if (raw.length > 2) raw = raw.slice(0, 2) + "/" + raw.slice(2);
                update("fechaVencimiento", raw);
              }}
              required
            />
          </label>
          <label>
            <span>CVV</span>
            <input
              type="password"
              inputMode="numeric"
              placeholder="•••"
              maxLength={3}
              value={details.cvv ?? ""}
              onChange={(e) => update("cvv", e.target.value.replace(/\D/g, "").slice(0, 3))}
              required
            />
          </label>
        </div>
      </div>
    );
  }

  if (metodoPago === "YAPE" || metodoPago === "PLIN") {
    return (
      <div className="payment-details-section">
        <div className="payment-details-title">
          <Smartphone size={14} />
          Datos de {metodoPago === "YAPE" ? "Yape" : "Plin"}
        </div>
        <div className="payment-details-fields">
          <label>
            <span>Número de celular</span>
            <input
              type="tel"
              inputMode="numeric"
              placeholder="987 654 321"
              maxLength={11}
              value={details.numeroCelular ?? ""}
              onChange={(e) => {
                const raw = e.target.value.replace(/\D/g, "").slice(0, 9);
                const formatted = raw.replace(/(\d{3})(?=\d)/g, "$1 ");
                update("numeroCelular", formatted);
              }}
              required
            />
          </label>
          <label>
            <span>Código de aprobación</span>
            <input
              type="text"
              inputMode="numeric"
              placeholder="123456"
              maxLength={6}
              value={details.codigoAprobacion ?? ""}
              onChange={(e) => update("codigoAprobacion", e.target.value.replace(/\D/g, "").slice(0, 6))}
              required
            />
          </label>
        </div>
      </div>
    );
  }

  if (metodoPago === "EFECTIVO") {
    return (
      <div className="payment-efectivo-note">
        <Banknote size={16} />
        El pago se realizará de forma presencial en el local del proveedor.
      </div>
    );
  }

  return null;
}
