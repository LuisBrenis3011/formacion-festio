## **Backlog Organizado de Implementación — Festio**

**Fecha:** 2026-06-26

**Alcance principal:** Directorio `app/` (API FastAPI + servicios + modelos)

**Áreas adicionales:** `tests/` y `festio-frontend`

**Convención de prioridad:** 🔴 Crítico · 🟠 Alto · 🟡 Medio · 🟢 Bajo

## **Flujo de trabajo recomendado**

1. Cerrar primero seguridad y ownership para evitar que el sistema siga permitiendo accesos indebidos.
2. Montar después la base de testing para que los cambios críticos queden protegidos por pruebas.
3. Implementar las reglas de negocio faltantes en reservas y reseñas.
4. Refactorizar pagos, notificaciones y deuda técnica cuando la lógica crítica ya esté estable.
5. Atacar paginación, mejoras transversales y funcionalidades nuevas por ramas separadas.
6. Dejar frontend e integraciones externas para el final, salvo que bloqueen una demo o entrega inmediata.

## **Agrupación por ramas sugeridas**

| **Rama sugerida** | **Objetivo** | **Tareas agrupadas** |
| --- | --- | --- |
| `feat/seguridad-y-accesos` | Cerrar huecos de acceso, roles y ownership | `TASK-SEC-01`, `TASK-SEC-02`, `TASK-SEC-03`, `TASK-SEC-04`, `TASK-QA-01` |
| `test/base-de-pruebas` | Crear infraestructura de pruebas y cubrir auth, reservas, pagos y disponibilidad | `TASK-TEST-06`, `TASK-TEST-01`, `TASK-TEST-02`, `TASK-TEST-03`, `TASK-TEST-04`, `TASK-TEST-05` |
| `feat/reglas-negocio-reservas-resenas` | Completar reglas de negocio de cancelación y reseñas | `TASK-BIZ-01`, `TASK-BIZ-02`, `TASK-BIZ-03` |
| `refactor/pagos-y-notificaciones` | Normalizar servicios, repositorios y deuda técnica cercana al flujo de pagos | `TASK-BIZ-04`, `TASK-BIZ-05`, `TASK-BIZ-07`, `TASK-QA-03`, `TASK-QA-04` |
| `feat/paginacion-de-listados` | Añadir paginación a endpoints de lectura | `TASK-QA-02` |
| `feat/gestion-backend-proveedor` | Completar capacidades operativas del proveedor y catálogo | `TASK-FEAT-01`, `TASK-FEAT-02`, `TASK-FEAT-03`, `TASK-FEAT-05` |
| `feat/comunicaciones-y-frontend` | Resolver notificaciones reales y experiencia de frontend | `TASK-FEAT-04`, `TASK-FEAT-06`, `TASK-FEAT-07` |
| `chore/historico-validado` | Mantener referencia de tareas ya cerradas o ya implementadas | `TASK-BIZ-06` |

## **Dependencias clave**

- `TASK-TEST-06` debe ejecutarse antes del resto de tests de integración.
- `TASK-SEC-01` y `TASK-SEC-04` deberían cerrarse antes de probar paneles y acciones de proveedor.
- `TASK-BIZ-05` conviene resolver antes de `TASK-FEAT-04` porque ambas tocan notificaciones.
- `TASK-BIZ-06` aparece como completada y está directamente relacionada con `TASK-FEAT-01`; no se elimina, pero conviene validar si `FEAT-01` sigue pendiente o solo requiere ajuste/documentación.
- `TASK-FEAT-07` depende funcionalmente de que exista una vista backend útil para reservas del proveedor, idealmente `TASK-FEAT-02` y el estado de completado.

## **Rama 1 — Seguridad y control de acceso**

**Branch sugerida:** `feat/seguridad-y-accesos`

### **TASK-SEC-01 — Falta control de roles en endpoints**

