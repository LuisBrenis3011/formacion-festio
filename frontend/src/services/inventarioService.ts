import { requestAuthJson } from "./apiClient";
import type { 
  ServicioProducto, 
  ProveedorServicioCreate, 
  ProveedorServicioUpdate 
} from "../types";

export const inventarioService = {
  async listar(): Promise<ServicioProducto[]> {
    return requestAuthJson<ServicioProducto[]>("/api/proveedor/inventario", {
      method: "GET",
    });
  },

  async obtener(id: number): Promise<ServicioProducto> {
    return requestAuthJson<ServicioProducto>(`/api/proveedor/inventario/${id}`, {
      method: "GET",
    });
  },

  async crear(datos: ProveedorServicioCreate): Promise<ServicioProducto> {
    return requestAuthJson<ServicioProducto>("/api/proveedor/inventario", {
      method: "POST",
      body: JSON.stringify(datos),
    });
  },

  async actualizar(id: number, datos: ProveedorServicioUpdate): Promise<ServicioProducto> {
    return requestAuthJson<ServicioProducto>(`/api/proveedor/inventario/${id}`, {
      method: "PATCH",
      body: JSON.stringify(datos),
    });
  },

  async eliminar(id: number): Promise<void> {
    return requestAuthJson<void>(`/api/proveedor/inventario/${id}`, {
      method: "DELETE",
    });
  },
};
