import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { X, Loader2, Building2, User, ArrowLeft } from "lucide-react";
import { useAuth } from "../hooks/useAuth";
import { useNavigate } from "react-router-dom";
import type { RegistroProveedorDraft } from "../services/authService";

// ── Zod schemas (defined outside component for resolver caching — formcfg rule) ──

const loginSchema = z.object({
  email: z.string().email("Ingresa un email válido"),
  password: z.string().min(1, "La contraseña es obligatoria"),
});

const clienteSchema = z.object({
  nombre: z.string().min(1, "El nombre es obligatorio"),
  apellido: z.string().min(1, "El apellido es obligatorio"),
  email: z.string().email("Ingresa un email válido"),
  telefono: z.string().optional(),
  password: z.string().min(6, "Mínimo 6 caracteres"),
});

const proveedorSchema = z.object({
  nombre: z.string().min(1, "El nombre es obligatorio"),
  apellido: z.string().min(1, "El apellido es obligatorio"),
  email: z.string().email("Ingresa un email válido"),
  telefono: z.string().optional(),
  password: z.string().min(6, "Mínimo 6 caracteres"),
  nombre_empresa: z.string().min(1, "El nombre de empresa es obligatorio"),
  ruc: z.string().min(1, "El RUC es obligatorio"),
  distrito: z.string().min(1, "El distrito es obligatorio"),
});

type LoginFormData = z.infer<typeof loginSchema>;
type ClienteFormData = z.infer<typeof clienteSchema>;
type ProveedorFormData = z.infer<typeof proveedorSchema>;

type RolSeleccion = "CLIENTE" | "PROVEEDOR" | null;

// ── Sub-components (no inline — rerender rule) ──────────────────────────────

function LoginForm({ onClose }: { onClose: () => void }) {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    mode: "onSubmit",
    defaultValues: { email: "", password: "" },
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormData) => {
    setServerError(null);
    try {
      await login({ email: data.email, password: data.password, metodoPago: "" });
      onClose();
      // useEffect en AuthProvider recarga user, luego verificamos
      // El redirect se maneja después basado en el rol
      const token = localStorage.getItem("festio_token");
      if (token) {
        // Quick check: read the token to see role
        try {
          const payload = JSON.parse(atob(token.split(".")[1]));
          if (payload.rol === "PROVEEDOR") {
            navigate("/proveedor/dashboard");
          }
        } catch {
          // ignore parse errors — user stays on chat
        }
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Error al iniciar sesión";
      setServerError(message);
    }
  };

  return (
    <form className="auth-modal-form" onSubmit={handleSubmit(onSubmit)}>
      <div className="auth-modal-fields">
        <label className="wide-field" id="login-email-label">
          <span>Correo electrónico</span>
          <input
            id="login-email"
            type="email"
            autoComplete="email"
            {...register("email")}
          />
          {errors.email ? <p className="field-error">{errors.email.message}</p> : null}
        </label>

        <label className="wide-field" id="login-password-label">
          <span>Contraseña</span>
          <input
            id="login-password"
            type="password"
            autoComplete="current-password"
            {...register("password")}
          />
          {errors.password ? <p className="field-error">{errors.password.message}</p> : null}
        </label>
      </div>

      {serverError ? <p className="inline-error">{serverError}</p> : null}

      <button
        id="login-submit"
        className="primary-action wide-field"
        type="submit"
        disabled={isSubmitting}
      >
        {isSubmitting ? <Loader2 className="spin" size={18} /> : null}
        {isSubmitting ? "Ingresando..." : "Iniciar sesión"}
      </button>
    </form>
  );
}