- **Prioridad:** 🔴 Crítico
- **Archivos:** `catalogo.py`, `usuarios.py`, `proveedores.py`, `personal.py`
- **Problema:** Muchos endpoints solo validan que exista un token válido (`get_current_user`), pero no validan el rol. Eso permite que un `CLIENTE` pueda crear categorías, modificar proveedores o eliminar personal.
- **Qué hacer:** Usar `require_role(RolUsuario.PROVEEDOR)` en endpoints de personal y catálogo de servicios. La dependencia `require_role` ya existe; solo falta aplicarla en los routers.
- **Criterio de aceptación:** Un `CLIENTE` recibe `403 Forbidden` al intentar crear una categoría o entrar a endpoints de proveedor. Un `PROVEEDOR` puede crear su personal, pero no el de otro proveedor.

### **TASK-SEC-02 — El webhook de pagos no tiene autenticación**

- **Prioridad:** 🔴 Crítico
- **Archivo:** `pagos.py`
- **Problema:** Los endpoints `POST /{pago_id}/aprobar` y `POST /{pago_id}/rechazar` están completamente abiertos. Cualquier persona con acceso a la URL podría aprobar o rechazar pagos.
- **Qué hacer:** Agregar un header secreto tipo `X-Webhook-Secret` y validarlo contra una variable de entorno.
- **Criterio de aceptación:** Las solicitudes sin el secreto correcto reciben `401 Unauthorized`.

### **TASK-SEC-03 — Los endpoints de notificaciones no validan ownership**

- **Prioridad:** 🟠 Alto
- **Archivo:** `notificaciones.py`
- **Problema:** `GET /usuario/{usuario_id}` permite que cualquier usuario autenticado vea las notificaciones de otro usuario.
- **Qué hacer:** Comparar `usuario_id` del path con `usuario.id` del token JWT y permitir acceso solo si son iguales.
- **Criterio de aceptación:** Un cliente solo ve sus propias notificaciones.

### **TASK-SEC-04 — No se valida ownership en acciones sobre recursos**

- **Prioridad:** 🟠 Alto
- **Archivos:** `reservas.py`, `personal.py`
- **Problema:** `PATCH /{reserva_id}/cancelar` permite que cualquier usuario autenticado cancele cualquier reserva. Los endpoints de personal tampoco verifican que el `proveedor_id` del body pertenezca al proveedor autenticado.
- **Qué hacer:** Verificar que la reserva a cancelar pertenece al usuario autenticado. Verificar también que el personal se crea o edita solo para el proveedor autenticado.

### **TASK-QA-01 — Endpoint de clientes no tiene protección**

- **Prioridad:** 🟡 Medio
- **Archivo:** `clientes.py`
- **Problema:** `GET /clientes` y `POST /clientes` están completamente abiertos, sin autenticación.
- **Qué hacer:** Definir y aplicar la protección mínima necesaria según el rol esperado de consumo.

## **Rama 2 — Base de testing e infraestructura de pruebas**

**Branch sugerida:** `test/base-de-pruebas`

### **TASK-TEST-06 — Configurar `conftest.py` con BD de pruebas**

- **Prioridad:** 🔴 Crítico
- **Archivo nuevo:** `tests/conftest.py`
- **Problema:** Sin un `conftest.py` con fixtures para BD y `TestClient`, ningún test de integración puede funcionar.
- **Qué debe incluir:**

```python
# Fixture de BD SQLite en memoria
# Fixture de TestClient con la app de FastAPI
# Fixture de usuario autenticado (cliente, proveedor)
# Override de get_db para usar la BD de pruebas
# Override de redis_client con un mock
```

### **TASK-TEST-01 — Tests de autenticación y registro**

- **Prioridad:** 🔴 Crítico
- **Archivo:** `test_auth.py`
- **Problema:** No hay cobertura para registro, login ni endpoint `/me`.
- **Tests a implementar:**

