import { createContext, useState, useEffect, type ReactNode } from "react";
import { authService, type RegistroProveedorDraft } from "../services/authService";
import type { AuthUser, LoginDraft, TokenResponse } from "../types";

type AuthContextType = {
  user: AuthUser | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (datos: LoginDraft) => Promise<void>;
  registroProveedor: (datos: RegistroProveedorDraft) => Promise<void>;
  logout: () => void;
};

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem("festio_token"));
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadUser() {
      if (!token) {
        setIsLoading(false);
        return;
      }
      try {
        const userData = await authService.getMe();
        setUser(userData);
      } catch (error) {
        console.error("Token inválido o expirado", error);
        logout();
      } finally {
        setIsLoading(false);
      }
    }
    loadUser();
  }, [token]);

  const handleAuthSuccess = async (data: TokenResponse) => {
    localStorage.setItem("festio_token", data.access_token);
    setToken(data.access_token);
    // user se cargará en el useEffect, pero podemos setearlo parcialmente para que sea más rápido
    setUser({
      id: data.usuario_id,
      nombre: data.nombre,
      apellido: "",
      email: "",
      rol: data.rol,
      estado: "ACTIVO",
      proveedor_id: data.proveedor_id,
    });
  };

  const login = async (datos: LoginDraft) => {
    const data = await authService.login(datos);
    await handleAuthSuccess(data);
  };

  const registroProveedor = async (datos: RegistroProveedorDraft) => {
    const data = await authService.registroProveedor(datos);
    await handleAuthSuccess(data);
  };

  const logout = () => {
    localStorage.removeItem("festio_token");
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user,
        isLoading,
        login,
        registroProveedor,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
