import { requestAuthJson } from "./apiClient";
import type { LoginDraft, TokenResponse, AuthUser } from "../types";

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
      body: JSON.stringify(datos),
    });
  },

  async registroProveedor(datos: RegistroProveedorDraft): Promise<TokenResponse> {
    return requestAuthJson<TokenResponse>("/api/auth/registro-proveedor", {
      method: "POST",
      body: JSON.stringify(datos),
    });
  },

  async getMe(): Promise<AuthUser> {
    return requestAuthJson<AuthUser>("/api/auth/me", {
      method: "GET",
    });
  },
};
