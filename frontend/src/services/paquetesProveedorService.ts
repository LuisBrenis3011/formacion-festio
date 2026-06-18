import { requestAuthJson } from "./apiClient";
import type { 
  Paquete, 
  ProveedorPaqueteCreate, 
  ProveedorPaqueteUpdate 
} from "../types";

export const paquetesProveedorService = {
  async listar(): Promise<Paquete[]> {
    return requestAuthJson<Paquete[]>("/api/proveedor/paquetes", {
      method: "GET",
    });
  },

  async obtener(id: number): Promise<Paquete> {
    return requestAuthJson<Paquete>(`/api/proveedor/paquetes/${id}`, {
      method: "GET",
    });
  },

  async crear(datos: ProveedorPaqueteCreate): Promise<Paquete> {
    return requestAuthJson<Paquete>("/api/proveedor/paquetes", {
      method: "POST",
      body: JSON.stringify(datos),
    });
  },

  async actualizar(id: number, datos: ProveedorPaqueteUpdate): Promise<Paquete> {
    return requestAuthJson<Paquete>(`/api/proveedor/paquetes/${id}`, {
      method: "PATCH",
      body: JSON.stringify(datos),
    });
  },

  async eliminar(id: number): Promise<void> {
    return requestAuthJson<void>(`/api/proveedor/paquetes/${id}`, {
      method: "DELETE",
    });
  },
};
