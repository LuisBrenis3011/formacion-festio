// ═══════════════════════════════════════════════════════════════════════════════
// FESTIO — TypeScript Types (alineados con schemas del backend)
// ═══════════════════════════════════════════════════════════════════════════════

// ─── Auth & Roles ────────────────────────────────────────────────────────────

export type RolUsuario = "CLIENTE" | "PROVEEDOR" | "ADMIN";

export type TokenResponse = {
  access_token: string;
  token_type: string;
  rol: RolUsuario;
  usuario_id: number;
  nombre: string;
  proveedor_id?: number | null;
};

export type AuthUser = {
  id: number;
  nombre: string;
  apellido: string;
  email: string;
  rol: RolUsuario;
  estado: string;
  proveedor_id?: number | null;
  nombre_empresa?: string | null;
};

// ─── Catálogo ────────────────────────────────────────────────────────────────

export type Categoria = {
  id: number;
  nombre: string;
  descripcion?: string | null;
};

export type Tematica = {
  id: number;
  categoria_id: number;
  nombre: string;
  imagen_referencial?: string | null;
};

export type TipoItemCatalogo = "SERVICIO" | "PRODUCTO";

export type ServicioProducto = {
  id: number;
  proveedor_id: number;
  categoria_id: number;
  nombre: string;
  tipo: TipoItemCatalogo;
  requiere_persona: boolean;
  precio_unitario: number;
  stock_maximo_simultaneo: number | null;
  duracion_base_horas?: number | null;
  estado: string;
};

export type DetallePaquete = {
  id: number;
  paquete_id: number;
  servicio_producto_id: number;
  cantidad_incluida: number;
  servicio_nombre?: string | null;
};

export type Paquete = {
  id: number;
  proveedor_id: number;
  categoria_id: number;
  tematica_id?: number | null;
  nombre: string;
  descripcion?: string | null;
  precio_base: number;
  estado: string;
  detalles: DetallePaquete[];
};

// ─── B2B: Schemas de creación (sin proveedor_id) ─────────────────────────────

export type ProveedorServicioCreate = {
  categoria_id: number;
  nombre: string;
  tipo: TipoItemCatalogo;
  requiere_persona: boolean;
  precio_unitario: number;
  stock_maximo_simultaneo: number;
  duracion_base_horas?: number | null;
};

export type ProveedorServicioUpdate = Partial<ProveedorServicioCreate> & {
  estado?: string;
};

export type DetallePaqueteCreate = {
  servicio_producto_id: number;
  cantidad_incluida: number;
};

export type ProveedorPaqueteCreate = {
  categoria_id: number;
  tematica_id?: number | null;
  nombre: string;
  descripcion?: string | null;
  precio_base: number;
  detalles: DetallePaqueteCreate[];
};

export type ProveedorPaqueteUpdate = Partial<Omit<ProveedorPaqueteCreate, "detalles">> & {
  estado?: string;
  detalles?: DetallePaqueteCreate[];
};

export type DashboardStats = {
  total_servicios: number;
  total_paquetes: number;
  total_reservas: number;
};

export type ProveedorPerfil = {
  id: number;
  usuario_id: number;
  nombre_empresa: string;
  ruc: string;
  descripcion?: string | null;
  distrito: string;
  calificacion_promedio: number;
  estado_verificacion: string;
  capacidad_humana_total: number;
};

// ─── Chat Conversacional ─────────────────────────────────────────────────────

/** Mensaje individual en la conversación del chat */
export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  recommendation?: RecomendacionResponse;
  timestamp: Date;
};

export type ChatFilters = {
  proveedor_ids: number[];
  categoria_ids: number[];
};

/** Payload que va al backend — empata con ChatRequest de Pydantic */
export type ChatPayload = {
  mensaje: string;
  historial: { role: string; content: string }[];
  estado_conversacion?: RecomendacionRequest | null;
  filtro_proveedor_ids?: number[];
  filtro_categoria_ids?: number[];
};

// ─── Recomendación ───────────────────────────────────────────────────────────

export type RecomendacionRequest = {
  mensaje: string;
  nombre_evento?: string | null;
  tipo_evento?: string | null;
  tematica_detectada?: string | null;
  servicios_extra_detectados?: string[];
  cantidades_servicios?: Record<string, number>;
  fecha_evento_inicio?: string | null;
  fecha_evento_fin?: string | null;
  direccion?: string | null;
  aforo_estimado?: number | null;
  distrito?: string | null;
  presupuesto_maximo?: number | null;
  filtro_proveedor_ids?: number[];
  filtro_categoria_ids?: number[];
};


