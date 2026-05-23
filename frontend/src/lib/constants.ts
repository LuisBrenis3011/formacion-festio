import type { EventDraft, LoginDraft, RegisterDraft } from "../types";

export const SUGGESTIONS = [
  "Show infantil de Spiderman para 30 niños",
  "Hora loca para una fiesta de 50 personas",
  "DJ y luces para cumpleaños este sábado",
  "Sillas y toldo para evento familiar",
];

export const EVENT_INITIAL: EventDraft = {
  fecha: "",
  horaInicio: "",
  direccion: "",
  invitados: "",
};

export const REGISTER_INITIAL: RegisterDraft = {
  nombre: "",
  apellido: "",
  email: "",
  telefono: "",
  password: "",
  metodoPago: "TARJETA",
};

export const LOGIN_INITIAL: LoginDraft = {
  email: "",
  password: "",
  metodoPago: "TARJETA",
};
