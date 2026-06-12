import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import type { RolUsuario } from "../types";

type ProtectedRouteProps = {
  rol?: RolUsuario;
};

export function ProtectedRoute({ rol }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, user } = useAuth();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (rol && user?.rol !== rol) {
    // Si el rol no coincide, redirigimos a donde corresponda
    if (user?.rol === "PROVEEDOR") return <Navigate to="/proveedor/dashboard" replace />;
    if (user?.rol === "CLIENTE") return <Navigate to="/chat" replace />;
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}
