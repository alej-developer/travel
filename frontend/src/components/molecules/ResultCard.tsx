/**
 * ResultCard — Molecule
 * Unified card for Flight / Train / Accommodation results.
 * Each card shows a provider badge indicating the source platform.
 */
"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { formatPrice, formatDuration, calcDurationMinutes } from "@/lib/utils";
import { Badge } from "@/components/atoms/Badge";
import { Button } from "@/components/atoms/Button";
import { PlaneIcon, TrainIcon, HotelIcon, StarIcon, ArrowRightIcon } from "@/components/atoms/Icon";
import type { FlightResult, TrainResult, AccommodationResult } from "@/lib/api-client";
import { PROVIDER_DISPLAY_NAMES, PROVIDER_COLORS } from "@/lib/api-client";
import { format } from "date-fns";
import { es } from "date-fns/locale";

// ─── Provider Badge ─────────────────────────────────────────────────────────

function ProviderBadge({ provider }: { provider?: string }) {
  if (!provider) return null;
  const displayName = PROVIDER_DISPLAY_NAMES[provider] ?? provider;
  const colorClass = PROVIDER_COLORS[provider] ?? "bg-neutral-100 text-neutral-600";

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 text-2xs font-semibold px-2 py-0.5 rounded-pill",
        colorClass
      )}
    >
      {displayName}
    </span>
  );
}

// ─── Flight Card ────────────────────────────────────────────────────────────

interface FlightCardProps {
  data: FlightResult;
  onSelect?: (id: string) => void;
}

export function FlightCard({ data, onSelect }: FlightCardProps) {
  const duration = calcDurationMinutes(data.departure_at, data.arrival_at);
  const depTime = format(new Date(data.departure_at), "HH:mm");
  const arrTime = format(new Date(data.arrival_at), "HH:mm");

  return (
    <article className={cn(
      "bg-white rounded-2xl border border-neutral-100 p-5",
      "shadow-sm hover:shadow-card-hover transition-shadow duration-300",
      "animate-fade-in"
    )}>
      <div className="flex items-start justify-between gap-4">
        {/* Airline + Flight number */}
        <div className="flex items-center gap-2.5">
          <div className="w-10 h-10 rounded-xl bg-primary-50 flex items-center justify-center flex-shrink-0">
            <PlaneIcon size="sm" className="text-primary-500" />
          </div>
          <div>
            <p className="text-sm font-bold text-neutral-600">{data.airline}</p>
            <div className="flex items-center gap-1.5 mt-0.5">
              <p className="text-xs text-neutral-400">{data.flight_number}</p>
              <ProviderBadge provider={(data.metadata?.provider as string) ?? undefined} />
            </div>
          </div>
        </div>

        {/* Price */}
        <div className="text-right flex-shrink-0">
          <p className="text-xl font-black text-neutral-600">
            {formatPrice(data.price_cents, data.currency)}
          </p>
          <p className="text-2xs text-neutral-400">por persona</p>
        </div>
      </div>

      {/* Route */}
      <div className="mt-4 flex items-center gap-3">
        <div className="text-center">
          <p className="text-2xl font-black text-neutral-600 leading-none">{depTime}</p>
          <p className="text-sm font-semibold text-neutral-400 mt-1">{data.origin}</p>
        </div>

        <div className="flex-1 flex flex-col items-center gap-1">
          <p className="text-xs text-neutral-400">{formatDuration(duration)}</p>
          <div className="w-full flex items-center gap-1">
            <div className="h-px flex-1 bg-neutral-200" />
            <ArrowRightIcon size="xs" className="text-neutral-300" />
            <div className="h-px flex-1 bg-neutral-200" />
          </div>
          <Badge variant="neutral" size="sm">Directo</Badge>
        </div>

        <div className="text-center">
          <p className="text-2xl font-black text-neutral-600 leading-none">{arrTime}</p>
          <p className="text-sm font-semibold text-neutral-400 mt-1">{data.destination}</p>
        </div>
      </div>

      {/* CTA */}
      <Button
        variant="primary"
        size="sm"
        fullWidth
        className="mt-4"
        onClick={() => onSelect?.(data.id)}
      >
        Seleccionar vuelo
      </Button>
    </article>
  );
}

// ─── Train Card ─────────────────────────────────────────────────────────────

interface TrainCardProps {
  data: TrainResult;
  onSelect?: (id: string) => void;
}

