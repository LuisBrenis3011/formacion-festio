import { Sparkles, LogOut, LayoutDashboard } from "lucide-react";
import { useAuth } from "../hooks/useAuth";
import { useNavigate } from "react-router-dom";

type AppHeaderProps = {
  onLogoClick: () => void;
  subtitle?: string;
};

export function AppHeader({ onLogoClick, subtitle }: AppHeaderProps) {
  const { isAuthenticated, user, logout, openAuthModal } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <header className="app-header">
      <button className="brand-button" type="button" onClick={onLogoClick}>
        <span className="brand-icon">
          <Sparkles size={18} />
        </span>
        <div className="brand-text">
          <span>Festio</span>
          {subtitle ? <small>{subtitle}</small> : null}
        </div>
      </button>

      <nav className="header-actions">
        {isAuthenticated ? (
          <div className="header-user-info">
            {user?.rol === "PROVEEDOR" ? (
              <button
                id="header-go-panel"
                className="header-btn header-btn-outline"
                type="button"
                onClick={() => navigate("/proveedor/dashboard")}
              >
                <LayoutDashboard size={16} />
                Mi Panel
              </button>
            ) : null}
            <span className="header-user-name">
              Hola, <strong>{user?.nombre}</strong>
            </span>
            <button
              id="header-logout"
              className="header-btn header-btn-ghost"
              type="button"
              onClick={handleLogout}
            >
              <LogOut size={16} />
            </button>
          </div>
        ) : (
          <div className="header-auth-buttons">
            <button
              id="header-login"
              className="header-btn header-btn-ghost"
              type="button"
              onClick={() => openAuthModal("login")}
            >
              Iniciar sesión
            </button>
            <button
              id="header-register"
              className="header-btn header-btn-primary"
              type="button"
              onClick={() => openAuthModal("register")}
            >
              Registrarse
            </button>
          </div>
        )}
      </nav>
    </header>
  );
}