function ClienteRegisterForm({ onClose }: { onClose: () => void }) {
  const { registroCliente } = useAuth();
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ClienteFormData>({
    mode: "onSubmit",
    defaultValues: { nombre: "", apellido: "", email: "", telefono: "", password: "" },
    resolver: zodResolver(clienteSchema),
  });

  const onSubmit = async (data: ClienteFormData) => {
    setServerError(null);
    try {
      await registroCliente(data);
      onClose();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Error al registrarse";
      setServerError(message);
    }
  };

  return (
    <form className="auth-modal-form" onSubmit={handleSubmit(onSubmit)}>
      <div className="auth-modal-fields">
        <label id="cliente-nombre-label">
          <span>Nombre</span>
          <input id="cliente-nombre" type="text" autoComplete="given-name" {...register("nombre")} />
          {errors.nombre ? <p className="field-error">{errors.nombre.message}</p> : null}
        </label>

        <label id="cliente-apellido-label">
          <span>Apellido</span>
          <input id="cliente-apellido" type="text" autoComplete="family-name" {...register("apellido")} />
          {errors.apellido ? <p className="field-error">{errors.apellido.message}</p> : null}
        </label>

        <label className="wide-field" id="cliente-email-label">
          <span>Correo electrónico</span>
          <input id="cliente-email" type="email" autoComplete="email" {...register("email")} />
          {errors.email ? <p className="field-error">{errors.email.message}</p> : null}
        </label>

        <label id="cliente-telefono-label">
          <span>Teléfono (opcional)</span>
          <input id="cliente-telefono" type="tel" autoComplete="tel" {...register("telefono")} />
        </label>

        <label id="cliente-password-label">
          <span>Contraseña</span>
          <input id="cliente-password" type="password" autoComplete="new-password" {...register("password")} />
          {errors.password ? <p className="field-error">{errors.password.message}</p> : null}
        </label>
      </div>

      {serverError ? <p className="inline-error">{serverError}</p> : null}

      <button
        id="cliente-register-submit"
        className="primary-action wide-field"
        type="submit"
        disabled={isSubmitting}
      >
        {isSubmitting ? <Loader2 className="spin" size={18} /> : null}
        {isSubmitting ? "Creando cuenta..." : "Crear mi cuenta"}
      </button>
    </form>
  );
}

function ProveedorRegisterForm({ onClose }: { onClose: () => void }) {
  const { registroProveedor } = useAuth();
  const navigate = useNavigate();
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ProveedorFormData>({
    mode: "onSubmit",
    defaultValues: {
      nombre: "",
      apellido: "",
      email: "",
      telefono: "",
      password: "",
      nombre_empresa: "",
      ruc: "",
      distrito: "",
    },
    resolver: zodResolver(proveedorSchema),
  });

  const onSubmit = async (data: ProveedorFormData) => {
    setServerError(null);
    try {
      const provDraft: RegistroProveedorDraft = {
        nombre: data.nombre,
        apellido: data.apellido,
        email: data.email,
        telefono: data.telefono,
        password: data.password,
        nombre_empresa: data.nombre_empresa,
        ruc: data.ruc,
        distrito: data.distrito,
      };
      await registroProveedor(provDraft);
      onClose();
      navigate("/proveedor/dashboard");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Error al registrarse";
      setServerError(message);
    }
  };

  return (
    <form className="auth-modal-form" onSubmit={handleSubmit(onSubmit)}>
      <div className="auth-modal-fields">
        <label id="prov-nombre-label">
          <span>Nombre</span>
          <input id="prov-nombre" type="text" autoComplete="given-name" {...register("nombre")} />
          {errors.nombre ? <p className="field-error">{errors.nombre.message}</p> : null}
        </label>

        <label id="prov-apellido-label">
          <span>Apellido</span>
          <input id="prov-apellido" type="text" autoComplete="family-name" {...register("apellido")} />
          {errors.apellido ? <p className="field-error">{errors.apellido.message}</p> : null}
        </label>

        <label className="wide-field" id="prov-email-label">
          <span>Correo electrónico</span>
          <input id="prov-email" type="email" autoComplete="email" {...register("email")} />
          {errors.email ? <p className="field-error">{errors.email.message}</p> : null}
        </label>

        <label id="prov-telefono-label">
          <span>Teléfono (opcional)</span>
          <input id="prov-telefono" type="tel" autoComplete="tel" {...register("telefono")} />
        </label>

        <label id="prov-password-label">
          <span>Contraseña</span>
          <input id="prov-password" type="password" autoComplete="new-password" {...register("password")} />
          {errors.password ? <p className="field-error">{errors.password.message}</p> : null}
        </label>

        <div className="auth-divider wide-field">
          <span>Datos de la Empresa</span>
        </div>

        <label className="wide-field" id="prov-empresa-label">
          <span>Nombre de Empresa</span>
          <input id="prov-empresa" type="text" {...register("nombre_empresa")} />
          {errors.nombre_empresa ? <p className="field-error">{errors.nombre_empresa.message}</p> : null}
        </label>

        <label id="prov-ruc-label">
          <span>RUC</span>
          <input id="prov-ruc" type="text" {...register("ruc")} />
          {errors.ruc ? <p className="field-error">{errors.ruc.message}</p> : null}
        </label>

        <label id="prov-distrito-label">
          <span>Distrito</span>
          <input id="prov-distrito" type="text" {...register("distrito")} />
          {errors.distrito ? <p className="field-error">{errors.distrito.message}</p> : null}
        </label>
      </div>

      {serverError ? <p className="inline-error">{serverError}</p> : null}

      <button
        id="prov-register-submit"
        className="primary-action wide-field"
        type="submit"
        disabled={isSubmitting}
      >
        {isSubmitting ? <Loader2 className="spin" size={18} /> : null}
        {isSubmitting ? "Creando cuenta..." : "Registrarme como Proveedor"}
      </button>
    </form>
  );
}