```python
def test_registro_cliente_exitoso()
def test_registro_email_duplicado_retorna_400()
def test_registro_password_corta_retorna_422()
def test_registro_ruc_invalido_retorna_422()
def test_registro_telefono_invalido_retorna_422()
def test_login_exitoso_retorna_token()
def test_login_credenciales_incorrectas_retorna_401()
def test_login_cuenta_inactiva_retorna_403()
def test_me_retorna_datos_usuario()
def test_me_sin_token_retorna_401()
```

### **TASK-TEST-02 — Tests de reservas y checkout**

- **Prioridad:** 🔴 Crítico
- **Archivo:** `test_reservas.py`
- **Problema:** No hay cobertura sobre prebloqueo, checkout ni cancelación.
- **Tests a implementar:**

```python
def test_prebloquear_fecha_pasada_retorna_422()
def test_prebloquear_fin_antes_inicio_retorna_422()
def test_prebloquear_exitoso_retorna_temp_id()
def test_prebloquear_proveedor_inexistente_retorna_404()
def test_prebloquear_paquete_inactivo_retorna_404()
def test_checkout_simulado_bloqueo_expirado_retorna_408()
def test_checkout_simulado_exitoso()
def test_checkout_sin_datos_cliente_retorna_400()
def test_cancelar_reserva_completada_retorna_400()
def test_mis_reservas_retorna_lista()
def test_cantidad_cero_retorna_422()
```

### **TASK-TEST-03 — Tests de pagos**

- **Prioridad:** 🟠 Alto
- **Archivo:** `test_pagos.py`
- **Problema:** No hay cobertura del flujo de registro, aprobación, rechazo ni comprobantes.
- **Tests a implementar:**

```python
def test_registrar_pago_exitoso()
def test_registrar_pago_monto_negativo_retorna_422()
def test_registrar_pago_reserva_inexistente_retorna_404()
def test_aprobar_pago_exitoso()
def test_rechazar_pago_y_notificacion()
def test_comprobante_generado_despues_aprobacion()
def test_comprobante_reserva_sin_pago_retorna_404()
```

### **TASK-TEST-04 — Tests de disponibilidad**

- **Prioridad:** 🟠 Alto
- **Archivo:** `test_disponibilidad.py`
- **Problema:** No hay cobertura sobre disponibilidad real, stock ni capacidad humana.
- **Tests a implementar:**

```python
def test_consultar_disponibilidad_todo_disponible()
def test_consultar_stock_agotado_retorna_no_disponible()
def test_consultar_capacidad_humana_excedida()
def test_consultar_proveedor_inexistente()
def test_bloqueo_temporal_cuenta_como_ocupacion()
```

### **TASK-TEST-05 — Tests de validaciones Pydantic (schemas)**

- **Prioridad:** 🟡 Medio
- **Archivo nuevo:** `tests/test_schemas.py`
- **Problema:** Faltan tests unitarios puros para validar que los schemas rechazan datos inválidos sin necesidad de BD.
- **Tests a implementar:**

```python
def test_usuario_nombre_vacio_retorna_error()
def test_usuario_ruc_formato_invalido()
def test_usuario_telefono_no_peruano()
def test_evento_fecha_pasada()
def test_evento_fin_antes_inicio()
def test_detalle_cantidad_negativa()
def test_pago_monto_cero()
def test_resena_calificacion_fuera_rango()
def test_servicio_precio_negativo()
```

## **Rama 3 — Reglas de negocio de reservas y reseñas**

**Branch sugerida:** `feat/reglas-negocio-reservas-resenas`

### **TASK-BIZ-01 — Falta política de cancelación con tiempo límite**

- **Prioridad:** 🟠 Alto
- **Archivo:** `reserva_gestion_service.py`
- **Problema:** `cancelar_reserva()` solo verifica que la reserva no esté `COMPLETADA`, pero no aplica reglas de negocio sobre tiempo mínimo, reembolso ni liberación de ocupaciones.
- **Preguntas implícitas que la tarea debe resolver:** ¿Se puede cancelar 1 hora antes del evento? ¿Se devuelve el dinero? ¿Se libera inventario y capacidad humana al cancelar?
- **Qué hacer:**

