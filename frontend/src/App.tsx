import {
  ArrowLeft,
  CalendarDays,
  CheckCircle2,
  Clock3,
  CreditCard,
  Loader2,
  MapPin,
  Minus,
  Package,
  PartyPopper,
  Plus,
  Search,
  Sparkles,
  UserRound,
  Users,
  X,
} from "lucide-react";
import { FormEvent, useMemo, useState } from "react";
import {
  checkoutSimulado,
  listarServiciosProveedor,
  prebloquearReserva,
  recomendarEvento,
} from "./api";
import type {
  CheckoutClienteCreate,
  CheckoutReservaResponse,
  ItemRecomendado,
  PreReservaResponse,
  ProveedorRecomendado,
  RecomendacionResponse,
  ServicioProducto,
} from "./types";

type Screen = "home" | "results" | "detail" | "success";
type AuthTab = "login" | "register";

type EventDraft = {
  fecha: string;
  horaInicio: string;
  direccion: string;
  invitados: string;
};

type RegisterDraft = {
  nombre: string;
  apellido: string;
  email: string;
  telefono: string;
  password: string;
  metodoPago: string;
};

const eventInitial: EventDraft = {
  fecha: "",
  horaInicio: "",
  direccion: "",
  invitados: "",
};

const registerInitial: RegisterDraft = {
  nombre: "",
  apellido: "",
  email: "",
  telefono: "",
  password: "",
  metodoPago: "TARJETA",
};

const loginInitial = {
  email: "",
  password: "",
  metodoPago: "TARJETA",
};

const suggestions = [
  "Show infantil de Spiderman para 30 niños",
  "Hora loca para una fiesta de 50 personas",
  "DJ y luces para cumpleaños este sábado",
  "Sillas y toldo para evento familiar",
];

const money = new Intl.NumberFormat("es-PE", {
  style: "currency",
  currency: "PEN",
});

