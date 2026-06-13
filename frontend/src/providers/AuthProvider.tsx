import { createContext, useState, useEffect, useCallback, type ReactNode } from "react";
import { authService, type RegistroProveedorDraft } from "../services/authService";
import type { AuthUser, AuthModalMode, LoginDraft, RegistroClienteDraft, TokenResponse } from "../types";

type AuthContextType = {
  user: AuthUser | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (datos: LoginDraft) => Promise<void>;
  registroProveedor: (datos: RegistroProveedorDraft) => Promise<void>;
  registroCliente: (datos: RegistroClienteDraft) => Promise<void>;
  logout: () => void;
  // Modal de auth
  authModalMode: AuthModalMode;
  openAuthModal: (mode: "login" | "register") => void;
  closeAuthModal: () => void;
};

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem("festio_token"));
  const [isLoading, setIsLoading] = useState(true);
  const [authModalMode, setAuthModalMode] = useState<AuthModalMode>(null);

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

  const registroCliente = async (datos: RegistroClienteDraft) => {
    const data = await authService.registroCliente(datos);
    await handleAuthSuccess(data);
  };

  const logout = () => {
    localStorage.removeItem("festio_token");
    setToken(null);
    setUser(null);
  };

  const openAuthModal = useCallback((mode: "login" | "register") => {
    setAuthModalMode(mode);
  }, []);

  const closeAuthModal = useCallback(() => {
    setAuthModalMode(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user,
        isLoading,
        login,
        registroProveedor,
        registroCliente,
        logout,
        authModalMode,
        openAuthModal,
        closeAuthModal,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
