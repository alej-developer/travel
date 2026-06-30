/**
 * ResultsGrid — Organism
 *
 * Responsive CSS Grid (auto-fill cards) with:
 * - Skeleton loading state (8 cards)
 * - Error state
 * - Empty state
 * - React Query integration (useQuery)
 * - Filter bar (sort by price / duration)
 * - Dynamic card rendering by transport type
 */
"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { cn } from "@/lib/utils";
import { CardSkeleton } from "@/components/atoms/Skeleton";
import { Badge } from "@/components/atoms/Badge";
import { Button } from "@/components/atoms/Button";
import { FilterIcon, SpinnerIcon } from "@/components/atoms/Icon";
import { FlightCard, TrainCard, AccommodationCard } from "@/components/molecules/ResultCard";
import { travelApi, queryKeys, type SearchParams, type TransportType } from "@/lib/api-client";

// ─── Types ──────────────────────────────────────────────────────────────────

type SortKey = "price_asc" | "price_desc" | "duration_asc";

interface ResultsGridProps {
  params: SearchParams | null;
  className?: string;
}

const SORT_OPTIONS: { key: SortKey; label: string }[] = [
  { key: "price_asc",    label: "Precio ↑" },
  { key: "price_desc",   label: "Precio ↓" },
  { key: "duration_asc", label: "Duración" },
];

// ─── Empty State ─────────────────────────────────────────────────────────────

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <div className="w-20 h-20 rounded-full bg-neutral-100 flex items-center justify-center mb-4">
        <FilterIcon size="lg" className="text-neutral-300" />
      </div>
      <h3 className="text-lg font-bold text-neutral-500">No encontramos resultados</h3>
      <p className="text-sm text-neutral-400 mt-1 max-w-xs">
        Prueba a cambiar las fechas, el origen o el destino.
      </p>
    </div>
  );
}

// ─── Error State ─────────────────────────────────────────────────────────────

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <div className="w-20 h-20 rounded-full bg-primary-50 flex items-center justify-center mb-4">
        <span className="text-3xl">⚠️</span>
      </div>
      <h3 className="text-lg font-bold text-neutral-500">Error al cargar resultados</h3>
      <p className="text-sm text-neutral-400 mt-1 mb-4 max-w-xs">{message}</p>
      <Button variant="secondary" size="sm" onClick={onRetry}>
        Reintentar
      </Button>
    </div>
  );
}

// ─── Initial State ─────────────────────────────────────────────────────────

function InitialState() {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <div className="w-20 h-20 rounded-full bg-primary-50 flex items-center justify-center mb-4">
        <SpinnerIcon size="xl" className="text-primary-300 animate-spin-slow" />
      </div>
      <h3 className="text-lg font-bold text-neutral-400">
        Busca tu próximo viaje
      </h3>
      <p className="text-sm text-neutral-300 mt-1">
        Los resultados aparecerán aquí en segundos
      </p>
    </div>
  );
}

// ─── Skeleton Grid ───────────────────────────────────────────────────────────

function SkeletonGrid() {
  return (
    <div className="grid grid-cols-auto-fill-card gap-4">
      {Array.from({ length: 8 }).map((_, i) => (
        <CardSkeleton key={i} />
      ))}
    </div>
  );
}

// ─── Main Organism ───────────────────────────────────────────────────────────

