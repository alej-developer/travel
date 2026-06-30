/**
 * useDateRange — Custom hook
 *
 * Manages a date range selection (check-in / check-out or departure / return).
 * Exposes formatted strings, raw Date objects, validation and reset.
 */
"use client";

import { useState, useCallback } from "react";
import { format, isAfter, isBefore, isToday, parseISO } from "date-fns";
import { es } from "date-fns/locale";

export interface DateRange {
  startDate: Date | null;
  endDate: Date | null;
}

export interface UseDateRangeReturn {
  range: DateRange;
  startFormatted: string;
  endFormatted: string;
  isValid: boolean;
  nightCount: number;
  setStartDate: (date: Date | null) => void;
  setEndDate: (date: Date | null) => void;
  setRange: (start: Date | null, end: Date | null) => void;
  reset: () => void;
  isDateDisabled: (date: Date) => boolean;
}

const DEFAULT_FORMAT = "d MMM yyyy";

export function useDateRange(
  formatStr: string = DEFAULT_FORMAT,
  minDate: Date = new Date()
): UseDateRangeReturn {
  const [range, setRangeState] = useState<DateRange>({
    startDate: null,
    endDate: null,
  });

  const setStartDate = useCallback((date: Date | null) => {
    setRangeState((prev) => ({
      startDate: date,
      // Clear end date if it's before the new start
      endDate:
        prev.endDate && date && !isAfter(prev.endDate, date)
          ? null
          : prev.endDate,
    }));
  }, []);

  const setEndDate = useCallback((date: Date | null) => {
    setRangeState((prev) => ({
      ...prev,
      endDate: date,
    }));
  }, []);

  const setRange = useCallback((start: Date | null, end: Date | null) => {
    setRangeState({ startDate: start, endDate: end });
  }, []);

  const reset = useCallback(() => {
    setRangeState({ startDate: null, endDate: null });
  }, []);

  const isDateDisabled = useCallback(
    (date: Date): boolean => {
      return isBefore(date, minDate) && !isToday(date);
    },
    [minDate]
  );

  const startFormatted = range.startDate
    ? format(range.startDate, formatStr, { locale: es })
    : "";

  const endFormatted = range.endDate
    ? format(range.endDate, formatStr, { locale: es })
    : "";

  const isValid = Boolean(
    range.startDate &&
    range.endDate &&
    isAfter(range.endDate, range.startDate)
  );

  const nightCount =
    range.startDate && range.endDate
      ? Math.round(
          (range.endDate.getTime() - range.startDate.getTime()) /
            (1000 * 60 * 60 * 24)
        )
      : 0;

  return {
    range,
    startFormatted,
    endFormatted,
    isValid,
    nightCount,
    setStartDate,
    setEndDate,
    setRange,
    reset,
    isDateDisabled,
  };
}
