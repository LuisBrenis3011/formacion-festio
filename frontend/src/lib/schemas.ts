/**
 * Zod schemas for validating API responses.
 *
 * These mirror the TypeScript types in `types.ts` but add runtime validation
 * so that TanStack Query can fail-fast on malformed backend data.
 */
import { z } from "zod";

// ---------- Items & Packages ----------

export const itemRecomendadoSchema = z.object({
  servicio_producto_id: z.number(),
  nombre: z.string(),
  cantidad: z.number(),
  precio_unitario: z.number(),
  horas: z.number().nullable().optional(),
  subtotal: z.number(),
  tipo: z.string(),
  motivo: z.string(),
  stock_maximo_simultaneo: z.number().nullable().optional(),
});

export const paqueteRecomendadoSchema = z.object({
  paquete_id: z.number(),
  nombre: z.string(),
  descripcion: z.string().nullable().optional(),
  precio_base: z.number(),
  incluye: z.array(itemRecomendadoSchema),
});

// ---------- PreReserva ----------

export const preReservaPayloadSchema = z.object({
  proveedor_id: z.number(),
  paquete_id: z.number(),
  nombre_evento: z.string(),
  tipo_evento: z.string().nullable().optional(),
  fecha_evento_inicio: z.string(),
  fecha_evento_fin: z.string(),
  direccion: z.string(),
  aforo_estimado: z.number().nullable().optional(),
  adicionales: z.array(
    z.object({
      servicio_producto_id: z.number(),
      cantidad: z.number(),
      horas_contratadas: z.number().nullable().optional(),
    }),
  ),
});

// ---------- Proveedor ----------

export const proveedorRecomendadoSchema = z.object({
  proveedor_id: z.number(),
  nombre_empresa: z.string(),
  distrito: z.string().nullable().optional(),
  calificacion_promedio: z.number().nullable().optional(),
  paquete: paqueteRecomendadoSchema,
  adicionales_sugeridos: z.array(itemRecomendadoSchema),
  total_estimado: z.number(),
  adelanto_20: z.number(),
  saldo_presencial: z.number(),
  disponible: z.boolean(),
  observaciones: z.array(z.string()),
  puede_prebloquear: z.boolean(),
  datos_faltantes_prebloqueo: z.array(z.string()),
  payload_prebloqueo: preReservaPayloadSchema.nullable().optional(),
});

// ---------- Recomendación Response ----------

export const recomendacionRequestSchema = z.object({
  mensaje: z.string(),
  nombre_evento: z.string().nullable().optional(),
  tipo_evento: z.string().nullable().optional(),
  tematica_detectada: z.string().nullable().optional(),
  servicios_extra_detectados: z.array(z.string()).optional(),
  cantidades_servicios: z.record(z.string(), z.number()).optional(),
  fecha_evento_inicio: z.string().nullable().optional(),
  fecha_evento_fin: z.string().nullable().optional(),
  direccion: z.string().nullable().optional(),
  aforo_estimado: z.number().nullable().optional(),
  distrito: z.string().nullable().optional(),
  presupuesto_maximo: z.number().nullable().optional(),
});

export const recomendacionResponseSchema = z.object({
  respuesta: z.string(),
  accion: z.string(),
  requiere_fecha_hora: z.boolean(),
  datos_faltantes_prebloqueo: z.array(z.string()),
  endpoint_prebloqueo: z.string(),
  intencion_detectada: z.array(z.string()),
  estado_conversacion: recomendacionRequestSchema.nullable().optional(),
  resultados_principales: z.array(proveedorRecomendadoSchema),
  otras_opciones: z.array(proveedorRecomendadoSchema),
});

export type RecomendacionResponseValidated = z.infer<typeof recomendacionResponseSchema>;
