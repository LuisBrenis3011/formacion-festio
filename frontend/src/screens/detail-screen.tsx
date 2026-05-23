import { useMemo } from "react";
import { ArrowLeft, CreditCard, Loader2, Minus, Plus } from "lucide-react";
import { PackageLine } from "../components/package-line";
import { SummaryLine } from "../components/summary-line";
import { addHours, formatDuration, formatTime, money } from "../lib/format";
import type { ContinueToPaymentParams } from "../hooks/use-payment-flow";
import type {
  EventDraft,
  ProveedorRecomendado,
  ServicioProducto,
} from "../types";

type DetailScreenProps = {
  provider: ProveedorRecomendado;
  eventDraft: EventDraft;
  setEventDraft: React.Dispatch<React.SetStateAction<EventDraft>>;
  extras: ServicioProducto[];
  extraQuantities: Record<number, number>;
  updateExtra: (service: ServicioProducto, direction: 1 | -1) => void;
  extraTotal: number;
  total: number;
  advance: number;
  balance: number;
  packageDurationHours: number;
  selectedExtras: ServicioProducto[];
  error: string | null;
  loadingPayment: boolean;
  onBack: () => void;
  onContinue: (params: ContinueToPaymentParams) => void;
};

export function DetailScreen({
  provider,
  eventDraft,
  setEventDraft,
  extras,
  extraQuantities,
  updateExtra,
  extraTotal,
  total,
  advance,
  balance,
  packageDurationHours,
  selectedExtras,
  error,
  loadingPayment,
  onBack,
  onContinue,
}: DetailScreenProps) {
  // Compute endDateTime locally — combines booking eventDraft + extras packageDurationHours
  const endDateTime = useMemo(() => {
    if (!eventDraft.fecha || !eventDraft.horaInicio) return "";
    return addHours(
      `${eventDraft.fecha}T${eventDraft.horaInicio}:00`,
      packageDurationHours,
    );
  }, [eventDraft.fecha, eventDraft.horaInicio, packageDurationHours]);

  function handleContinue() {
    onContinue({
      provider,
      eventDraft,
      endDateTime,
      selectedExtras,
      extraQuantities,
    });
  }

  return (
    <main className="page-wrap detail-wrap">
      <button className="ghost-button" type="button" onClick={onBack}>
        <ArrowLeft size={18} />
        Volver al chat
      </button>

      {error && <p className="inline-error">{error}</p>}

      <section className="detail-layout">
        <article className="detail-main">
          <div className="detail-title">
            <span>{provider.nombre_empresa}</span>
            <h2>{provider.paquete.nombre}</h2>
            {provider.paquete.descripcion && <p>{provider.paquete.descripcion}</p>}
          </div>

          <div className="included-block">
            <h3>Incluye</h3>
            <div className="included-list">
              {provider.paquete.incluye.map((item) => (
                <PackageLine key={item.servicio_producto_id} item={item} />
              ))}
            </div>
          </div>

          <div className="extras-block">
            <h3>Adicionales</h3>
            <div className="extras-list">
              {extras.map((service) => {
                const quantity = extraQuantities[service.id] ?? 0;
                const stock = Math.max(service.stock_maximo_simultaneo ?? 1, 1);
                return (
                  <div className="extra-row" key={service.id}>
                    <div>
                      <strong>{service.nombre}</strong>
                      <span>
                        {money.format(service.precio_unitario)}
                        {service.duracion_base_horas ? ` · ${formatDuration(service.duracion_base_horas)}` : ""}
                        {` · stock ${stock}`}
                      </span>
                    </div>
                    <div className="stepper">
                      <button type="button" onClick={() => updateExtra(service, -1)} disabled={quantity === 0}>
                        <Minus size={16} />
                      </button>
                      <span>{quantity}</span>
                      <button type="button" onClick={() => updateExtra(service, 1)} disabled={quantity >= stock}>
                        <Plus size={16} />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </article>

        <aside className="booking-panel">
          <div className="summary-card">
            <span className="summary-eyebrow">Datos del evento</span>
            <div className="field-grid">
              <label>
                <span>Fecha</span>
                <input
                  type="date"
                  value={eventDraft.fecha}
                  onChange={(e) => setEventDraft((prev) => ({ ...prev, fecha: e.target.value }))}
                />
              </label>
              <label>
                <span>Hora de inicio</span>
                <input
                  type="time"
                  value={eventDraft.horaInicio}
                  onChange={(e) => setEventDraft((prev) => ({ ...prev, horaInicio: e.target.value }))}
                />
              </label>
              <label>
                <span>Fin calculado</span>
                <input value={endDateTime ? formatTime(endDateTime) : ""} readOnly placeholder="Automático" />
              </label>
              <label>
                <span>Invitados</span>
                <input
                  inputMode="numeric"
                  value={eventDraft.invitados}
                  onChange={(e) => setEventDraft((prev) => ({ ...prev, invitados: e.target.value }))}
                  placeholder="30"
                />
              </label>
              <label className="wide-field">
                <span>Dirección del cliente</span>
                <input
                  value={eventDraft.direccion}
                  onChange={(e) => setEventDraft((prev) => ({ ...prev, direccion: e.target.value }))}
                  placeholder="Av. Primavera 123, Surco"
                />
              </label>
            </div>

            <div className="price-summary">
              <SummaryLine label="Paquete" value={provider.paquete.precio_base} />
              <SummaryLine label="Adicionales" value={extraTotal} />
              <SummaryLine label="Total" value={total} strong />
              <SummaryLine label="Adelanto 20%" value={advance} />
              <SummaryLine label="En el local 80%" value={balance} />
            </div>

            <button className="primary-action" type="button" onClick={handleContinue} disabled={loadingPayment}>
              {loadingPayment ? <Loader2 className="spin" size={18} /> : <CreditCard size={18} />}
              Continuar al pago
            </button>
          </div>
        </aside>
      </section>
    </main>
  );
}
