import { PartyPopper } from "lucide-react";

type AppHeaderProps = {
  onLogoClick: () => void;
};

export function AppHeader({ onLogoClick }: AppHeaderProps) {
  return (
    <header className="app-header">
      <button className="brand-button" type="button" onClick={onLogoClick}>
        <span className="brand-icon">
          <PartyPopper size={20} />
        </span>
        <span>Festio</span>
      </button>
    </header>
  );
}
