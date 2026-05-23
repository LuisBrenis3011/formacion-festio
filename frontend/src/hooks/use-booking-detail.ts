import { useState } from "react";
import { listarServiciosProveedor } from "../api";
import { readError } from "../lib/format";
import { EVENT_INITIAL } from "../lib/constants";
import type { EventDraft, ProveedorRecomendado, ServicioProducto } from "../types";

/**
 * Manages the booking detail state: selected provider, its services,
 * the event draft form data, and the async openPackage action.
 */
export function useBookingDetail(onOpen: () => void) {
  const [selectedProvider, setSelectedProvider] = useState<ProveedorRecomendado | null>(null);
  const [providerServices, setProviderServices] = useState<ServicioProducto[]>([]);
  const [eventDraft, setEventDraft] = useState<EventDraft>(EVENT_INITIAL);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function openPackage(provider: ProveedorRecomendado) {
    setLoadingDetail(true);
    setError(null);
    setSelectedProvider(provider);

    try {
      const services = await listarServiciosProveedor(provider.proveedor_id);
      setProviderServices(services);
      onOpen();
    } catch (apiError) {
      setError(readError(apiError));
    } finally {
      setLoadingDetail(false);
    }
  }

  return {
    selectedProvider,
    providerServices,
    eventDraft,
    setEventDraft,
    openPackage,
    loadingDetail,
    error,
    setError,
  };
}
