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
        "relative w-full bg-gradient-to-br from-primary-500 via-primary-600 to-primary-700",
        "pt-[10rem] pb-[7rem] px-4 sm:px-6",
        className
      )}
    >
      <div className="flex flex-col gap-6 w-full max-w-5xl mx-auto">
        {/* Hero headline */}
        <div className="text-center">
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black text-white tracking-tightest text-balance leading-tight drop-shadow-sm">
            Tu próximo viaje,<br />
            <span className="text-primary-100">al mejor precio</span>
          </h1>
          <p className="mt-4 text-primary-100 text-lg sm:text-xl font-medium drop-shadow-sm">
            Compara vuelos, trenes y alojamientos en tiempo real
          </p>
        </div>

        {/* Search card */}
        <form
          onSubmit={handleSubmit}
          noValidate
          className="w-full relative z-10"
          aria-label="Buscador de viajes"
        >
          <div className="bg-white rounded-3xl shadow-2xl overflow-visible max-w-[1100px] mx-auto">
            {/* Transport toggle */}
            <div className="px-4 sm:px-6 pt-4 sm:pt-5 pb-0">
              <TransportToggle value={transport} onChange={setTransport} />
            </div>

            {/* Search fields */}
            <div className="p-3 sm:p-4">
              <div className={cn(
                "flex flex-col lg:flex-row items-stretch w-full bg-white rounded-2xl border border-neutral-200",
                "shadow-search divide-y lg:divide-y-0 lg:divide-x divide-neutral-100"
              )}>
                {/* ── Origin ────────────────────────────────────────────── */}
                <div className="relative flex-1 flex flex-col items-start gap-0.5 px-4 py-3 hover:bg-neutral-50 transition-colors rounded-t-2xl lg:rounded-none lg:rounded-l-2xl">
                  <label htmlFor={`${id}-origin`} className="text-2xs font-semibold text-neutral-400 uppercase tracking-wider cursor-pointer">
                    Origen
                  </label>
                  <div className="flex items-center gap-2 w-full">
                    <LocationIcon size="sm" className="text-neutral-400 flex-shrink-0" />
                    <input
                      id={`${id}-origin`}
                      type="text"
                      placeholder={isAccommodation ? "Ciudad" : "Aeropuerto o ciudad"}
                      value={origin}
                      onChange={(e) => {
                        setOrigin(e.target.value);
                        if (errors.origin) setErrors((p) => ({ ...p, origin: "" }));
                      }}
                      className={cn(
                        "w-full bg-transparent border-0 p-0 text-base text-neutral-600 placeholder-neutral-300",
                        "focus:outline-none focus:ring-0 truncate"
                      )}
                    />
                  </div>

                  {/* Swap button (desktop absolute, mobile hidden or separate) */}
                  {!isAccommodation && (
                    <button
                      type="button"
                      onClick={handleSwap}
                      aria-label="Intercambiar origen y destino"
                      className={cn(
                        "hidden lg:flex absolute right-0 top-1/2 -translate-y-1/2 translate-x-1/2 z-10",
                        "w-8 h-8 items-center justify-center rounded-full border-2 border-neutral-200 bg-white",
                        "text-neutral-400 hover:text-neutral-600 hover:border-neutral-400",
                        "transition-all duration-200 hover:rotate-180"
                      )}
                    >
                      <ArrowRightIcon size="xs" />
                    </button>
                  )}
                </div>

                {/* ── Destination ───────────────────────────────────────── */}
                <div className="relative flex-1 flex flex-col items-start gap-0.5 px-4 py-3 hover:bg-neutral-50 transition-colors">
                  <label htmlFor={`${id}-destination`} className="text-2xs font-semibold text-neutral-400 uppercase tracking-wider cursor-pointer">
                    Destino
                  </label>
                  <div className="flex items-center gap-2 w-full">
                    <LocationIcon size="sm" className="text-neutral-400 flex-shrink-0" />
                    <input
                      id={`${id}-destination`}
                      type="text"
                      placeholder={isAccommodation ? "Ciudad o dirección" : "Aeropuerto o ciudad"}
                      value={destination}
                      onChange={(e) => {
                        setDestination(e.target.value);
                        if (errors.destination) setErrors((p) => ({ ...p, destination: "" }));
                      }}
                      className={cn(
                        "w-full bg-transparent border-0 p-0 text-base text-neutral-600 placeholder-neutral-300",
                        "focus:outline-none focus:ring-0 truncate"
                      )}
                    />
                  </div>
                </div>

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
                  className="flex-1 lg:min-w-[140px] hover:bg-neutral-50 transition-colors"
                />

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
                  className="flex-1 lg:min-w-[140px] hover:bg-neutral-50 transition-colors"
                />

                {/* ── Passengers ─────────────────────────────────────────── */}
                <PassengerSelector
                  counts={passengers.counts}
                  total={passengers.total}
                  label={passengers.label}
                  onIncrement={passengers.increment}
                  onDecrement={passengers.decrement}
                  canIncrement={passengers.canIncrement}
                  canDecrement={passengers.canDecrement}
                  className="flex-1 lg:min-w-[150px] hover:bg-neutral-50 transition-colors"
                />

                {/* ── Search CTA ─────────────────────────────────────────── */}
                <div className="flex items-center justify-center p-2 bg-neutral-50 lg:bg-transparent rounded-b-2xl lg:rounded-none lg:rounded-r-2xl">
                  <Button
                    type="submit"
                    variant="primary"
                    size="lg"
                    loading={isLoading}
                    leftIcon={<SearchIcon size="sm" />}
                    className="w-full lg:w-auto rounded-xl h-12 px-6 min-w-[120px]"
                    aria-label="Buscar viajes"
                  >
                    Buscar
                  </Button>
                </div>
              </div>

              {/* Error summary */}
              {Object.keys(errors).length > 0 && (
                <p className="mt-2 text-sm text-primary-500 font-medium px-4 pb-2 text-center lg:text-left">
                  Por favor completa todos los campos requeridos.
                </p>
              )}
            </div>
          </div>

          {/* Quick links */}
          <div className="mt-4 flex flex-wrap gap-2 justify-center px-4">
            {["Madrid → Barcelona", "Valencia → Sevilla", "Bilbao → Málaga"].map((route) => {
              const [from, to] = route.split(" → ");
              return (
                <button
                  key={route}
                  type="button"
                  onClick={() => { setOrigin(from); setDestination(to); }}
                  className={cn(
                    "text-sm text-white hover:text-white",
                    "bg-white/10 hover:bg-white/20 backdrop-blur-sm",
                    "px-4 py-1.5 rounded-pill",
                    "transition-all duration-150 border border-white/20"
                  )}
                >
                  {route}
                </button>
              );
            })}
          </div>
        </form>
      </div>
    </section>
  );
}

export default SearchHero;
