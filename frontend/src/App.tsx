import { Routes, Route, Navigate } from "react-router-dom";
import { ClienteApp } from "./ClienteApp";
import { AuthModal } from "./components/AuthModal";
import { ProtectedRoute } from "./components/ProtectedRoute";
import type { RolUsuario } from "./types";

// Pantallas B2B
import { ProveedorLayout } from "./screens/proveedor/ProveedorLayout";
import { DashboardScreen } from "./screens/proveedor/DashboardScreen";
import { InventarioScreen } from "./screens/proveedor/InventarioScreen";
import { PaquetesScreen } from "./screens/proveedor/PaquetesScreen";
import { PerfilScreen } from "./screens/proveedor/PerfilScreen";

export default function App() {
  return (
    <>
      {/* Modal de auth global — se renderiza siempre, visible solo cuando authModalMode != null */}
      <AuthModal />

      <Routes>
        {/* Chat público — accesible sin login */}
        <Route path="/" element={<ClienteApp />} />
        <Route path="/chat" element={<ClienteApp />} />

        {/* Rutas proveedor — Panel B2B protegidas por rol */}
        <Route path="/proveedor" element={<ProtectedRoute rol="PROVEEDOR" />}>
          <Route element={<ProveedorLayout />}>
            <Route path="dashboard" element={<DashboardScreen />} />
            <Route path="inventario" element={<InventarioScreen />} />
            <Route path="paquetes" element={<PaquetesScreen />} />
            <Route path="perfil" element={<PerfilScreen />} />
            {/* Redirección por defecto */}
            <Route path="" element={<Navigate to="dashboard" replace />} />
          </Route>
        </Route>

        {/* 404 genérico → al chat */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}
