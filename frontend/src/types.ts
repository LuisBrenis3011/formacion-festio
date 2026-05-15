export type RecomendacionRequest = {
  mensaje: string;
  nombre_evento?: string;
  tipo_evento?: string;
  fecha_evento_inicio?: string;
  fecha_evento_fin?: string;
  direccion?: string;
  aforo_estimado?: number;
  distrito?: string;
  presupuesto_maximo?: number;
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
  nombre: string;
  apellido: string;
  email: string;
  telefono?: string;
  password: string;
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

export type ServicioProducto = {
  id: number;
  proveedor_id: number;
  categoria_id?: number | null;
  nombre: string;
  tipo: string;
  requiere_persona: boolean;
  precio_unitario: number;
  stock_maximo_simultaneo: number;
  duracion_base_horas?: number | null;
  estado: string;
};
