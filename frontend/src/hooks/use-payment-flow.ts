import { type FormEvent, useState } from "react";
import { checkoutSimulado, prebloquearReserva } from "../api";
import {
  cleanNumber,
  inferEventType,
  loginPayload,
  readError,
  registerPayload,
} from "../lib/format";
import { LOGIN_INITIAL, REGISTER_INITIAL } from "../lib/constants";
import type {
  AuthTab,
  CheckoutReservaResponse,
  EventDraft,
  LoginDraft,
  PreReservaResponse,
  ProveedorRecomendado,
  RegisterDraft,
  ServicioProducto,
  AuthUser,
} from "../types";

export type ContinueToPaymentParams = {
  provider: ProveedorRecomendado;
  eventDraft: EventDraft;
  endDateTime: string;
  selectedExtras: ServicioProducto[];
  extraQuantities: Record<number, number>;
};

/**
 * Manages the full payment flow: pre-reserva, auth form drafts,
 * and the simulated checkout. Functions accept needed external data
 * as params to stay decoupled from the booking/extras hooks.
 */
export function usePaymentFlow({ onSuccess }: { onSuccess: () => void }) {
  const [preReserva, setPreReserva] = useState<PreReservaResponse | null>(null);
  const [confirmation, setConfirmation] = useState<CheckoutReservaResponse | null>(null);
  const [paymentOpen, setPaymentOpen] = useState(false);
  const [authTab, setAuthTab] = useState<AuthTab>("register");
  const [registerDraft, setRegisterDraft] = useState<RegisterDraft>(REGISTER_INITIAL);
  const [loginDraft, setLoginDraft] = useState<LoginDraft>(LOGIN_INITIAL);
  const [loadingPayment, setLoadingPayment] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function continueToPayment(params: ContinueToPaymentParams) {
    const { provider, eventDraft, endDateTime, selectedExtras, extraQuantities } = params;

    if (!eventDraft.fecha || !eventDraft.horaInicio || !eventDraft.direccion.trim()) {
      setError("Selecciona fecha, hora de inicio y dirección del cliente.");
      return;
    }
    if (!endDateTime) {
      setError("No se pudo calcular la hora de fin.");
      return;
    }

    setLoadingPayment(true);
    setError(null);

    try {
      const response = await prebloquearReserva({
        proveedor_id: provider.proveedor_id,
        paquete_id: provider.paquete.paquete_id,
        nombre_evento: provider.paquete.nombre,
        tipo_evento: inferEventType(provider),
        fecha_evento_inicio: `${eventDraft.fecha}T${eventDraft.horaInicio}:00`,
        fecha_evento_fin: endDateTime,
        direccion: eventDraft.direccion.trim(),
        aforo_estimado: cleanNumber(eventDraft.invitados) ?? null,
        adicionales: selectedExtras.map((service) => ({
          servicio_producto_id: service.id,
          cantidad: extraQuantities[service.id] ?? 0,
          horas_contratadas: service.duracion_base_horas ?? null,
        })),
      });
      setPreReserva(response);
      setPaymentOpen(true);
    } catch (apiError) {
      setError(readError(apiError));
    } finally {
      setLoadingPayment(false);
    }
  }

  async function submitPayment(
    event: FormEvent<HTMLFormElement>,
    direccion: string,
    metodoPago: string,
    isAuthenticated: boolean,
    user: AuthUser | null,
  ) {
    event.preventDefault();
    if (!preReserva) return;

    let payload;
    if (isAuthenticated && user) {
      payload = {
        nombre: user.nombre,
        apellido: user.apellido,
        email: user.email,
        password: "authenticated_session",
        direccion,
        metodo_pago: metodoPago,
      };
    } else {
      payload =
        authTab === "login"
          ? loginPayload(loginDraft, direccion)
          : registerPayload(registerDraft, direccion);
      payload.metodo_pago = metodoPago;
    }

    setLoadingPayment(true);
    setError(null);

    try {
      const response = await checkoutSimulado(preReserva.reserva_temp_id, payload);
      setConfirmation(response);
      setPaymentOpen(false);
      onSuccess();
    } catch (apiError) {
      setError(readError(apiError));
    } finally {
      setLoadingPayment(false);
    }
  }

  return {
    preReserva,
    confirmation,
    paymentOpen,
    setPaymentOpen,
    authTab,
    setAuthTab,
    registerDraft,
    setRegisterDraft,
    loginDraft,
    setLoginDraft,
    loadingPayment,
    error,
    continueToPayment,
    submitPayment,
  };
}
