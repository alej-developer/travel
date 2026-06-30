/**
 * PassengerSelector — Molecule
 * Dropdown with increment/decrement controls for Adults, Children, Infants.
 */
"use client";

import React, { useState, useRef, useEffect } from "react";
import { cn } from "@/lib/utils";
import { UsersIcon, PlusIcon, MinusIcon, ChevronDownIcon } from "@/components/atoms/Icon";
import type { PassengerCounts } from "@/hooks/usePassengers";

interface PassengerCategory {
  key: keyof PassengerCounts;
  label: string;
  description: string;
}

const CATEGORIES: PassengerCategory[] = [
  { key: "adults",   label: "Adultos",  description: "13 años o más" },
  { key: "children", label: "Niños",    description: "2 a 12 años" },
  { key: "infants",  label: "Bebés",    description: "Menores de 2 años" },
];

interface PassengerSelectorProps {
  counts: PassengerCounts;
  total: number;
  label: string;
  onIncrement: (type: keyof PassengerCounts) => void;
  onDecrement: (type: keyof PassengerCounts) => void;
  canIncrement: (type: keyof PassengerCounts) => boolean;
  canDecrement: (type: keyof PassengerCounts) => boolean;
  className?: string;
}

export function PassengerSelector({
  counts,
  total,
  label,
  onIncrement,
  onDecrement,
  canIncrement,
  canDecrement,
  className,
}: PassengerSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    }
    if (isOpen) document.addEventListener("mousedown", handleOutside);
    return () => document.removeEventListener("mousedown", handleOutside);
  }, [isOpen]);

  return (
    <div ref={containerRef} className={cn("relative", className)}>
      {/* Trigger */}
      <button
        type="button"
        onClick={() => setIsOpen((o) => !o)}
        aria-expanded={isOpen}
        aria-haspopup="listbox"
        className="w-full flex flex-col items-start gap-0.5 px-4 py-3 bg-transparent border-0 text-left cursor-pointer focus:outline-none"
      >
        <span className="text-2xs font-semibold text-neutral-400 uppercase tracking-wider">
          Pasajeros
        </span>
        <div className="flex items-center gap-2 w-full">
          <UsersIcon size="sm" className="text-neutral-400 flex-shrink-0" />
          <span className="text-base font-medium text-neutral-600 truncate">
            {label}
          </span>
          <ChevronDownIcon
            size="sm"
            className={cn(
              "text-neutral-300 ml-auto flex-shrink-0 transition-transform duration-200",
              isOpen && "rotate-180"
            )}
          />
        </div>
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div
          role="listbox"
          className={cn(
            "absolute top-full left-0 z-50 mt-2",
            "bg-white rounded-2xl shadow-xl border border-neutral-100",
            "p-4 w-72",
            "animate-fade-scale"
          )}
        >
          <div className="space-y-4">
            {CATEGORIES.map(({ key, label: catLabel, description }) => (
              <div key={key} className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold text-neutral-600">{catLabel}</p>
                  <p className="text-xs text-neutral-400">{description}</p>
                </div>

                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    onClick={() => onDecrement(key)}
                    disabled={!canDecrement(key)}
                    aria-label={`Reducir ${catLabel}`}
                    className={cn(
                      "w-8 h-8 flex items-center justify-center rounded-full",
                      "border-2 transition-all duration-150",
                      canDecrement(key)
                        ? "border-neutral-300 text-neutral-600 hover:border-neutral-500 hover:text-neutral-800"
                        : "border-neutral-100 text-neutral-200 cursor-not-allowed"
                    )}
                  >
                    <MinusIcon size="xs" />
                  </button>

                  <span className="w-5 text-center text-base font-semibold text-neutral-600">
                    {counts[key]}
                  </span>

                  <button
                    type="button"
                    onClick={() => onIncrement(key)}
                    disabled={!canIncrement(key)}
                    aria-label={`Añadir ${catLabel}`}
                    className={cn(
                      "w-8 h-8 flex items-center justify-center rounded-full",
                      "border-2 transition-all duration-150",
                      canIncrement(key)
                        ? "border-neutral-300 text-neutral-600 hover:border-neutral-500 hover:text-neutral-800"
                        : "border-neutral-100 text-neutral-200 cursor-not-allowed"
                    )}
                  >
                    <PlusIcon size="xs" />
                  </button>
                </div>
              </div>
            ))}
          </div>

          <button
            type="button"
            onClick={() => setIsOpen(false)}
            className="mt-4 w-full py-2 text-sm font-semibold text-neutral-600 hover:text-neutral-800 text-center transition-colors"
          >
            Confirmar
          </button>
        </div>
      )}
    </div>
  );
}

export default PassengerSelector;
