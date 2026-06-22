import { AlertTriangle } from "lucide-react";
import type { ItemRecomendado } from "../types";

type PackageLineProps = {
  item: ItemRecomendado;
};

export function PackageLine({ item }: PackageLineProps) {
  const agotado = item.stock_maximo_simultaneo != null && item.stock_maximo_simultaneo <= 0;

  return (
    <div className={`included-row${agotado ? " included-row-agotado" : ""}`}>
      <span>{item.nombre}</span>
      <strong>x{item.cantidad}</strong>
      {agotado && (
        <span className="badge-agotado">
          <AlertTriangle size={12} />
          Agotado
        </span>
      )}
    </div>
  );
}
