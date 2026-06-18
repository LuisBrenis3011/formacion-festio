type PaymentMethodSelectProps = {
  value: string;
  onChange: (value: string) => void;
};

export function PaymentMethodSelect({ value, onChange }: PaymentMethodSelectProps) {
  return (
    <label className="wide-field">
      <span>Método de pago</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="TARJETA">Tarjeta</option>
        <option value="YAPE">Yape</option>
        <option value="PLIN">Plin</option>
        <option value="EFECTIVO">Efectivo</option>
      </select>
    </label>
  );
}
