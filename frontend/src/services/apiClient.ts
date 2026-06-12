const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export function readApiError(payload: unknown, status: number): string {
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

/**
 * Realiza una petición JSON agregando automáticamente el header Authorization
 * si hay un token disponible en localStorage.
 */
export async function requestAuthJson<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem("festio_token");
  
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...init.headers,
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
  });

  // Manejar el caso de 204 No Content
  if (response.status === 204) {
    return null as unknown as T;
  }

  const payload = await response.json().catch(() => null);
  
  if (!response.ok) {
    throw new Error(readApiError(payload, response.status));
  }
  
  return payload as T;
}
