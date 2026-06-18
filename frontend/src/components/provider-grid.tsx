import { Search, Sparkles } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { ProviderCard } from "./provider-card";
import type { ProveedorRecomendado } from "../types";

type ProviderGridProps = {
  principales: ProveedorRecomendado[];
  otras: ProveedorRecomendado[];
  isPending: boolean;
  onSelect: (provider: ProveedorRecomendado) => void;
  loadingDetail: boolean;
  onNewSearch: () => void;
};

function ProviderCardSkeleton() {
  return (
    <Card className="flex flex-col gap-6 py-6">
      <CardHeader className="gap-3 pb-0">
        <div className="flex items-center gap-2">
          <Skeleton className="h-3 w-24" />
          <Skeleton className="h-3 w-16" />
        </div>
        <Skeleton className="h-5 w-3/4" />
        <Skeleton className="h-4 w-full" />
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <div className="flex gap-2">
          <Skeleton className="h-5 w-12 rounded-full" />
          <Skeleton className="h-5 w-16 rounded-full" />
        </div>
        <div className="flex gap-1.5">
          <Skeleton className="h-5 w-20 rounded-full" />
          <Skeleton className="h-5 w-24 rounded-full" />
          <Skeleton className="h-5 w-16 rounded-full" />
        </div>
      </CardContent>
      <div className="flex items-center justify-between px-6">
        <div className="flex flex-col gap-1">
          <Skeleton className="h-7 w-24" />
          <Skeleton className="h-3 w-20" />
        </div>
        <Skeleton className="h-8 w-24 rounded-md" />
      </div>
    </Card>
  );
}

export function ProviderGrid({
  principales,
  otras,
  isPending,
  onSelect,
  loadingDetail,
  onNewSearch,
}: ProviderGridProps) {
  // Loading state: show skeleton cards
  if (isPending) {
    return (
      <section className="flex flex-col gap-10">
        <div className="flex flex-col gap-5">
          <div className="flex items-center gap-2.5">
            <Sparkles className="h-4 w-4 text-amber-500" />
            <h3 className="text-lg font-black text-[var(--teal-dark)]">
              Buscando opciones…
            </h3>
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <ProviderCardSkeleton key={i} />
            ))}
          </div>
        </div>
      </section>
    );
  }

  // Empty state
  if (principales.length === 0 && otras.length === 0) {
    return (
      <div className="flex flex-col items-center gap-5 rounded-2xl border border-dashed border-[var(--line)] bg-white px-6 py-16 text-center">
        <Search className="h-10 w-10 text-muted-foreground/40" />
        <p className="text-lg font-bold text-muted-foreground">
          No encontramos opciones disponibles para esta búsqueda.
        </p>
        <Button
          onClick={onNewSearch}
          className="bg-[var(--teal)] hover:bg-[var(--teal-dark)] text-white"
        >
          Intentar otra búsqueda
        </Button>
      </div>
    );
  }

  return (
    <section className="flex flex-col gap-10">
      {/* Principales */}
      {principales.length > 0 && (
        <div className="flex flex-col gap-5">
          <div className="flex items-center gap-2.5">
            <Sparkles className="h-4 w-4 text-amber-500" />
            <h3 className="text-lg font-black text-[var(--teal-dark)]">
              Coincidencias ideales
            </h3>
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {principales.map((provider) => (
              <ProviderCard
                key={provider.proveedor_id}
                provider={provider}
                onSelect={() => onSelect(provider)}
                disabled={loadingDetail}
                featured
              />
            ))}
          </div>
        </div>
      )}

      {/* Otras opciones */}
      {otras.length > 0 && (
        <div className="flex flex-col gap-5">
          <h3 className="text-lg font-black text-muted-foreground">
            Otras alternativas para ti
          </h3>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {otras.map((provider) => (
              <ProviderCard
                key={provider.proveedor_id}
                provider={provider}
                onSelect={() => onSelect(provider)}
                disabled={loadingDetail}
              />
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
