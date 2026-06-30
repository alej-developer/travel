/**
 * usePassengers — Custom hook
 * Manages passenger counts by category (adults, children, infants).
 */
"use client";

import { useState, useCallback } from "react";

export interface PassengerCounts {
  adults: number;
  children: number;
  infants: number;
}

const LIMITS = {
  adults: { min: 1, max: 9 },
  children: { min: 0, max: 8 },
  infants: { min: 0, max: 4 },
};

export function usePassengers(initial: PassengerCounts = { adults: 1, children: 0, infants: 0 }) {
  const [counts, setCounts] = useState<PassengerCounts>(initial);

  const increment = useCallback((type: keyof PassengerCounts) => {
    setCounts((prev) => ({
      ...prev,
      [type]: Math.min(prev[type] + 1, LIMITS[type].max),
    }));
  }, []);

  const decrement = useCallback((type: keyof PassengerCounts) => {
    setCounts((prev) => ({
      ...prev,
      [type]: Math.max(prev[type] - 1, LIMITS[type].min),
    }));
  }, []);

  const total = counts.adults + counts.children + counts.infants;

  const label =
    total === 1 ? "1 pasajero" : `${total} pasajeros`;

  const canIncrement = (type: keyof PassengerCounts) =>
    counts[type] < LIMITS[type].max;

  const canDecrement = (type: keyof PassengerCounts) =>
    counts[type] > LIMITS[type].min;

  const reset = useCallback(() => setCounts(initial), [initial]);

  return {
    counts,
    total,
    label,
    increment,
    decrement,
    canIncrement,
    canDecrement,
    reset,
  };
}
