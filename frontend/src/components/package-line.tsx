import type { ItemRecomendado } from "../types";

type PackageLineProps = {
  item: ItemRecomendado;
};

export function PackageLine({ item }: PackageLineProps) {
  return (
    <div className="included-row">
      <span>{item.nombre}</span>
      <strong>x{item.cantidad}</strong>
    </div>
  );
}
