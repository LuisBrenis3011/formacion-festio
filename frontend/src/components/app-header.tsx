import { Sparkles } from "lucide-react";

type AppHeaderProps = {
  onLogoClick: () => void;
  subtitle?: string;
};

export function AppHeader({ onLogoClick, subtitle }: AppHeaderProps) {
  return (
    <header className="app-header">
      <button className="brand-button" type="button" onClick={onLogoClick}>
        <span className="brand-icon">
          <Sparkles size={18} />
        </span>
        <div className="brand-text">
          <span>Festio</span>
          {subtitle && <small>{subtitle}</small>}
        </div>
      </button>
    </header>
  );
}
