import { money } from "@/lib/format";

type SummaryLineProps = {
  label: string;
  value: number;
  strong?: boolean;
};

export function SummaryLine({ label, value, strong = false }: SummaryLineProps) {
  return (
    <div className={strong ? "summary-line summary-total" : "summary-line"}>
      <span>{label}</span>
      <strong>{money.format(value)}</strong>
    </div>
  );
}
