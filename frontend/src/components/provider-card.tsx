import { MapPin, Sparkles, Star } from "lucide-react";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { money } from "@/lib/format";
import type { ProveedorRecomendado } from "../types";


type ProviderCardProps = {
  provider: ProveedorRecomendado;
  onSelect: () => void;
  disabled?: boolean;
  featured?: boolean;
};

export function ProviderCard({
  provider,
  onSelect,
  disabled = false,
  featured = false,
}: ProviderCardProps) {
  const rating = provider.calificacion_promedio;
  const items = provider.paquete.incluye;

  return (
    <Card
      className={cn(
        "group relative cursor-pointer transition-all duration-200 hover:-translate-y-1 hover:shadow-lg",
        featured && "border-2 border-[var(--teal)] bg-gradient-to-br from-white to-teal-50/60",
        !featured && "hover:border-[var(--teal)]/40",
        disabled && "pointer-events-none opacity-55",
      )}
      onClick={onSelect}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onSelect();
        }
      }}
    >
      {/* Featured ribbon */}
      {featured && (
        <div className="absolute -top-px -right-px rounded-bl-lg rounded-tr-xl bg-amber-500 px-3 py-1">
          <Sparkles className="h-3.5 w-3.5 text-white" />
        </div>
      )}

      <CardHeader className="gap-3 pb-0">
        {/* Provider name + district */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold uppercase tracking-wide text-[var(--teal-dark)]">
            {provider.nombre_empresa}
          </span>
          {provider.distrito && (
            <span className="flex items-center gap-1 text-xs text-muted-foreground">
              <MapPin className="h-3 w-3" />
              {provider.distrito}
            </span>
          )}
        </div>

        {/* Package name */}
        <CardTitle className="text-lg leading-tight">
          {provider.paquete.nombre}
        </CardTitle>

        {/* Description */}
        {provider.paquete.descripcion && (
          <p className="text-sm leading-relaxed text-muted-foreground line-clamp-2">
            {provider.paquete.descripcion}
          </p>
        )}
      </CardHeader>

      <CardContent className="flex flex-col gap-3">
        {/* Rating + Availability badges */}
        <div className="flex flex-wrap items-center gap-2">
          {rating != null && rating > 0 && (
            <Badge variant="secondary" className="gap-1">
              <Star className="h-3 w-3 fill-amber-400 text-amber-400" />
              {rating.toFixed(1)}
            </Badge>
          )}
          <Badge variant={provider.disponible ? "success" : "warning"}>
            {provider.disponible ? "Disponible" : "Consultar"}
          </Badge>
        </div>

        {/* Included items (first 3) */}
        {items.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {items.slice(0, 3).map((item) => (
              <span
                key={item.servicio_producto_id}
                className="inline-flex items-center gap-1 rounded-full bg-teal-50 px-2 py-0.5 text-xs font-medium text-teal-800"
              >
                {item.nombre}
                <span className="font-bold text-teal-600">×{item.cantidad}</span>
              </span>
            ))}
            {items.length > 3 && (
              <span className="inline-flex items-center rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-500">
                +{items.length - 3} más
              </span>
            )}
          </div>
        )}
      </CardContent>

      <CardFooter className="flex items-center justify-between pt-0">
        {/* Price */}
        <div className="flex flex-col">
          <span className="text-2xl font-black text-[var(--teal-dark)]">
            {money.format(provider.paquete.precio_base)}
          </span>
          <span className="text-xs text-muted-foreground">
            Adelanto {money.format(provider.adelanto_20)}
          </span>
        </div>

        {/* CTA */}
        <Button
          size="sm"
          className="bg-[var(--teal)] hover:bg-[var(--teal-dark)] text-white"
          tabIndex={-1}
        >
          Ver paquete
        </Button>
      </CardFooter>
    </Card>
  );
}