export function TrainCard({ data, onSelect }: TrainCardProps) {
  const duration = calcDurationMinutes(data.departure_at, data.arrival_at);
  const depTime = format(new Date(data.departure_at), "HH:mm");
  const arrTime = format(new Date(data.arrival_at), "HH:mm");

  return (
    <article className={cn(
      "bg-white rounded-2xl border border-neutral-100 p-5",
      "shadow-sm hover:shadow-card-hover transition-shadow duration-300",
      "animate-fade-in"
    )}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-2.5">
          <div className="w-10 h-10 rounded-xl bg-accent-50 flex items-center justify-center flex-shrink-0">
            <TrainIcon size="sm" className="text-accent-600" />
          </div>
          <div>
            <p className="text-sm font-bold text-neutral-600">{data.operator}</p>
            <div className="flex items-center gap-1.5 mt-0.5 flex-wrap">
              <Badge variant="accent" size="sm">{data.train_number}</Badge>
              <Badge variant="default" size="sm">{data.service_class}</Badge>
              <ProviderBadge provider={(data.metadata?.provider as string) ?? undefined} />
            </div>
          </div>
        </div>

        <div className="text-right flex-shrink-0">
          <p className="text-xl font-black text-neutral-600">
            {formatPrice(data.price_cents, data.currency)}
          </p>
          <p className="text-2xs text-neutral-400">por persona</p>
        </div>
      </div>

      <div className="mt-4 flex items-center gap-3">
        <div className="text-center">
          <p className="text-2xl font-black text-neutral-600 leading-none">{depTime}</p>
          <p className="text-xs text-neutral-400 mt-1 max-w-[80px] truncate">
            {data.origin_station}
          </p>
        </div>

        <div className="flex-1 flex flex-col items-center gap-1">
          <p className="text-xs text-neutral-400">{formatDuration(duration)}</p>
          <div className="w-full flex items-center gap-1">
            <div className="h-px flex-1 bg-neutral-200" />
            <ArrowRightIcon size="xs" className="text-neutral-300" />
            <div className="h-px flex-1 bg-neutral-200" />
          </div>
        </div>

        <div className="text-center">
          <p className="text-2xl font-black text-neutral-600 leading-none">{arrTime}</p>
          <p className="text-xs text-neutral-400 mt-1 max-w-[80px] truncate">
            {data.destination_station}
          </p>
        </div>
      </div>

      <Button
        variant="secondary"
        size="sm"
        fullWidth
        className="mt-4"
        onClick={() => onSelect?.(data.id)}
      >
        Seleccionar tren
      </Button>
    </article>
  );
}

// ─── Accommodation Card ──────────────────────────────────────────────────────

interface AccommodationCardProps {
  data: AccommodationResult;
  onSelect?: (id: string) => void;
}

export function AccommodationCard({ data, onSelect }: AccommodationCardProps) {
  const nights = Math.round(
    (new Date(data.check_out).getTime() - new Date(data.check_in).getTime()) /
      (1000 * 60 * 60 * 24)
  );

  return (
    <article className={cn(
      "bg-white rounded-2xl border border-neutral-100 overflow-hidden",
      "shadow-sm hover:shadow-card-hover transition-shadow duration-300",
      "animate-fade-in"
    )}>
      {/* Image area */}
      <div className="h-40 bg-gradient-to-br from-neutral-100 to-neutral-200 flex items-center justify-center">
        <HotelIcon size="xl" className="text-neutral-300" />
      </div>

      <div className="p-4">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-bold text-neutral-600 truncate">{data.name}</h3>
            <div className="flex items-center gap-1.5 mt-0.5">
              <p className="text-xs text-neutral-400 truncate">{data.city}, {data.country_code}</p>
              <ProviderBadge provider={(data.metadata?.provider as string) ?? undefined} />
            </div>
          </div>

          {data.star_rating && (
            <div className="flex items-center gap-1 flex-shrink-0">
              <StarIcon size="xs" className="text-amber-400 fill-amber-400 stroke-amber-400" />
              <span className="text-xs font-semibold text-neutral-500">{data.star_rating}</span>
            </div>
          )}
        </div>

        <div className="mt-3 flex items-baseline justify-between">
          <div>
            <span className="text-xl font-black text-neutral-600">
              {formatPrice(data.price_per_night_cents, data.currency)}
            </span>
            <span className="text-xs text-neutral-400 ml-1">/ noche</span>
          </div>
          <Badge variant="neutral" size="sm">{nights} noches</Badge>
        </div>

        <Badge variant="default" size="sm" className="mt-2">{data.room_type}</Badge>

        <Button
          variant="primary"
          size="sm"
          fullWidth
          className="mt-3"
          onClick={() => onSelect?.(data.id)}
        >
          Ver disponibilidad
        </Button>
      </div>
    </article>
  );
}
