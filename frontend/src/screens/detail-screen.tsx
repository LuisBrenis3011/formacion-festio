import { useMemo, type Dispatch, type SetStateAction } from "react";
import { AlertTriangle, ArrowLeft, CreditCard, Loader2, Minus, Plus } from "lucide-react";
import { PackageLine } from "../components/package-line";
import { SummaryLine } from "../components/summary-line";
import { addHours, formatDuration, formatTime, money } from "../lib/format";
import type { ContinueToPaymentParams } from "../hooks/use-payment-flow";
import type {
  EventDraft,
  ItemRecomendado,
  ProveedorRecomendado,
  ServicioProducto,
} from "../types";

const UNAVAILABLE_OBSERVATION_KEYWORDS = ["no disponible", "sin stock", "agotado", "agotada"];

function normalizeText(value: string) {
  return value.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
}

function itemHasUnavailableObservation(item: ItemRecomendado, observations: string[]) {
  const itemName = normalizeText(item.nombre);
  return observations.some((observation) => {
    const text = normalizeText(observation);
    if (!text.includes(itemName)) return false;
    return (
      UNAVAILABLE_OBSERVATION_KEYWORDS.some((keyword) => text.includes(keyword)) ||
      (text.includes("disponible") && text.includes("solicitado"))
    );
  });
}

function isIncludedItemUnavailable(item: ItemRecomendado, observations: string[]) {
  return (
    item.stock_maximo_simultaneo == null ||
    item.stock_maximo_simultaneo < item.cantidad ||
    itemHasUnavailableObservation(item, observations)
  );
}

type DetailScreenProps = {
  provider: ProveedorRecomendado;
  eventDraft: EventDraft;
  setEventDraft: Dispatch<SetStateAction<EventDraft>>;
  extras: ServicioProducto[];
  extraQuantities: Record<number, number>;
  updateExtra: (service: ServicioProducto, direction: 1 | -1) => void;
  extraTotal: number;
  total: number;
  advance: number;
  balance: number;
  packageDurationHours: number;
  selectedExtras: ServicioProducto[];
  eventType?: string | null;
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
  eventType,
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
  const extrasByType = useMemo(
    () =>
      extras.reduce<Record<string, ServicioProducto[]>>((groups, service) => {
        const label = service.tipo || "Adicionales";
        groups[label] = [...(groups[label] ?? []), service];
        return groups;
      }, {}),
    [extras],
  );
  const unavailableIncludedIds = useMemo(
    () =>
      new Set(
        provider.paquete.incluye
          .filter((item) => isIncludedItemUnavailable(item, provider.observaciones))
          .map((item) => item.servicio_producto_id),
      ),
    [provider.paquete.incluye, provider.observaciones],
  );
  const hasUnavailableIncluded = unavailableIncludedIds.size > 0;

  function handleContinue() {
    if (hasUnavailableIncluded) return;
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
                <PackageLine
                  key={item.servicio_producto_id}
                  item={item}
                  isUnavailable={unavailableIncludedIds.has(item.servicio_producto_id)}
                />
              ))}
            </div>
            {hasUnavailableIncluded && (
              <div className="inventory-warning">
                <AlertTriangle size={18} />
                <span>
                  Algunos servicios incluidos no están disponibles. Puedes seleccionar alternativas en los Adicionales.
                </span>
              </div>
            )}
          </div>

          <div className="extras-block">
            <h3>
              Adicionales
              {selectedExtras.length > 0 && (
                <span className="extras-count-badge">
                  {selectedExtras.length} seleccionados
                </span>
              )}
            </h3>
            <div className="extras-list">
              {Object.entries(extrasByType).map(([type, services]) => (
                <section className="extras-group" key={type}>
                  <div className="extras-group-header">{type}</div>
                  <div className="extras-group-items">
                    {services.map((service) => {
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
                </section>
              ))}
              {extras.length === 0 && (
                <div className="extra-row">
                  <div>
                    <strong>No hay adicionales disponibles</strong>
                    <span>Este paquete ya incluye los servicios activos del proveedor.</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </article>

        <aside className="booking-panel">
          <div className="summary-card">
            <span className="summary-eyebrow">Datos del evento</span>
            <div className="field-grid">
              <label>
                <span>Tipo de evento</span>
                <div className="tipo-evento-badge">
                  {eventType || provider.payload_prebloqueo?.tipo_evento || "Evento"}
                </div>
              </label>
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

            <button
              className="primary-action"
              type="button"
              onClick={handleContinue}
              disabled={loadingPayment || hasUnavailableIncluded}
            >
              {loadingPayment ? <Loader2 className="spin" size={18} /> : <CreditCard size={18} />}
              {hasUnavailableIncluded ? "Paquete no disponible" : "Continuar al pago"}
            </button>
          </div>
        </aside>
      </section>
    </main>
  );
}
