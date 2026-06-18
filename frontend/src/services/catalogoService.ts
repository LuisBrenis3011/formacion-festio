import { requestAuthJson } from "./apiClient";
import type { Categoria, Tematica } from "../types";

export const catalogoService = {
  async listarCategorias(): Promise<Categoria[]> {
    return requestAuthJson<Categoria[]>("/api/catalogo/categorias", {
      method: "GET",
    });
  },

  async listarTematicas(categoriaId?: number): Promise<Tematica[]> {
    let url = "/api/catalogo/tematicas";
    if (categoriaId !== undefined) {
      url += `?categoria_id=${categoriaId}`;
    }
    return requestAuthJson<Tematica[]>(url, {
      method: "GET",
    });
  },
};
