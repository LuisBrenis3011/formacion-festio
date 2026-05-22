import type {
  ChatPayload,
  CheckoutClienteCreate,
  CheckoutReservaResponse,
  PreReservaPayload,
  PreReservaResponse,
  RecomendacionResponse,
  ServicioProducto,
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

async function requestJson<T>(path: string, init: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init.headers,
    },
  });

  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(readApiError(payload, response.status));
  }
  return payload as T;
}

function readApiError(payload: unknown, status: number): string {
  if (!payload || typeof payload !== "object") {
    return `La API respondió con estado ${status}.`;
  }

  const detail = (payload as { detail?: unknown }).detail;
  if (typeof detail === "string") {
    return detail;
  }

  if (detail && typeof detail === "object") {
    const data = detail as { mensaje?: string; items?: string[] };
    const items = Array.isArray(data.items) ? ` ${data.items.join(" ")}` : "";
    return `${data.mensaje ?? "No se pudo completar la operación."}${items}`;
  }

  return `La API respondió con estado ${status}.`;
}

export function recomendarEvento(datos: ChatPayload) {
  return requestJson<RecomendacionResponse>("/api/chat/recomendar", {
    method: "POST",
    body: JSON.stringify(datos),
  });
}

export function prebloquearReserva(payload: PreReservaPayload) {
  return requestJson<PreReservaResponse>("/api/reservas/prebloquear", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function checkoutSimulado(reservaTempId: string, datos: CheckoutClienteCreate) {
  return requestJson<CheckoutReservaResponse>(
    `/api/reservas/checkout-simulado/${reservaTempId}`,
    {
      method: "POST",
      body: JSON.stringify(datos),
    },
  );
}

export function listarServiciosProveedor(proveedorId: number) {
  return requestJson<ServicioProducto[]>(`/api/catalogo/servicios?proveedor_id=${proveedorId}`, {
    method: "GET",
  });
}