export default function App() {
  const [screen, setScreen] = useState<Screen>("home");
  const [query, setQuery] = useState("");
  const [recommendation, setRecommendation] = useState<RecomendacionResponse | null>(null);
  const [selectedProvider, setSelectedProvider] = useState<ProveedorRecomendado | null>(null);
  const [providerServices, setProviderServices] = useState<ServicioProducto[]>([]);
  const [extraQuantities, setExtraQuantities] = useState<Record<number, number>>({});
  const [eventDraft, setEventDraft] = useState<EventDraft>(eventInitial);
  const [preReserva, setPreReserva] = useState<PreReservaResponse | null>(null);
  const [confirmation, setConfirmation] = useState<CheckoutReservaResponse | null>(null);
  const [paymentOpen, setPaymentOpen] = useState(false);
  const [authTab, setAuthTab] = useState<AuthTab>("register");
  const [registerDraft, setRegisterDraft] = useState<RegisterDraft>(registerInitial);
  const [loginDraft, setLoginDraft] = useState(loginInitial);
  const [loadingSearch, setLoadingSearch] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [loadingPayment, setLoadingPayment] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const principales = recommendation?.resultados_principales ?? [];
  const otras = recommendation?.otras_opciones ?? [];

  const packageDurationHours = useMemo(
    () => (selectedProvider ? inferPackageDuration(selectedProvider) : 2),
    [selectedProvider],
  );

  const endDateTime = useMemo(() => {
    if (!eventDraft.fecha || !eventDraft.horaInicio) {
      return "";
    }
    return addHours(`${eventDraft.fecha}T${eventDraft.horaInicio}:00`, packageDurationHours);
  }, [eventDraft.fecha, eventDraft.horaInicio, packageDurationHours]);

  const includedIds = useMemo(() => {
    return new Set(selectedProvider?.paquete.incluye.map((item) => item.servicio_producto_id) ?? []);
  }, [selectedProvider]);

  const extras = useMemo(() => {
    return providerServices
      .filter((service) => !includedIds.has(service.id))
      .filter((service) => service.estado === "ACTIVO")
      .sort((a, b) => a.nombre.localeCompare(b.nombre));
  }, [includedIds, providerServices]);

  const selectedExtras = useMemo(() => {
    return extras.filter((service) => (extraQuantities[service.id] ?? 0) > 0);
  }, [extraQuantities, extras]);

  const extraTotal = useMemo(() => {
    return selectedExtras.reduce((total, service) => {
      const quantity = extraQuantities[service.id] ?? 0;
      return total + serviceSubtotal(service, quantity);
    }, 0);
  }, [extraQuantities, selectedExtras]);

  const total = (selectedProvider?.paquete.precio_base ?? 0) + extraTotal;
  const advance = roundMoney(total * 0.2);
  const localBalance = roundMoney(total * 0.8);

  async function handleSearch(event?: FormEvent<HTMLFormElement>) {
    event?.preventDefault();
    const cleanQuery = query.trim();
    if (!cleanQuery) {
      setError("Describe el evento que quieres encontrar.");
      return;
    }

    setLoadingSearch(true);
    setError(null);
    setSelectedProvider(null);
    setPreReserva(null);
    setConfirmation(null);

    try {
      const response = await recomendarEvento({
        mensaje: cleanQuery,
        aforo_estimado: parseGuests(cleanQuery),
      });
      setRecommendation(response);
      setScreen("results");
    } catch (apiError) {
      setError(readError(apiError));
    } finally {
      setLoadingSearch(false);
    }
  }

  async function openPackage(provider: ProveedorRecomendado) {
    setLoadingDetail(true);
    setError(null);
    setSelectedProvider(provider);
    setExtraQuantities({});
    setEventDraft((current) => ({
      ...current,
      invitados: current.invitados || String(parseGuests(query) ?? ""),
    }));

    try {
      const services = await listarServiciosProveedor(provider.proveedor_id);
      setProviderServices(services);
      setScreen("detail");
    } catch (apiError) {
      setError(readError(apiError));
    } finally {
      setLoadingDetail(false);
    }
  }

  function updateExtra(service: ServicioProducto, direction: 1 | -1) {
    const stock = Math.max(service.stock_maximo_simultaneo ?? 1, 1);
    setExtraQuantities((current) => {
      const nextValue = Math.min(Math.max((current[service.id] ?? 0) + direction, 0), stock);
      return { ...current, [service.id]: nextValue };
    });
  }

  async function continueToPayment() {
    if (!selectedProvider) {
      return;
    }
    if (!eventDraft.fecha || !eventDraft.horaInicio || !eventDraft.direccion.trim()) {
      setError("Selecciona fecha, hora de inicio y dirección del cliente.");
      return;
    }
    if (!endDateTime) {
      setError("No se pudo calcular la hora de fin.");
      return;
    }

    setLoadingPayment(true);
    setError(null);

    try {
      const response = await prebloquearReserva({
        proveedor_id: selectedProvider.proveedor_id,
        paquete_id: selectedProvider.paquete.paquete_id,
        nombre_evento: selectedProvider.paquete.nombre,
        tipo_evento: inferEventType(selectedProvider),
        fecha_evento_inicio: `${eventDraft.fecha}T${eventDraft.horaInicio}:00`,
        fecha_evento_fin: endDateTime,
        direccion: eventDraft.direccion.trim(),
        aforo_estimado: cleanNumber(eventDraft.invitados) ?? null,
        adicionales: selectedExtras.map((service) => ({
          servicio_producto_id: service.id,
          cantidad: extraQuantities[service.id] ?? 0,
          horas_contratadas: service.duracion_base_horas ?? null,
        })),
      });
      setPreReserva(response);
      setPaymentOpen(true);
    } catch (apiError) {
      setError(readError(apiError));
    } finally {
      setLoadingPayment(false);
    }
  }

  async function submitPayment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!preReserva) {
      return;
    }

    const payload =
      authTab === "login"
        ? loginPayload(loginDraft, eventDraft.direccion)
        : registerPayload(registerDraft, eventDraft.direccion);

    setLoadingPayment(true);
    setError(null);

    try {
      const response = await checkoutSimulado(preReserva.reserva_temp_id, payload);
      setConfirmation(response);
      setPaymentOpen(false);
      setScreen("success");
    } catch (apiError) {
      setError(readError(apiError));
    } finally {
      setLoadingPayment(false);
    }
  }

  return (
    <div className={`app-shell screen-${screen}`}>
      <header className="app-header">
        <button className="brand-button" type="button" onClick={() => setScreen("home")}>
          <span className="brand-icon">
            <PartyPopper size={20} />
          </span>
          <span>Festio</span>
        </button>
      </header>

      {screen === "home" && (
        <main className="home-screen">
          <section className="search-hero">
            <div className="hero-mark">
              <Sparkles size={22} />
            </div>
            <h1>Encuentra tu evento con Festio</h1>
            <p>Describe lo que necesitas y te conectamos con proveedores disponibles.</p>

            <form className="search-box" onSubmit={handleSearch}>
              <Search size={22} />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Ej: Show infantil de Spiderman para 30 niños este sábado..."
                autoFocus
              />
              <button type="submit" disabled={loadingSearch}>
                {loadingSearch ? <Loader2 className="spin" size={22} /> : <Search size={22} />}
              </button>
            </form>

            <div className="quick-suggestions">
              {suggestions.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  onClick={() => {
                    setQuery(suggestion);
                    setError(null);
                  }}
                >
                  {chipIcon(suggestion)}
                  <span>{suggestion.split(" para ")[0]}</span>
                </button>
              ))}
            </div>

            {error && <p className="inline-error">{error}</p>}
          </section>
        </main>
      )}

      {screen === "results" && (
        <main className="page-wrap">
          <section className="results-head">
            <button className="ghost-button" type="button" onClick={() => setScreen("home")}>
              <ArrowLeft size={18} />
              Nueva búsqueda
            </button>
            <div>
              <span>Resultados</span>
              <h2>{query}</h2>
            </div>
          </section>

          {error && <p className="inline-error">{error}</p>}

          <section className="results-content">
            {principales.length > 0 && (
              <div className="results-group">
                <h3 className="group-title">
                  <Sparkles size={16} />
                  Coincidencias ideales
                </h3>
                <div className="package-grid">
                  {principales.map((provider) => (
                    <PackageCard
                      key={provider.proveedor_id}
                      provider={provider}
                      onClick={() => openPackage(provider)}
                      disabled={loadingDetail}
                      featured
                    />
                  ))}
                </div>
              </div>
            )}

            {otras.length > 0 && (
              <div className="results-group secondary-results">
                <h3 className="group-title">Otras alternativas para ti</h3>
                <div className="package-grid compact">
                  {otras.map((provider) => (
                    <PackageCard
                      key={provider.proveedor_id}
                      provider={provider}
                      onClick={() => openPackage(provider)}
                      disabled={loadingDetail}
                    />
                  ))}
                </div>
              </div>
            )}

            {principales.length === 0 && otras.length === 0 && (
              <div className="empty-results">
                <p>No encontramos opciones disponibles para esta búsqueda.</p>
                <button className="primary-action" onClick={() => setScreen("home")}>
                  Intentar otra búsqueda
                </button>
              </div>
            )}
          </section>
        </main>
      )}

      {screen === "detail" && selectedProvider && (
        <main className="page-wrap detail-wrap">
          <button className="ghost-button" type="button" onClick={() => setScreen("results")}>
            <ArrowLeft size={18} />
            Volver a paquetes
          </button>

          {error && <p className="inline-error">{error}</p>}

          <section className="detail-layout">
            <article className="detail-main">
              <div className="detail-title">
                <span>{selectedProvider.nombre_empresa}</span>
                <h2>{selectedProvider.paquete.nombre}</h2>
                {selectedProvider.paquete.descripcion && <p>{selectedProvider.paquete.descripcion}</p>}
              </div>

              <div className="included-block">
                <h3>Incluye</h3>
                <div className="included-list">
                  {selectedProvider.paquete.incluye.map((item) => (
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
                      onChange={(event) => setEventDraft({ ...eventDraft, fecha: event.target.value })}
                    />
                  </label>
                  <label>
                    <span>Hora de inicio</span>
                    <input
                      type="time"
                      value={eventDraft.horaInicio}
                      onChange={(event) => setEventDraft({ ...eventDraft, horaInicio: event.target.value })}
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
                      onChange={(event) => setEventDraft({ ...eventDraft, invitados: event.target.value })}
                      placeholder="30"
                    />
                  </label>
                  <label className="wide-field">
                    <span>Dirección del cliente</span>
                    <input
                      value={eventDraft.direccion}
                      onChange={(event) => setEventDraft({ ...eventDraft, direccion: event.target.value })}
                      placeholder="Av. Primavera 123, Surco"
                    />
                  </label>
                </div>

                <div className="price-summary">
                  <SummaryLine label="Paquete" value={selectedProvider.paquete.precio_base} />
                  <SummaryLine label="Adicionales" value={extraTotal} />
                  <SummaryLine label="Total" value={total} strong />
                  <SummaryLine label="Adelanto 20%" value={advance} />
                  <SummaryLine label="En el local 80%" value={localBalance} />
                </div>

                <button className="primary-action" type="button" onClick={continueToPayment} disabled={loadingPayment}>
                  {loadingPayment ? <Loader2 className="spin" size={18} /> : <CreditCard size={18} />}
                  Continuar al pago
                </button>
              </div>
            </aside>
          </section>
        </main>
      )}

      {screen === "success" && confirmation && (
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
            <button className="primary-action" type="button" onClick={() => setScreen("home")}>
              Nueva búsqueda
            </button>
          </section>
        </main>
      )}

      {paymentOpen && preReserva && (
        <div className="modal-backdrop" role="presentation">
          <section className="payment-modal" role="dialog" aria-modal="true" aria-labelledby="payment-title">
            <button className="close-button" type="button" onClick={() => setPaymentOpen(false)}>
              <X size={20} />
            </button>
            <div className="modal-head">
              <span>Pago simulado</span>
              <h2 id="payment-title">{money.format(preReserva.monto_adelanto)} de adelanto</h2>
              <p>El saldo de {money.format(preReserva.monto_pendiente)} se paga en el local.</p>
            </div>

            <div className="auth-tabs">
              <button
                className={authTab === "login" ? "active" : ""}
                type="button"
                onClick={() => setAuthTab("login")}
              >
                Iniciar sesión
              </button>
              <button
                className={authTab === "register" ? "active" : ""}
                type="button"
                onClick={() => setAuthTab("register")}
              >
                Registrarse
              </button>
            </div>

            {error && <p className="inline-error">{error}</p>}

            <form className="auth-form" onSubmit={submitPayment}>
              {authTab === "register" ? (
                <>
                  <label>
                    <span>Nombre</span>
                    <input
                      required
                      value={registerDraft.nombre}
                      onChange={(event) => setRegisterDraft({ ...registerDraft, nombre: event.target.value })}
                    />
                  </label>
                  <label>
                    <span>Apellido</span>
                    <input
                      required
                      value={registerDraft.apellido}
                      onChange={(event) => setRegisterDraft({ ...registerDraft, apellido: event.target.value })}
                    />
                  </label>
                  <label className="wide-field">
                    <span>Email</span>
                    <input
                      required
                      type="email"
                      value={registerDraft.email}
                      onChange={(event) => setRegisterDraft({ ...registerDraft, email: event.target.value })}
                    />
                  </label>
                  <label>
                    <span>Teléfono</span>
                    <input
                      value={registerDraft.telefono}
                      onChange={(event) => setRegisterDraft({ ...registerDraft, telefono: event.target.value })}
                    />
                  </label>
                  <label>
                    <span>Password</span>
                    <input
                      required
                      type="password"
                      value={registerDraft.password}
                      onChange={(event) => setRegisterDraft({ ...registerDraft, password: event.target.value })}
                    />
                  </label>
                  <PaymentMethod
                    value={registerDraft.metodoPago}
                    onChange={(value) => setRegisterDraft({ ...registerDraft, metodoPago: value })}
                  />
                </>
              ) : (
                <>
                  <label className="wide-field">
                    <span>Email</span>
                    <input
                      required
                      type="email"
                      value={loginDraft.email}
                      onChange={(event) => setLoginDraft({ ...loginDraft, email: event.target.value })}
                    />
                  </label>
                  <label className="wide-field">
                    <span>Password</span>
                    <input
                      required
                      type="password"
                      value={loginDraft.password}
                      onChange={(event) => setLoginDraft({ ...loginDraft, password: event.target.value })}
                    />
                  </label>
                  <PaymentMethod
                    value={loginDraft.metodoPago}
                    onChange={(value) => setLoginDraft({ ...loginDraft, metodoPago: value })}
                  />
                </>
              )}

              <button className="primary-action wide-field" type="submit" disabled={loadingPayment}>
                {loadingPayment ? <Loader2 className="spin" size={18} /> : <CreditCard size={18} />}
                Confirmar pago
              </button>
            </form>
          </section>
        </div>
      )}
    </div>
  );
}

function PackageCard({
  provider,
  onClick,
  disabled,
  featured = false,
}: {
  provider: ProveedorRecomendado;
  onClick: () => void;
  disabled: boolean;
  featured?: boolean;
}) {
  return (
    <button
      className={`package-card ${featured ? "featured" : ""}`}
      type="button"
      onClick={onClick}
      disabled={disabled}
    >
      <span className="package-icon">
        {featured ? <Sparkles size={24} /> : <Package size={24} />}
      </span>
      <div className="package-info">
        <span className="provider-name">{provider.nombre_empresa}</span>
        <strong>{provider.paquete.nombre}</strong>
        <span className="package-price">{money.format(provider.paquete.precio_base)}</span>
      </div>
    </button>
  );
}


function PackageLine({ item }: { item: ItemRecomendado }) {
  return (
    <div className="included-row">
      <span>{item.nombre}</span>
      <strong>x{item.cantidad}</strong>
    </div>
  );
}

function SummaryLine({ label, value, strong = false }: { label: string; value: number; strong?: boolean }) {
  return (
    <div className={strong ? "summary-line summary-total" : "summary-line"}>
      <span>{label}</span>
      <strong>{money.format(value)}</strong>
    </div>
  );
}

function PaymentMethod({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  return (
    <label className="wide-field">
      <span>Método de pago</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="TARJETA">Tarjeta</option>
        <option value="YAPE">Yape</option>
        <option value="PLIN">Plin</option>
        <option value="EFECTIVO">Efectivo</option>
      </select>
    </label>
  );
}

function chipIcon(text: string) {
  if (text.toLowerCase().includes("hora loca")) return "🎉";
  if (text.toLowerCase().includes("dj")) return "🎵";
  if (text.toLowerCase().includes("silla")) return "🪑";
  return "🎪";
}

function inferPackageDuration(provider: ProveedorRecomendado) {
  const text = `${provider.paquete.nombre} ${provider.paquete.descripcion ?? ""}`.toLowerCase();
  if (text.includes("hora loca")) return 0.75;
  if (text.includes("infantil") || text.includes("show")) return 2;
  const durations = provider.paquete.incluye.map((item) => item.horas ?? 0).filter(Boolean);
  return durations.length ? Math.max(...durations) : 2;
}

function inferEventType(provider: ProveedorRecomendado) {
  const text = provider.paquete.nombre.toLowerCase();
  if (text.includes("hora loca")) return "Hora loca";
  if (text.includes("infantil")) return "Fiesta infantil";
  return "Evento";
}

function serviceSubtotal(service: ServicioProducto, quantity: number) {
  const hours = service.duracion_base_horas ?? 0;
  const hourly = service.requiere_persona || service.nombre.toLowerCase().includes("dj");
  return roundMoney(service.precio_unitario * quantity * (hourly && hours ? hours : 1));
}

function addHours(isoDate: string, hours: number) {
  const date = new Date(isoDate);
  date.setMinutes(date.getMinutes() + Math.round(hours * 60));
  return toLocalInputDateTime(date);
}

function toLocalInputDateTime(date: Date) {
  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, "0");
  const dd = String(date.getDate()).padStart(2, "0");
  const hh = String(date.getHours()).padStart(2, "0");
  const min = String(date.getMinutes()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}T${hh}:${min}:00`;
}

function formatTime(isoDate: string) {
  return isoDate.slice(11, 16);
}

function formatDuration(hours: number) {
  if (hours < 1) {
    return `${Math.round(hours * 60)} min`;
  }
  return `${hours} h`;
}

function parseGuests(text: string) {
  const match = text.match(/(\d+)\s*(niñ|persona|invitad|asistente|adult)/i);
  return match ? Number(match[1]) : undefined;
}

function cleanNumber(value: string) {
  const parsed = Number(value.trim());
  return Number.isFinite(parsed) && parsed > 0 ? parsed : undefined;
}

function roundMoney(value: number) {
  return Math.round(value * 100) / 100;
}

function readError(error: unknown) {
  return error instanceof Error ? error.message : "Ocurrió un error inesperado.";
}

function registerPayload(draft: RegisterDraft, direccion: string): CheckoutClienteCreate {
  return {
    nombre: draft.nombre,
    apellido: draft.apellido,
    email: draft.email,
    telefono: draft.telefono,
    password: draft.password,
    direccion,
    metodo_pago: draft.metodoPago,
  };
}

function loginPayload(draft: typeof loginInitial, direccion: string): CheckoutClienteCreate {
  return {
    nombre: "Cliente",
    apellido: "Festio",
    email: draft.email,
    password: draft.password,
    direccion,
    metodo_pago: draft.metodoPago,
  };
}
