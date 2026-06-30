/**
 * TransportToggle — Molecule
 * Toggle group for selecting transport type: Vuelo | Tren | Alojamiento
 */
"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { PlaneIcon, TrainIcon, HotelIcon } from "@/components/atoms/Icon";

export type TransportType = "flight" | "train" | "accommodation";

interface TransportOption {
  type: TransportType;
  label: string;
  Icon: React.ComponentType<{ size?: "xs" | "sm" | "md" | "lg" | "xl"; className?: string }>;
}

const OPTIONS: TransportOption[] = [
  { type: "flight",        label: "Vuelo",        Icon: PlaneIcon },
  { type: "train",         label: "Tren",          Icon: TrainIcon },
  { type: "accommodation", label: "Alojamiento",   Icon: HotelIcon },
];

interface TransportToggleProps {
  value: TransportType;
  onChange: (type: TransportType) => void;
  className?: string;
}

export function TransportToggle({ value, onChange, className }: TransportToggleProps) {
  return (
    <div
      role="tablist"
      aria-label="Tipo de transporte"
      className={cn(
        "inline-flex items-center bg-neutral-100 rounded-2xl p-1 gap-0.5",
        className
      )}
    >
      {OPTIONS.map(({ type, label, Icon }) => {
        const isActive = value === type;
        return (
          <button
            key={type}
            role="tab"
            aria-selected={isActive}
            onClick={() => onChange(type)}
            className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold",
              "transition-all duration-200 ease-smooth",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-1",
              isActive
                ? "bg-white text-neutral-600 shadow-sm"
                : "text-neutral-400 hover:text-neutral-600 hover:bg-neutral-50"
            )}
          >
            <Icon size="sm" />
            <span className="hidden sm:inline">{label}</span>
          </button>
        );
      })}
    </div>
  );
}

export default TransportToggle;
