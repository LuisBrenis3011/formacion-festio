import type { EventDraft, LoginDraft, RegisterDraft } from "../types";

export type SuggestionCard = {
  icon: string;
  title: string;
  description: string;
  query: string;
};

export const SUGGESTION_CARDS: SuggestionCard[] = [
  {
    icon: "🎪",
    title: "Show infantil",
    description: "Show de Spiderman para 30 niños",
    query: "Quiero un show infantil de Spiderman para 30 niños",
  },
  {
    icon: "🎉",
    title: "Hora loca",
    description: "Hora loca para 50 personas",
    query: "Necesito hora loca para una fiesta de 50 personas",
  },
  {
    icon: "🎂",
    title: "Cumpleaños",
    description: "Animación de princesas para cumpleaños",
    query: "Quiero animación de princesas para un cumpleaños infantil",
  },
  {
    icon: "💼",
    title: "Corporativo",
    description: "Show de magia para evento corporativo",
    query: "Necesito un show de magia para evento corporativo",
  },
  {
    icon: "🦸",
    title: "Superhéroes",
    description: "Fiesta temática de superhéroes",
    query: "Quiero una fiesta temática de superhéroes",
  },
  {
    icon: "👑",
    title: "Quinceañera",
    description: "Decoración y toldo para quinceañera",
    query: "Necesito decoración y toldo para una quinceañera",
  },
];

export const SUGGESTIONS = SUGGESTION_CARDS.map((c) => c.query);

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