```text
1. Validar un tiempo mínimo antes del evento para permitir la cancelación (ej. 48 horas).
2. Liberar los registros de OcupacionServicioProducto y OcupacionGlobalProveedor.
3. Actualizar el monto_pendiente y crear una política de reembolso.
```

- **Criterio de aceptación:** Si faltan menos de 48 horas para el evento, la cancelación es rechazada con mensaje descriptivo. Al cancelar, el stock se libera y vuelve a quedar disponible para nuevas reservas.

### **TASK-BIZ-02 — No se previene doble reseña del mismo usuario**

- **Prioridad:** 🟠 Alto
- **Archivo:** `resena_service.py`
- **Problema:** Un usuario puede crear múltiples reseñas para el mismo proveedor e inflar artificialmente la calificación promedio.
- **Qué hacer:** Verificar si ya existe una reseña del `usuario_id` para el `proveedor_id` antes de crear una nueva. Si ya existe, retornar `409 Conflict`.
- **Criterio de aceptación:** Un usuario solo puede dejar una reseña por proveedor. Si intenta crear otra, recibe error `409` con mensaje claro.

### **TASK-BIZ-03 — Validación redundante de calificación en servicio (ya la hace Pydantic)**

- **Prioridad:** 🟡 Medio
- **Archivo:** `resena_service.py`
- **Problema:** Las validaciones manuales `if not (1 <= datos.calificacion <= 5)` son redundantes porque `ResenaCreate` y `ResenaPublicaCreate` ya validan con `Field(ge=1, le=5)`.
- **Qué hacer:** Eliminar las validaciones manuales de `calificacion` en `crear_resena()` y `crear_resena_publica()`.

## **Rama 4 — Refactor de pagos, notificaciones y deuda técnica cercana**

**Branch sugerida:** `refactor/pagos-y-notificaciones`

### **TASK-BIZ-04 — `pago_service.py` usa `db: Session` directamente en vez de repositorios**

- **Prioridad:** 🟡 Medio
- **Archivo:** `pago_service.py`
- **Problema:** Mientras otros servicios usan el patrón Repository, `pago_service` recibe `db: Session` directamente y hace `db.query(...)`. Eso rompe consistencia y dificulta los tests unitarios con mocks.
- **Qué hacer:** Refactorizar para recibir `PagoTransaccionRepository` en vez de `Session`. Actualizar el router `pagos.py` para inyectar el repo con `Depends()`.

### **TASK-BIZ-05 — `notificacion_service.py` mezcla firmas repo y `db: Session`**

- **Prioridad:** 🟡 Medio
- **Archivos:** `notificacion_service.py`, `pago_service.py`
- **Problema:** `notificar_confirmacion_reserva()` recibe `repo: NotificacionRepository`, pero desde `pago_service.aprobar_pago_completo()` se le estaría pasando `db`, lo que puede fallar en runtime.
- **Qué hacer:** Verificar si la llamada actual funciona o falla. Crear `NotificacionRepository(db)` dentro de `aprobar_pago_completo()` antes de pasar la dependencia a `notificacion_service`.

### **TASK-BIZ-07 — `datetime.utcnow()` está deprecado en Python 3.12+**

- **Prioridad:** 🟢 Bajo
- **Archivos:** `checkout_service.py`, `security.py`, `reserva_gestion_service.py`
- **Problema:** `datetime.utcnow()` está deprecado desde Python 3.12. El reemplazo correcto es `datetime.now(timezone.utc)`.
- **Qué hacer:** Reemplazar todas las ocurrencias de `datetime.utcnow()` por `datetime.now(timezone.utc)`.

### **TASK-QA-03 — `BaseRepository.update()` tiene firma inconsistente**