// ── Selector de Rol ─────────────────────────────────────────────────────────

function RolSelector({ onSelect }: { onSelect: (rol: RolSeleccion) => void }) {
  return (
    <div className="rol-selector">
      <p className="rol-selector-title">¿Quién eres?</p>
      <p className="rol-selector-subtitle">Selecciona tu perfil para personalizar tu experiencia</p>

      <div className="rol-cards">
        <button
          id="select-rol-cliente"
          className="rol-card"
          type="button"
          onClick={() => onSelect("CLIENTE")}
        >
          <div className="rol-card-icon rol-card-icon-cliente">
            <User size={28} />
          </div>
          <strong>Cliente</strong>
          <span>Busco servicios para mi evento</span>
        </button>

        <button
          id="select-rol-proveedor"
          className="rol-card"
          type="button"
          onClick={() => onSelect("PROVEEDOR")}
        >
          <div className="rol-card-icon rol-card-icon-proveedor">
            <Building2 size={28} />
          </div>
          <strong>Proveedor de Eventos</strong>
          <span>Ofrezco servicios para eventos</span>
        </button>
      </div>
    </div>
  );
}

// ── AuthModal principal ─────────────────────────────────────────────────────

export function AuthModal() {
  const { authModalMode, closeAuthModal } = useAuth();
  const [registerRol, setRegisterRol] = useState<RolSeleccion>(null);

  if (!authModalMode) return null;

  const isLogin = authModalMode === "login";

  const handleClose = () => {
    closeAuthModal();
    setRegisterRol(null);
  };


  const handleBackToRolSelector = () => {
    setRegisterRol(null);
  };

  return (
    <div className="modal-backdrop" role="presentation" onClick={handleClose}>
      <section
        className="auth-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="auth-modal-title"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          id="auth-modal-close"
          className="close-button"
          type="button"
          onClick={handleClose}
        >
          <X size={20} />
        </button>

        <div className="auth-modal-head">
          {!isLogin && registerRol ? (
            <button
              className="auth-back-button"
              type="button"
              onClick={handleBackToRolSelector}
            >
              <ArrowLeft size={16} />
              Cambiar tipo de cuenta
            </button>
          ) : null}

          <h2 id="auth-modal-title">
            {isLogin
              ? "Bienvenido de vuelta"
              : registerRol === "CLIENTE"
                ? "Crea tu cuenta"
                : registerRol === "PROVEEDOR"
                  ? "Registro de Proveedor"
                  : "Únete a Festio"}
          </h2>
          <p>
            {isLogin
              ? "Inicia sesión para continuar"
              : registerRol
                ? registerRol === "CLIENTE"
                  ? "Completa tus datos para empezar"
                  : "Registra tu empresa y empieza a ofrecer servicios"
                : "Selecciona tu tipo de cuenta"}
          </p>
        </div>

        {isLogin ? (
          <LoginForm onClose={handleClose} />
        ) : registerRol === "CLIENTE" ? (
          <ClienteRegisterForm onClose={handleClose} />
        ) : registerRol === "PROVEEDOR" ? (
          <ProveedorRegisterForm onClose={handleClose} />
        ) : (
          <RolSelector onSelect={setRegisterRol} />
        )}
      </section>
    </div>
  );
}
