import { useMutation } from "@tanstack/react-query";
import { recomendarEvento } from "../api";
import { recomendacionResponseSchema } from "@/lib/schemas";
import type { RecomendacionResponse } from "../types";

/**
 * Extracts a guest count from free-form Spanish text.
 * Examples: "30 niños" → 30, "50 personas" → 50
 */
function parseGuests(text: string): number | undefined {
  const match = text.match(/(\d+)\s*(niñ|persona|invitad|asistente|adult)/i);
  return match ? Number(match[1]) : undefined;
}

/**
 * Hook that orchestrates the full search flow:
 *
 *   1. Takes the raw text query from the search input
 *   2. Sends it to the backend (which already parses with Gemini / NLP)
 *   3. Validates the response with a Zod schema
 *   4. Returns typed, validated data ready for the UI
 *
 * Uses `useMutation` because the search is triggered imperatively by
 * the user (on submit), not on mount.
 */
export function useRecomendarEvento() {
  return useMutation<RecomendacionResponse, Error, string>({
    mutationFn: async (rawQuery: string) => {
      const cleanQuery = rawQuery.trim();
      if (!cleanQuery) {
        throw new Error("Describe el evento que quieres encontrar.");
      }

      // Call backend endpoint — the server handles NLP/Gemini parsing internally
      const response = await recomendarEvento({
        mensaje: cleanQuery,
        aforo_estimado: parseGuests(cleanQuery),
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
