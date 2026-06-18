import { requestAuthJson } from "./apiClient";
import type { ProveedorPerfil, DashboardStats } from "../types";

export const proveedorService = {
  async getMiPerfil(): Promise<ProveedorPerfil> {
    return requestAuthJson<ProveedorPerfil>("/api/proveedores/mi-perfil", {
      method: "GET",
    });
  },

  async updateMiPerfil(datos: Partial<ProveedorPerfil>): Promise<ProveedorPerfil> {
    return requestAuthJson<ProveedorPerfil>("/api/proveedores/mi-perfil", {
      method: "PATCH",
      body: JSON.stringify(datos),
    });
  },

  async getMiDashboard(): Promise<DashboardStats> {
    return requestAuthJson<DashboardStats>("/api/proveedores/mi-dashboard", {
      method: "GET",
    });
  },
};
