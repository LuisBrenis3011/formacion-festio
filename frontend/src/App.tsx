import { Routes, Route, Navigate } from "react-router-dom";
import { ClienteApp } from "./ClienteApp";
import { ProtectedRoute } from "./components/ProtectedRoute";

// Pantallas B2B
import { LoginScreen } from "./screens/LoginScreen";
import { ProveedorLayout } from "./screens/proveedor/ProveedorLayout";
import { DashboardScreen } from "./screens/proveedor/DashboardScreen";
import { InventarioScreen } from "./screens/proveedor/InventarioScreen";
import { PaquetesScreen } from "./screens/proveedor/PaquetesScreen";
import { PerfilScreen } from "./screens/proveedor/PerfilScreen";

export default function App() {
  return (
    <Routes>
      {/* Rutas públicas / Cliente */}
      <Route path="/login" element={<LoginScreen />} />
      
      {/* Ruta cliente — el chat se mantiene igual */}
      <Route path="/" element={<ClienteApp />} />
      <Route path="/chat" element={<ProtectedRoute rol="CLIENTE" />}>
        <Route index element={<ClienteApp />} />
      </Route>

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

      {/* 404 genérico */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
