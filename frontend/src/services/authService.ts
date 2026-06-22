import { requestAuthJson } from "./apiClient";
import type { LoginDraft, TokenResponse, AuthUser, RegistroClienteDraft } from "../types";

// Schema local de registro basado en lo que necesita el backend
export type RegistroProveedorDraft = {
  nombre: string;
  apellido: string;
  email: string;
  telefono?: string;
  password: string;
  nombre_empresa: string;
  ruc: string;
  distrito: string;
  descripcion?: string;
  capacidad_humana_total?: number;
};

export const authService = {
  async login(datos: LoginDraft): Promise<TokenResponse> {
    return requestAuthJson<TokenResponse>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email: datos.email, password: datos.password }),
    });
  },

  async registroProveedor(datos: RegistroProveedorDraft): Promise<TokenResponse> {
    return requestAuthJson<TokenResponse>("/api/auth/registro-proveedor", {
      method: "POST",
      body: JSON.stringify(datos),
    });
  },

  /** Registra un cliente y luego hace auto-login para obtener token. */
  async registroCliente(datos: RegistroClienteDraft): Promise<TokenResponse> {
    // 1. Registrar con rol CLIENTE
    await requestAuthJson("/api/auth/registro", {
      method: "POST",
      body: JSON.stringify({ ...datos, rol: "CLIENTE" }),
    });

    // 2. Auto-login para obtener token
    return requestAuthJson<TokenResponse>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email: datos.email, password: datos.password }),
    });
  },

  async getMe(): Promise<AuthUser> {
    return requestAuthJson<AuthUser>("/api/auth/me", {
      method: "GET",
    });
  },
};

