import { useState } from "react";
import { useAuth } from "../hooks/useAuth";
import type { LoginDraft } from "../types";
import { type RegistroProveedorDraft } from "../services/authService";
import { useNavigate } from "react-router-dom";

export function LoginScreen() {
  const { login, registroProveedor } = useAuth();
  const navigate = useNavigate();
  const [isLogin, setIsLogin] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const [loginForm, setLoginForm] = useState<LoginDraft>({
    email: "",
    password: "",
    metodoPago: "", // no se usa aquí pero está en el type
  });

  const [registerForm, setRegisterForm] = useState<RegistroProveedorDraft>({
    nombre: "",
    apellido: "",
    email: "",
    password: "",
    nombre_empresa: "",
    ruc: "",
    distrito: "",
    telefono: "",
  });

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    try {
      await login(loginForm);
      // El ProtectedRoute se encarga de redirigir según el rol
      navigate("/proveedor/dashboard");
    } catch (err: any) {
      setError(err.message || "Error al iniciar sesión");
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    try {
      await registroProveedor(registerForm);
      navigate("/proveedor/dashboard");
    } catch (err: any) {
      setError(err.message || "Error al registrarse");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-white p-8 rounded-2xl shadow-xl">
        <div className="text-center">
          <h2 className="text-3xl font-extrabold text-gray-900 font-display">
            Festio <span className="text-primary">B2B</span>
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            {isLogin ? "Inicia sesión en tu cuenta" : "Únete como proveedor"}
          </p>
        </div>

        {error && (
          <div className="bg-red-50 text-red-500 p-3 rounded-md text-sm border border-red-200">
            {error}
          </div>
        )}

        <div className="flex border-b border-gray-200 mb-6">
          <button
            className={`flex-1 py-2 text-center text-sm font-medium border-b-2 transition-colors ${
              isLogin ? "border-primary text-primary" : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
            onClick={() => { setIsLogin(true); setError(null); }}
          >
            Iniciar Sesión
          </button>
          <button
            className={`flex-1 py-2 text-center text-sm font-medium border-b-2 transition-colors ${
              !isLogin ? "border-primary text-primary" : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
            onClick={() => { setIsLogin(false); setError(null); }}
          >
            Registrarse
          </button>
        </div>

        {isLogin ? (
          <form className="mt-8 space-y-6" onSubmit={handleLoginSubmit}>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Correo electrónico</label>
                <input
                  type="email"
                  required
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm p-2 border"
                  value={loginForm.email}
                  onChange={(e) => setLoginForm({ ...loginForm, email: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Contraseña</label>
                <input
                  type="password"
                  required
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm p-2 border"
                  value={loginForm.password}
                  onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50"
            >
              {isLoading ? "Cargando..." : "Entrar al Panel"}
            </button>
          </form>
        ) : (
          <form className="mt-8 space-y-6" onSubmit={handleRegisterSubmit}>
            <div className="space-y-4 max-h-[60vh] overflow-y-auto pr-2">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Nombre</label>
                  <input
                    type="text"
                    required
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm p-2 border"
                    value={registerForm.nombre}
                    onChange={(e) => setRegisterForm({ ...registerForm, nombre: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Apellido</label>
                  <input
                    type="text"
                    required
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm p-2 border"
                    value={registerForm.apellido}
                    onChange={(e) => setRegisterForm({ ...registerForm, apellido: e.target.value })}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Correo electrónico</label>
                <input
                  type="email"
                  required
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm p-2 border"
                  value={registerForm.email}
                  onChange={(e) => setRegisterForm({ ...registerForm, email: e.target.value })}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Teléfono</label>
                <input
                  type="tel"
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm p-2 border"
                  value={registerForm.telefono}
                  onChange={(e) => setRegisterForm({ ...registerForm, telefono: e.target.value })}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Contraseña</label>
                <input
                  type="password"
                  required
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm p-2 border"
                  value={registerForm.password}
                  onChange={(e) => setRegisterForm({ ...registerForm, password: e.target.value })}
                />
              </div>

              <div className="pt-4 border-t border-gray-200">
                <h3 className="text-sm font-medium text-gray-900 mb-4">Datos de la Empresa</h3>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Nombre de Empresa</label>
                    <input
                      type="text"
                      required
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm p-2 border"
                      value={registerForm.nombre_empresa}
                      onChange={(e) => setRegisterForm({ ...registerForm, nombre_empresa: e.target.value })}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">RUC</label>
                    <input
                      type="text"
                      required
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm p-2 border"
                      value={registerForm.ruc}
                      onChange={(e) => setRegisterForm({ ...registerForm, ruc: e.target.value })}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">Distrito</label>
                    <input
                      type="text"
                      required
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary sm:text-sm p-2 border"
                      value={registerForm.distrito}
                      onChange={(e) => setRegisterForm({ ...registerForm, distrito: e.target.value })}
                    />
                  </div>
                </div>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50"
            >
              {isLoading ? "Creando cuenta..." : "Registrarme como Proveedor"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
