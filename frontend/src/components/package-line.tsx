import { AlertTriangle } from "lucide-react";
import type { ItemRecomendado } from "../types";

type PackageLineProps = {
  item: ItemRecomendado;
  isUnavailable?: boolean;
};

export function PackageLine({ item, isUnavailable }: PackageLineProps) {
  const agotado =
    isUnavailable ??
    (item.stock_maximo_simultaneo == null || item.stock_maximo_simultaneo < item.cantidad);

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
