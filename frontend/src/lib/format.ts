import type {
  CheckoutClienteCreate,
  LoginDraft,
  ProveedorRecomendado,
  RegisterDraft,
  ServicioProducto,
} from "../types";

/** Shared currency formatter for Peruvian Soles */
export const money = new Intl.NumberFormat("es-PE", {
  style: "currency",
  currency: "PEN",
});

export function formatDuration(hours: number): string {
  if (hours < 1) {
    return `${Math.round(hours * 60)} min`;
  }
  return `${hours} h`;
}

export function formatTime(isoDate: string): string {
  return isoDate.slice(11, 16);
}

export function addHours(isoDate: string, hours: number): string {
  const date = new Date(isoDate);
  date.setMinutes(date.getMinutes() + Math.round(hours * 60));
  return toLocalInputDateTime(date);
}

export function toLocalInputDateTime(date: Date): string {
  const yyyy = date.getFullYear();
  const mm = String(date.getMonth() + 1).padStart(2, "0");
  const dd = String(date.getDate()).padStart(2, "0");
  const hh = String(date.getHours()).padStart(2, "0");
  const min = String(date.getMinutes()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}T${hh}:${min}:00`;
}

export function roundMoney(value: number): number {
  return Math.round(value * 100) / 100;
}

export function cleanNumber(value: string): number | undefined {
  const parsed = Number(value.trim());
  return Number.isFinite(parsed) && parsed > 0 ? parsed : undefined;
}

export function readError(error: unknown): string {
  return error instanceof Error ? error.message : "Ocurrió un error inesperado.";
}

export function inferPackageDuration(provider: ProveedorRecomendado): number {
  const text = `${provider.paquete.nombre} ${provider.paquete.descripcion ?? ""}`.toLowerCase();
  if (text.includes("hora loca")) return 0.75;
  if (text.includes("infantil") || text.includes("show")) return 2;
  const durations = provider.paquete.incluye.map((item) => item.horas ?? 0).filter(Boolean);
  return durations.length ? Math.max(...durations) : 2;
}

export function inferEventType(provider: ProveedorRecomendado): string {
  const text = provider.paquete.nombre.toLowerCase();
  if (text.includes("hora loca")) return "Hora loca";
  if (text.includes("infantil")) return "Fiesta infantil";
  return "Evento";
}

export function serviceSubtotal(service: ServicioProducto, quantity: number): number {
  const hours = service.duracion_base_horas ?? 0;
  const hourly = service.requiere_persona || service.nombre.toLowerCase().includes("dj");
  return roundMoney(service.precio_unitario * quantity * (hourly && hours ? hours : 1));
}

export function registerPayload(draft: RegisterDraft, direccion: string): CheckoutClienteCreate {
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

export function loginPayload(draft: LoginDraft, direccion: string): CheckoutClienteCreate {
  return {
    nombre: "Cliente",
    apellido: "Festio",
    email: draft.email,
    password: draft.password,
    direccion,
    metodo_pago: draft.metodoPago,
  };
}
