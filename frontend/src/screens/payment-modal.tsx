import { useState, type Dispatch, type FormEvent, type SetStateAction } from "react";
import { CreditCard, Loader2, X, CheckCircle } from "lucide-react";
import { PaymentMethodSelect } from "../components/payment-method-select";
import { PaymentDetailsForm, type PaymentDetailsData } from "../components/payment-details-form";
import { money } from "../lib/format";
import type { AuthTab, AuthUser, LoginDraft, PreReservaResponse, RegisterDraft } from "../types";

type PaymentModalProps = {
  preReserva: PreReservaResponse;
  isAuthenticated: boolean;
  user: AuthUser | null;
  authTab: AuthTab;
  setAuthTab: (tab: AuthTab) => void;
  registerDraft: RegisterDraft;
  setRegisterDraft: Dispatch<SetStateAction<RegisterDraft>>;
  loginDraft: LoginDraft;
  setLoginDraft: Dispatch<SetStateAction<LoginDraft>>;
  loadingPayment: boolean;
  error: string | null;
  onSubmit: (event: FormEvent<HTMLFormElement>, metodoPago: string) => void;
  onClose: () => void;
};

export function PaymentModal({
  preReserva,
  isAuthenticated,
  user,
  authTab,
  setAuthTab,
  registerDraft,
  setRegisterDraft,
  loginDraft,
  setLoginDraft,
  loadingPayment,
  error,
  onSubmit,
  onClose,
}: PaymentModalProps) {
  const [metodoPago, setMetodoPago] = useState("TARJETA");
  const [paymentDetails, setPaymentDetails] = useState<PaymentDetailsData>({});
  const selectedMetodoPago = isAuthenticated
    ? metodoPago
    : authTab === "login"
      ? loginDraft.metodoPago
      : registerDraft.metodoPago;

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    onSubmit(e, selectedMetodoPago);
  };

  return (
    <div className="modal-backdrop" role="presentation">
      <section className="payment-modal" role="dialog" aria-modal="true" aria-labelledby="payment-title">
        <button className="close-button" type="button" onClick={onClose}>
          <X size={20} />
        </button>
        <div className="modal-head">
          <span>Confirma tu reserva</span>
          <h2 id="payment-title">Adelanto a pagar: {money.format(preReserva.monto_adelanto)}</h2>
          <p>El saldo de {money.format(preReserva.monto_pendiente)} se paga en el local.</p>
        </div>

        {error && <p className="inline-error">{error}</p>}

        <form className="auth-form" onSubmit={handleSubmit}>
          {isAuthenticated && user ? (
            /* ─── USUARIO AUTENTICADO: solo método de pago ─── */
            <>
              <div className="auth-user-summary">
                <div className="auth-user-avatar">
                  {(user.nombre.charAt(0) || "C").toUpperCase()}
                </div>
                <div className="auth-user-details">
                  <strong>{user.nombre} {user.apellido}</strong>
                  <span><CheckCircle size={12} style={{ display: "inline", verticalAlign: "middle" }} /> Sesión activa</span>
                </div>
              </div>

              <PaymentMethodSelect
                value={metodoPago}
                onChange={setMetodoPago}
              />

              <PaymentDetailsForm
                metodoPago={metodoPago}
                details={paymentDetails}
                onChange={setPaymentDetails}
              />
            </>
          ) : (
            /* ─── USUARIO NO AUTENTICADO: login/registro + método de pago ─── */
            <>
              <div className="auth-tabs">
                <button
                  className={authTab === "login" ? "active" : ""}
                  type="button"
                  onClick={() => setAuthTab("login")}
                >
                  Iniciar sesión
                </button>
                <button
                  className={authTab === "register" ? "active" : ""}
                  type="button"
                  onClick={() => setAuthTab("register")}
                >
                  Registrarse
                </button>
              </div>

              {authTab === "register" ? (
                <>
                  <label className="wide-field">
                    <span>Nombre</span>
                    <input
                      required
                      value={registerDraft.nombre}
                      onChange={(e) => setRegisterDraft((prev) => ({ ...prev, nombre: e.target.value }))}
                    />
                  </label>
                  <label className="wide-field">
                    <span>Apellido</span>
                    <input
                      required
                      value={registerDraft.apellido}
                      onChange={(e) => setRegisterDraft((prev) => ({ ...prev, apellido: e.target.value }))}
                    />
                  </label>
                  <label className="wide-field">
                    <span>Email</span>
                    <input
                      required
                      type="email"
                      value={registerDraft.email}
                      onChange={(e) => setRegisterDraft((prev) => ({ ...prev, email: e.target.value }))}
                    />
                  </label>
                  <label className="wide-field">
                    <span>Teléfono</span>
                    <input
                      value={registerDraft.telefono}
                      onChange={(e) => setRegisterDraft((prev) => ({ ...prev, telefono: e.target.value }))}
                    />
                  </label>
                  <label className="wide-field">
                    <span>Password</span>
                    <input
                      required
                      type="password"
                      value={registerDraft.password}
                      onChange={(e) => setRegisterDraft((prev) => ({ ...prev, password: e.target.value }))}
                    />
                  </label>
                </>
              ) : (
                <>
                  <label className="wide-field">
                    <span>Email</span>
                    <input
                      required
                      type="email"
                      value={loginDraft.email}
                      onChange={(e) => setLoginDraft((prev) => ({ ...prev, email: e.target.value }))}
                    />
                  </label>
                  <label className="wide-field">
                    <span>Password</span>
                    <input
                      required
                      type="password"
                      value={loginDraft.password}
                      onChange={(e) => setLoginDraft((prev) => ({ ...prev, password: e.target.value }))}
                    />
                  </label>
                </>
              )}

              <PaymentMethodSelect
                value={authTab === "login" ? loginDraft.metodoPago : registerDraft.metodoPago}
                onChange={(value) => {
                  setMetodoPago(value);
                  if (authTab === "login") {
                    setLoginDraft((prev) => ({ ...prev, metodoPago: value }));
                  } else {
                    setRegisterDraft((prev) => ({ ...prev, metodoPago: value }));
                  }
                }}
              />

              <PaymentDetailsForm
                metodoPago={selectedMetodoPago}
                details={paymentDetails}
                onChange={setPaymentDetails}
              />
            </>
          )}

          <button className="primary-action wide-field" type="submit" disabled={loadingPayment}>
            {loadingPayment ? <Loader2 className="spin" size={18} /> : <CreditCard size={18} />}
            Confirmar pago
          </button>
        </form>
      </section>
    </div>
  );
}