- **Prioridad:** 🟢 Bajo
- **Archivo:** `base.py`
- **Problema:** `update()` espera `db_obj: ModelType` como primer argumento, pero en `proveedor_service.py` se llama como `repo.update(proveedor_id, datos)` pasando un `int`. Aunque algunos repos concretos podrían sobrescribir la firma, esto sigue siendo propenso a errores.
- **Qué hacer:** Verificar que todos los repos concretos que usan `update` tengan la firma correcta y documentar la firma esperada.

### **TASK-QA-04 — El comprobante autogenerado no contempla concurrencia**

- **Prioridad:** 🟢 Bajo
- **Archivo:** `pago_service.py`
- **Problema:** La generación del número correlativo con `ultimo.id + 1` puede producir duplicados bajo carga concurrente.
- **Qué hacer:** Usar una secuencia en la BD o `SELECT MAX(id) FOR UPDATE` para evitar condiciones de carrera.

## **Rama 5 — Paginación y escalabilidad de listados**

**Branch sugerida:** `feat/paginacion-de-listados`

### **TASK-QA-02 — Paginación ausente en todos los endpoints de listado**

- **Prioridad:** 🟡 Medio
- **Archivos:** Todos los routers con `GET /` que retornan listas.
- **Problema:** Ningún endpoint de listado tiene paginación. Con muchos registros, las respuestas crecerán demasiado.
- **Qué hacer:** Agregar parámetros `skip: int = Query(0, ge=0)` y `limit: int = Query(20, ge=1, le=100)` a los endpoints de listado. Aplicar `.offset(skip).limit(limit)` en las queries.
- **Endpoints afectados:** `/usuarios`, `/clientes`, `/proveedores`, `/personal/proveedor/{id}`, `/catalogo/servicios`, `/resenas/proveedor/{id}`, `/notificaciones/usuario/{id}`, `/reservas/mis-reservas`.

## **Rama 6 — Funcionalidades backend para proveedor y catálogo**

**Branch sugerida:** `feat/gestion-backend-proveedor`

### **TASK-FEAT-01 — Endpoint `PATCH /reservas/{id}/completar`**

- **Prioridad:** No especificada en el backlog original
- **Área:** Backend
- **Objetivo:** Marcar reservas como completadas y registrar el pago del saldo pendiente (90%).
- **Nota de planificación:** Esta tarea está vinculada con `TASK-BIZ-06`, que figura como completada. Mantenerla aquí sirve para validar si el endpoint ya existe y solo falta endurecerlo, documentarlo o integrarlo con otros flujos.

### **TASK-FEAT-02 — Endpoint para que el proveedor gestione sus reservas**

- **Prioridad:** No especificada en el backlog original
- **Área:** Backend
- **Objetivo:** Crear `GET /proveedor/mis-reservas`, ya que hoy solo existe la vista del cliente.

### **TASK-FEAT-03 — Soft-delete en servicios y paquetes del proveedor**

- **Prioridad:** No especificada en el backlog original
- **Área:** Backend
- **Objetivo:** Agregar `deleted_at` a las queries de catálogo para que los ítems eliminados no aparezcan en búsquedas públicas.

### **TASK-FEAT-05 — Rate limiting en endpoints públicos**

- **Prioridad:** No especificada en el backlog original
- **Área:** Backend
- **Problema:** Los endpoints públicos como login, registro y chat IA no tienen rate limiting.
- **Qué hacer:** Agregar middleware como `slowapi` para prevenir abuso.

## **Rama 7 — Comunicaciones reales y frontend**

**Branch sugerida:** `feat/comunicaciones-y-frontend`

### **TASK-FEAT-04 — Email real en notificaciones**

- **Prioridad:** No especificada en el backlog original
- **Área:** Backend / Integración externa
- **Problema:** `notificacion_service.py` solo registra notificaciones en la BD como `PUSH`, pero nunca envía un email real.
- **Qué hacer:** Implementar el envío con un servicio de email como SendGrid o Amazon SES.

