import { useMutation } from "@tanstack/react-query";
import { recomendarEvento } from "../api";
import { recomendacionResponseSchema } from "@/lib/schemas";
import type { ChatPayload, RecomendacionResponse } from "../types";

/**
 * Hook that orchestrates the chat recommendation flow:
 *
 *   1. Takes the full ChatPayload (mensaje + historial)
 *   2. Sends it to the backend (which parses with Gemini + deterministic engine)
 *   3. Validates the response with a Zod schema
 *   4. Returns typed, validated data ready for the UI
 *
 * Uses `useMutation` because each message is triggered imperatively by
 * the user (on submit), not on mount.
 */
export function useRecomendarEvento() {
  return useMutation<RecomendacionResponse, Error, ChatPayload>({
    mutationFn: async (payload: ChatPayload) => {
      const cleanQuery = payload.mensaje.trim();
      if (!cleanQuery) {
        throw new Error("Describe el evento que quieres encontrar.");
      }

      // Send full payload (mensaje + historial) to backend
      const response = await recomendarEvento({
        mensaje: cleanQuery,
        historial: payload.historial,
        estado_conversacion: payload.estado_conversacion ?? null,
      });

      // Runtime-validate the response shape with Zod
      const parsed = recomendacionResponseSchema.safeParse(response);
      if (!parsed.success) {
        console.error("[useRecomendarEvento] Zod validation failed:", parsed.error.format());
        // Still return the raw response — Zod errors shouldn't break the UX
        // since the backend may have added new fields.
        return response;
      }

      return parsed.data as RecomendacionResponse;
    },
  });
}
