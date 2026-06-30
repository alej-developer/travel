/**
 * SearchHero — Organism
 *
 * Full-width search bar with:
 * - TransportToggle (flight / train / accommodation)
 * - Origin + Destination text inputs
 * - DatePickerField (departure + return)
 * - PassengerSelector
 * - Search CTA button
 *
 * State is managed by hooks (useDateRange, usePassengers).
 * On submit, calls onSearch prop with typed SearchParams.
 */
"use client";

import React, { useState, useId } from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/atoms/Button";
import { Input } from "@/components/atoms/Input";
import { SearchIcon, LocationIcon, ArrowRightIcon } from "@/components/atoms/Icon";
import { TransportToggle, type TransportType } from "@/components/molecules/TransportToggle";
import { DatePickerField } from "@/components/molecules/DatePickerField";
import { PassengerSelector } from "@/components/molecules/PassengerSelector";
import { useDateRange } from "@/hooks/useDateRange";
import { usePassengers } from "@/hooks/usePassengers";
import type { SearchParams } from "@/lib/api-client";

interface SearchHeroProps {
  onSearch: (params: SearchParams) => void;
  isLoading?: boolean;
  className?: string;
}

export function SearchHero({ onSearch, isLoading = false, className }: SearchHeroProps) {
  const id = useId();
  const [transport, setTransport] = useState<TransportType>("flight");
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});

  const dateRange = useDateRange();
  const passengers = usePassengers();

  const isAccommodation = transport === "accommodation";

  // ── Validation ──────────────────────────────────────────────────────────
  function validate(): boolean {
    const newErrors: Record<string, string> = {};

    if (!origin.trim())
      newErrors.origin = "El origen es obligatorio";
    if (!destination.trim())
      newErrors.destination = "El destino es obligatorio";
    if (!dateRange.range.startDate)
      newErrors.startDate = "Selecciona una fecha de salida";
    if (!isAccommodation && !dateRange.range.endDate)
      newErrors.endDate = "Selecciona una fecha de regreso";

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }

  // ── Submit ───────────────────────────────────────────────────────────────
  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!validate()) return;

    const params: SearchParams = {
      origin: origin.trim().toUpperCase(),
      destination: destination.trim().toUpperCase(),
      date_from: dateRange.range.startDate?.toISOString().split("T")[0],
      date_to: dateRange.range.endDate?.toISOString().split("T")[0],
      passengers: passengers.total,
      type: transport,
    };

    onSearch(params);
  }

  // ── Swap origin/destination ──────────────────────────────────────────────
  function handleSwap() {
    const tmp = origin;
    setOrigin(destination);
    setDestination(tmp);
  }

  return (
    <section
      className={cn(
        "w-full bg-gradient-to-br from-primary-500 via-primary-600 to-primary-700",
        "py-16 px-4 sm:px-6",
        className
      )}
    >
      {/* Hero headline */}
      <div className="max-w-5xl mx-auto text-center mb-10">
        <h1 className="text-4xl sm:text-5xl font-black text-white tracking-tightest text-balance leading-tight">
          Tu próximo viaje,<br />
          <span className="text-primary-100">al mejor precio</span>
        </h1>
        <p className="mt-3 text-primary-200 text-lg font-medium">
          Compara vuelos, trenes y alojamientos en tiempo real
        </p>
      </div>

      {/* Search card */}
      <form
        onSubmit={handleSubmit}
        noValidate
        className="max-w-5xl mx-auto"
        aria-label="Buscador de viajes"
      >
        <div className="bg-white rounded-3xl shadow-2xl overflow-visible">
          {/* Transport toggle */}
          <div className="px-6 pt-5 pb-0">
            <TransportToggle value={transport} onChange={setTransport} />
          </div>

          {/* Search fields */}
          <div className="p-3 sm:p-4">
            <div className={cn(
              "grid gap-0 bg-white rounded-2xl border border-neutral-200",
              "shadow-search divide-y sm:divide-y-0 sm:divide-x divide-neutral-100",
              "sm:grid-cols-[1fr_auto_1fr_1px_1fr_1px_1fr_1px_auto_auto]",
              "md:grid-cols-[1fr_auto_1fr_1px_1fr_1px_1fr_1px_auto_auto]"
            )}>

              {/* ── Origin ────────────────────────────────────────────── */}
              <div className="relative group">
                <Input
                  label="Origen"
                  placeholder={isAccommodation ? "Ciudad" : "Aeropuerto o ciudad"}
                  value={origin}
                  onChange={(e) => {
                    setOrigin(e.target.value);
                    if (errors.origin) setErrors((p) => ({ ...p, origin: "" }));
                  }}
                  error={errors.origin}
                  leftAdornment={<LocationIcon size="sm" />}
                  className="border-0 shadow-none rounded-none focus:ring-0 bg-transparent h-auto py-3 pl-10"
                  id={`${id}-origin`}
                />
              </div>

              {/* ── Swap button ──────────────────────────────────────── */}
              {!isAccommodation && (
                <div className="flex items-center justify-center px-1 sm:px-0">
                  <button
                    type="button"
                    onClick={handleSwap}
                    aria-label="Intercambiar origen y destino"
                    className={cn(
                      "w-8 h-8 flex items-center justify-center",
                      "rounded-full border-2 border-neutral-200 bg-white",
                      "text-neutral-400 hover:text-neutral-600 hover:border-neutral-400",
                      "transition-all duration-200 z-10",
                      "hover:rotate-180 rotate-0"
                    )}
                    style={{ transition: "transform 0.3s ease, border-color 0.15s, color 0.15s" }}
                  >
                    <ArrowRightIcon size="xs" />
                  </button>
                </div>
              )}

              {/* ── Destination ───────────────────────────────────────── */}
              <div className="relative group">
                <Input
                  label="Destino"
                  placeholder={isAccommodation ? "Ciudad o dirección" : "Aeropuerto o ciudad"}
                  value={destination}
                  onChange={(e) => {
                    setDestination(e.target.value);
                    if (errors.destination) setErrors((p) => ({ ...p, destination: "" }));
                  }}
                  error={errors.destination}
                  leftAdornment={<LocationIcon size="sm" />}
                  className="border-0 shadow-none rounded-none focus:ring-0 bg-transparent h-auto py-3 pl-10"
                  id={`${id}-destination`}
                />
              </div>

              {/* Divider */}
              <div className="hidden sm:block w-px bg-neutral-100 self-stretch" />

              {/* ── Departure date ─────────────────────────────────────── */}
              <DatePickerField
                label={isAccommodation ? "Check-in" : "Salida"}
                value={dateRange.range.startDate}
                onChange={dateRange.setStartDate}
                placeholder="Añadir fecha"
                highlightRange={{
                  start: dateRange.range.startDate,
                  end: dateRange.range.endDate,
                }}
                className="min-w-[140px]"
              />

              {/* Divider */}
              <div className="hidden sm:block w-px bg-neutral-100 self-stretch" />

              {/* ── Return date ────────────────────────────────────────── */}
              <DatePickerField
                label={isAccommodation ? "Check-out" : "Regreso"}
                value={dateRange.range.endDate}
                onChange={dateRange.setEndDate}
                placeholder="Añadir fecha"
                minDate={dateRange.range.startDate ?? new Date()}
                highlightRange={{
                  start: dateRange.range.startDate,
                  end: dateRange.range.endDate,
                }}
                className="min-w-[140px]"
              />

              {/* Divider */}
              <div className="hidden sm:block w-px bg-neutral-100 self-stretch" />

              {/* ── Passengers ─────────────────────────────────────────── */}
              <PassengerSelector
                counts={passengers.counts}
                total={passengers.total}
                label={passengers.label}
                onIncrement={passengers.increment}
                onDecrement={passengers.decrement}
                canIncrement={passengers.canIncrement}
                canDecrement={passengers.canDecrement}
                className="min-w-[150px]"
              />

              {/* ── Search CTA ─────────────────────────────────────────── */}
              <div className="flex items-center p-2">
                <Button
                  type="submit"
                  variant="primary"
                  size="lg"
                  loading={isLoading}
                  leftIcon={<SearchIcon size="sm" />}
                  className="rounded-2xl h-14 px-6 min-w-[140px]"
                  aria-label="Buscar viajes"
                >
                  Buscar
                </Button>
              </div>
            </div>

            {/* Error summary */}
            {Object.keys(errors).length > 0 && (
              <p className="mt-2 text-sm text-white/80 pl-2">
                Por favor completa todos los campos requeridos.
              </p>
            )}
          </div>
        </div>

        {/* Quick links */}
        <div className="mt-4 flex flex-wrap gap-2 justify-center">
          {["Madrid → Barcelona", "Valencia → Sevilla", "Bilbao → Málaga"].map((route) => {
            const [from, to] = route.split(" → ");
            return (
              <button
                key={route}
                type="button"
                onClick={() => { setOrigin(from); setDestination(to); }}
                className={cn(
                  "text-sm text-white/70 hover:text-white",
                  "bg-white/10 hover:bg-white/20 backdrop-blur-sm",
                  "px-3 py-1.5 rounded-pill",
                  "transition-all duration-150 border border-white/10"
                )}
              >
                {route}
              </button>
            );
          })}
        </div>
      </form>
    </section>
  );
}

export default SearchHero;