### **TASK-FEAT-06 — Modal flotante de reseñas por servicio**

- **Prioridad:** 🟠 Alto
- **Área:** Frontend (`festio-frontend`)
- **Problema:** El backend permite leer reseñas públicamente, pero mostrarlas embebidas en la página del servicio/proveedor alarga demasiado la vista y ensucia el diseño.
- **Qué hacer:** Mostrar un botón `Ver Reseñas (X)` junto con estrellas y rating promedio. Al hacer clic, abrir un modal u overlay sobre toda la vista. El modal debe consumir los endpoints públicos de reseñas y mostrarlas en una lista desplazable.
- **Criterio de aceptación:** La vista de detalle del servicio se mantiene limpia y minimalista. El modal aparece de forma fluida, se puede cerrar haciendo clic fuera o en una `X`, y soporta scroll cuando hay muchas reseñas.

### **TASK-FEAT-07 — Panel de gestión de reservas (Proveedor)**

- **Prioridad:** 🟡 Medio
- **Área:** Frontend (`festio-frontend`)
- **Problema:** El cliente tiene su vista de `Mis Reservas`, pero el proveedor necesita un panel equivalente para ver sus eventos programados y, si aplica, cambiar el estado a `COMPLETADA` al terminar.
- **Qué hacer:** Construir la vista del proveedor usando los endpoints backend relacionados, especialmente si `TASK-FEAT-02` y el flujo de completado ya están disponibles.

## **Histórico y validación de tareas ya cerradas**

**Branch sugerida:** `chore/historico-validado`

### **TASK-BIZ-06 — No hay endpoint para completar una reserva (COMPLETADA)**

- **Prioridad:** 🟡 Medio
- **Archivo:** `reserva_gestion_service.py`
- **Estado en backlog original:** **COMPLETADA**
- **Contexto:** El enum `EstadoReserva` tiene `COMPLETADA`, pero originalmente no existía un endpoint para marcar una reserva como completada después de que el evento termina. Tampoco existía un flujo para registrar el pago del 90% restante presencial.
- **Qué se había planteado hacer:**

```text
1. Crear PATCH /reservas/{id}/completar (solo PROVEEDOR).
2. Validar que se haya registrado un pago del saldo pendiente (SALDO_PRESENCIAL).
3. Cambiar estado a COMPLETADA.
```

## **Resumen ejecutivo por bloque**

| **Bloque** | **Tareas** | **Prioridad máxima** | **Motivo de ejecución** |
| --- | --- | --- | --- |
| Seguridad y acceso | `SEC-01`, `SEC-02`, `SEC-03`, `SEC-04`, `QA-01` | 🔴 Crítico | Cierra exposición directa de datos y acciones sensibles |
| Base de testing | `TEST-06`, `TEST-01`, `TEST-02`, `TEST-03`, `TEST-04`, `TEST-05` | 🔴 Crítico | Permite validar y proteger cambios futuros |
| Reglas de negocio | `BIZ-01`, `BIZ-02`, `BIZ-03` | 🟠 Alto | Corrige comportamiento funcional visible para usuarios |
| Refactor de pagos y notificaciones | `BIZ-04`, `BIZ-05`, `BIZ-07`, `QA-03`, `QA-04` | 🟡 Medio | Reduce deuda técnica y riesgo operativo en pagos |
| Escalabilidad de listados | `QA-02` | 🟡 Medio | Evita respuestas excesivas y mejora consumo de API |
| Features backend | `FEAT-01`, `FEAT-02`, `FEAT-03`, `FEAT-05` | Variable | Extiende capacidades operativas del proveedor |
| Features frontend e integraciones | `FEAT-04`, `FEAT-06`, `FEAT-07` | 🟠 Alto | Mejora experiencia de usuario y comunicaciones reales |