export type ItemRecomendado = {
  servicio_producto_id: number;
  nombre: string;
  cantidad: number;
  precio_unitario: number;
  horas?: number | null;
  subtotal: number;
  tipo: string;
  motivo: string;
  stock_maximo_simultaneo?: number | null;
};

export type PaqueteRecomendado = {
  paquete_id: number;
  nombre: string;
  descripcion?: string | null;
  precio_base: number;
  incluye: ItemRecomendado[];
};

export type PreReservaItem = {
  servicio_producto_id: number;
  cantidad: number;
  horas_contratadas?: number | null;
};

export type PreReservaPayload = {
  proveedor_id: number;
  paquete_id: number;
  nombre_evento: string;
  tipo_evento?: string | null;
  fecha_evento_inicio: string;
  fecha_evento_fin: string;
  direccion: string;
  aforo_estimado?: number | null;
  adicionales: PreReservaItem[];
};

export type ProveedorRecomendado = {
  proveedor_id: number;
  nombre_empresa: string;
  distrito?: string | null;
  calificacion_promedio?: number | null;
  paquete: PaqueteRecomendado;
  adicionales_sugeridos: ItemRecomendado[];
  total_estimado: number;
  adelanto_20: number;
  saldo_presencial: number;
  disponible: boolean;
  observaciones: string[];
  puede_prebloquear: boolean;
  datos_faltantes_prebloqueo: string[];
  payload_prebloqueo?: PreReservaPayload | null;
};

export type RecomendacionResponse = {
  respuesta: string;
  accion: string;
  requiere_fecha_hora: boolean;
  datos_faltantes_prebloqueo: string[];
  endpoint_prebloqueo: string;
  intencion_detectada: string[];
  estado_conversacion?: RecomendacionRequest | null;
  resultados_principales: ProveedorRecomendado[];
  otras_opciones: ProveedorRecomendado[];
};

export type PreReservaDetalle = {
  paquete_id?: number | null;
  servicio_producto_id?: number | null;
  nombre: string;
  tipo: string;
  cantidad: number;
  horas_contratadas?: number | null;
  precio_unitario: number;
  subtotal: number;
};

export type PreReservaResponse = {
  reserva_temp_id: string;
  proveedor_id: number;
  paquete_id: number;
  monto_total: number;
  monto_adelanto: number;
  monto_pendiente: number;
  minutos_restantes: number;
  detalles: PreReservaDetalle[];
  mensaje: string;
};

export type CheckoutClienteCreate = {
  nombre?: string;
  apellido?: string;
  email?: string;
  telefono?: string;
  password?: string;
  direccion?: string;
  metodo_pago: string;
};

export type CheckoutReservaResponse = {
  reserva_id: number;
  evento_id: number;
  cliente_id: number;
  pago_id: number;
  estado_pago: string;
  monto_total: number;
  monto_adelanto: number;
  monto_pendiente: number;
  mensaje: string;
};

// ─── Historial de Reservas ───────────────────────────────────────────────────

export type MisReservasDetalle = {
  nombre: string;
  tipo: string;
  cantidad: number;
  subtotal: number;
};

export type MisReservasItem = {
  reserva_id: number;
  estado: string;
  nombre_evento: string;
  tipo_evento: string | null;
  fecha_evento_inicio: string;
  fecha_evento_fin: string;
  direccion: string;
  nombre_empresa: string;
  monto_total: number;
  monto_adelanto: number;
  monto_pendiente: number;
  fecha_creacion: string;
  detalles: MisReservasDetalle[];
};

// ─── Reseñas ─────────────────────────────────────────────────────────────────

export type ResenaPublicaCreate = {
  proveedor_id: number;
  calificacion: number;
  comentario?: string | null;
};

export type ResenaPublicaOut = {
  id: number;
  proveedor_id: number;
  calificacion: number;
  comentario?: string | null;
  fecha: string;
  nombre_usuario: string;
};

// ─── UI State Types ──────────────────────────────────────────────────────────

export type Screen = "chat" | "detail" | "success" | "reservas";

export type AuthTab = "login" | "register";

export type AuthModalMode = "login" | "register" | null;

export type RegistroClienteDraft = {
  nombre: string;
  apellido: string;
  email: string;
  telefono?: string;
  password: string;
};

export type EventDraft = {
  fecha: string;
  horaInicio: string;
  direccion: string;
  invitados: string;
};

export type RegisterDraft = {
  nombre: string;
  apellido: string;
  email: string;
  telefono: string;
  password: string;
  metodoPago: string;
};

export type LoginDraft = {
  email: string;
  password: string;
  metodoPago: string;
};
