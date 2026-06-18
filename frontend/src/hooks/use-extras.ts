import { useMemo, useState } from "react";
import { inferPackageDuration, roundMoney, serviceSubtotal } from "../lib/format";
import type { ProveedorRecomendado, ServicioProducto } from "../types";

/**
 * Manages the extras/add-ons stepper and all derived price calculations.
 * Automatically resets quantities when the provider changes using the
 * "derived state during render" pattern (avoids useEffect for state sync).
 */
export function useExtras(
  provider: ProveedorRecomendado | null,
  services: ServicioProducto[],
) {
  const [extraQuantities, setExtraQuantities] = useState<Record<number, number>>({});
  const [prevProviderId, setPrevProviderId] = useState<number | null>(null);

  // Reset quantities when provider changes (derived state during render)
  const currentId = provider?.proveedor_id ?? null;
  if (currentId !== prevProviderId) {
    setPrevProviderId(currentId);
    setExtraQuantities({});
  }

  const packageDurationHours = useMemo(
    () => (provider ? inferPackageDuration(provider) : 2),
    [provider],
  );

  const includedIds = useMemo(
    () => new Set(provider?.paquete.incluye.map((item) => item.servicio_producto_id) ?? []),
    [provider],
  );

  const extras = useMemo(
    () =>
      services
        .filter((service) => !includedIds.has(service.id))
        .filter((service) => service.estado === "ACTIVO")
        .sort((a, b) => a.nombre.localeCompare(b.nombre)),
    [includedIds, services],
  );

  const selectedExtras = useMemo(
    () => extras.filter((service) => (extraQuantities[service.id] ?? 0) > 0),
    [extraQuantities, extras],
  );

  const extraTotal = useMemo(
    () =>
      selectedExtras.reduce((total, service) => {
        const quantity = extraQuantities[service.id] ?? 0;
        return total + serviceSubtotal(service, quantity);
      }, 0),
    [extraQuantities, selectedExtras],
  );

  const total = (provider?.paquete.precio_base ?? 0) + extraTotal;
  const advance = roundMoney(total * 0.2);
  const balance = roundMoney(total * 0.8);

  function updateExtra(service: ServicioProducto, direction: 1 | -1) {
    const stock = Math.max(service.stock_maximo_simultaneo ?? 1, 1);
    setExtraQuantities((current) => {
      const nextValue = Math.min(Math.max((current[service.id] ?? 0) + direction, 0), stock);
      return { ...current, [service.id]: nextValue };
    });
  }

  return {
    extras,
    extraQuantities,
    updateExtra,
    selectedExtras,
    extraTotal,
    total,
    advance,
    balance,
    packageDurationHours,
  };
}