export function ResultsGrid({ params, className }: ResultsGridProps) {
  const [sortKey, setSortKey] = useState<SortKey>("price_asc");
  const transport: TransportType = params?.type ?? "flight";

  // Decide which query to run based on transport type
  const flightQuery = useQuery({
    queryKey: queryKeys.flights(params ?? undefined),
    queryFn: () => travelApi.getFlights(params ?? undefined),
    enabled: !!params && transport === "flight",
    staleTime: 60_000,
    retry: 2,
  });

  const trainQuery = useQuery({
    queryKey: queryKeys.trains(params ?? undefined),
    queryFn: () => travelApi.getTrains(params ?? undefined),
    enabled: !!params && transport === "train",
    staleTime: 60_000,
    retry: 2,
  });

  const accomQuery = useQuery({
    queryKey: queryKeys.accommodations(params ?? undefined),
    queryFn: () => travelApi.getAccommodations(params ?? undefined),
    enabled: !!params && transport === "accommodation",
    staleTime: 60_000,
    retry: 2,
  });

  const activeQuery =
    transport === "flight"
      ? flightQuery
      : transport === "train"
      ? trainQuery
      : accomQuery;

  const { isLoading, isError, error, data, refetch } = activeQuery;

  // ── Sort items client-side ──────────────────────────────────────────────
  const items = React.useMemo(() => {
    if (!data?.items) return [];
    const sorted = [...data.items];

    if (sortKey === "price_asc") {
      sorted.sort((a, b) => {
        const pa = "price_cents" in a ? a.price_cents : a.price_per_night_cents;
        const pb = "price_cents" in b ? b.price_cents : b.price_per_night_cents;
        return pa - pb;
      });
    } else if (sortKey === "price_desc") {
      sorted.sort((a, b) => {
        const pa = "price_cents" in a ? a.price_cents : a.price_per_night_cents;
        const pb = "price_cents" in b ? b.price_cents : b.price_per_night_cents;
        return pb - pa;
      });
    }

    return sorted;
  }, [data, sortKey]);

  // ── Render ──────────────────────────────────────────────────────────────
  return (
    <section className={cn("py-8 px-4 sm:px-6 max-w-7xl mx-auto", className)}>
      {/* Header */}
      {params && (
        <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold text-neutral-600">
              {isLoading
                ? "Buscando..."
                : data
                ? `${data.total} resultados`
                : "Resultados"}
            </h2>
            {isLoading && (
              <Badge variant="primary" dot>
                Scraping en progreso
              </Badge>
            )}
          </div>

          {/* Sort */}
          {!isLoading && items.length > 0 && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-neutral-400">Ordenar por:</span>
              <div className="flex items-center gap-1 bg-neutral-100 rounded-xl p-1">
                {SORT_OPTIONS.map((opt) => (
                  <button
                    key={opt.key}
                    type="button"
                    onClick={() => setSortKey(opt.key)}
                    className={cn(
                      "px-3 py-1.5 rounded-lg text-sm font-medium",
                      "transition-all duration-150",
                      sortKey === opt.key
                        ? "bg-white text-neutral-600 shadow-xs"
                        : "text-neutral-400 hover:text-neutral-600"
                    )}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Content states */}
      {!params && <InitialState />}
      {params && isLoading && <SkeletonGrid />}
      {params && isError && (
        <ErrorState
          message={error instanceof Error ? error.message : "Error desconocido"}
          onRetry={refetch}
        />
      )}
      {params && !isLoading && !isError && items.length === 0 && <EmptyState />}

      {/* Results */}
      {!isLoading && items.length > 0 && (
        <div className="grid grid-cols-auto-fill-card gap-4">
          {transport === "flight" &&
            items.map((item) => (
              <FlightCard
                key={item.id}
                data={item as Parameters<typeof FlightCard>[0]["data"]}
              />
            ))}
          {transport === "train" &&
            items.map((item) => (
              <TrainCard
                key={item.id}
                data={item as Parameters<typeof TrainCard>[0]["data"]}
              />
            ))}
          {transport === "accommodation" &&
            items.map((item) => (
              <AccommodationCard
                key={item.id}
                data={item as Parameters<typeof AccommodationCard>[0]["data"]}
              />
            ))}
        </div>
      )}

      {/* Pagination hint */}
      {data?.has_more && !isLoading && (
        <div className="mt-8 flex justify-center">
          <Button variant="secondary" size="md">
            Cargar más resultados
          </Button>
        </div>
      )}
    </section>
  );
}

export default ResultsGrid;
