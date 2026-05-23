import { type FormEvent } from "react";
import { CreditCard, Loader2, X } from "lucide-react";
import { PaymentMethodSelect } from "../components/payment-method-select";
import { money } from "../lib/format";
import type { AuthTab, LoginDraft, PreReservaResponse, RegisterDraft } from "../types";

type PaymentModalProps = {
  preReserva: PreReservaResponse;
  authTab: AuthTab;
  setAuthTab: (tab: AuthTab) => void;
  registerDraft: RegisterDraft;
  setRegisterDraft: React.Dispatch<React.SetStateAction<RegisterDraft>>;
  loginDraft: LoginDraft;
  setLoginDraft: React.Dispatch<React.SetStateAction<LoginDraft>>;
  loadingPayment: boolean;
  error: string | null;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onClose: () => void;
};

export function PaymentModal({
  preReserva,
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
  return (
    <div className="modal-backdrop" role="presentation">
      <section className="payment-modal" role="dialog" aria-modal="true" aria-labelledby="payment-title">
        <button className="close-button" type="button" onClick={onClose}>
          <X size={20} />
        </button>
        <div className="modal-head">
          <span>Pago simulado</span>
          <h2 id="payment-title">{money.format(preReserva.monto_adelanto)} de adelanto</h2>
          <p>El saldo de {money.format(preReserva.monto_pendiente)} se paga en el local.</p>
        </div>

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

        {error && <p className="inline-error">{error}</p>}

        <form className="auth-form" onSubmit={onSubmit}>
          {authTab === "register" ? (
            <>
              <label>
                <span>Nombre</span>
                <input
                  required
                  value={registerDraft.nombre}
                  onChange={(e) => setRegisterDraft((prev) => ({ ...prev, nombre: e.target.value }))}
                />
              </label>
              <label>
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
              <label>
                <span>Teléfono</span>
                <input
                  value={registerDraft.telefono}
                  onChange={(e) => setRegisterDraft((prev) => ({ ...prev, telefono: e.target.value }))}
                />
              </label>
              <label>
                <span>Password</span>
                <input
                  required
                  type="password"
                  value={registerDraft.password}
                  onChange={(e) => setRegisterDraft((prev) => ({ ...prev, password: e.target.value }))}
                />
              </label>
              <PaymentMethodSelect
                value={registerDraft.metodoPago}
                onChange={(value) => setRegisterDraft((prev) => ({ ...prev, metodoPago: value }))}
              />
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
              <PaymentMethodSelect
                value={loginDraft.metodoPago}
                onChange={(value) => setLoginDraft((prev) => ({ ...prev, metodoPago: value }))}
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
