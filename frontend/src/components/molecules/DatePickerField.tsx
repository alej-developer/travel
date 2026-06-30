/**
 * DatePickerField — Molecule
 *
 * Custom calendar dropdown (no external library).
 * Renders a mini calendar with prev/next month navigation.
 */
"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import {
  format,
  startOfMonth,
  endOfMonth,
  eachDayOfInterval,
  isSameDay,
  isSameMonth,
  isToday,
  isBefore,
  addMonths,
  subMonths,
  getDay,
} from "date-fns";
import { es } from "date-fns/locale";
import { cn } from "@/lib/utils";
import { CalendarIcon, ChevronDownIcon, ChevronUpIcon } from "@/components/atoms/Icon";

interface DatePickerFieldProps {
  label: string;
  value: Date | null;
  onChange: (date: Date) => void;
  placeholder?: string;
  minDate?: Date;
  highlightRange?: { start: Date | null; end: Date | null };
  className?: string;
}

const WEEKDAYS = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sa", "Do"];

export function DatePickerField({
  label,
  value,
  onChange,
  placeholder = "Seleccionar fecha",
  minDate = new Date(),
  highlightRange,
  className,
}: DatePickerFieldProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [viewDate, setViewDate] = useState(value ?? new Date());
  const containerRef = useRef<HTMLDivElement>(null);

  // Close on outside click
  useEffect(() => {
    function handleOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    }
    if (isOpen) document.addEventListener("mousedown", handleOutside);
    return () => document.removeEventListener("mousedown", handleOutside);
  }, [isOpen]);

  // Keyboard: Escape closes
  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.key === "Escape") setIsOpen(false);
    }
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, []);

  const days = eachDayOfInterval({
    start: startOfMonth(viewDate),
    end: endOfMonth(viewDate),
  });

  // Monday-based offset (0=Mon, 6=Sun)
  const firstDayOffset = (getDay(startOfMonth(viewDate)) + 6) % 7;

  const isDisabled = useCallback(
    (date: Date) => isBefore(date, minDate) && !isToday(date),
    [minDate]
  );

  const isInRange = (date: Date) => {
    if (!highlightRange?.start || !highlightRange?.end) return false;
    return (
      date >= highlightRange.start && date <= highlightRange.end
    );
  };

  const isRangeStart = (date: Date) =>
    highlightRange?.start ? isSameDay(date, highlightRange.start) : false;
  const isRangeEnd = (date: Date) =>
    highlightRange?.end ? isSameDay(date, highlightRange.end) : false;

  const displayValue = value ? format(value, "d MMM yyyy", { locale: es }) : "";

  return (
    <div ref={containerRef} className={cn("relative", className)}>
      {/* Trigger */}
      <button
        type="button"
        onClick={() => setIsOpen((o) => !o)}
        aria-expanded={isOpen}
        aria-haspopup="dialog"
        className={cn(
          "w-full flex flex-col items-start gap-0.5 px-4 py-3",
          "bg-transparent border-0 text-left cursor-pointer",
          "transition-colors duration-150",
          "focus:outline-none"
        )}
      >
        <span className="text-2xs font-semibold text-neutral-400 uppercase tracking-wider">
          {label}
        </span>
        <div className="flex items-center gap-2 w-full">
          <CalendarIcon size="sm" className="text-neutral-400 flex-shrink-0" />
          <span
            className={cn(
              "text-base truncate",
              displayValue ? "text-neutral-600 font-medium" : "text-neutral-300"
            )}
          >
            {displayValue || placeholder}
          </span>
        </div>
      </button>

      {/* Calendar dropdown */}
      {isOpen && (
        <div
          role="dialog"
          aria-label={`Seleccionar ${label}`}
          className={cn(
            "absolute top-full left-0 z-50 mt-2",
            "bg-white rounded-2xl shadow-xl border border-neutral-100",
            "p-4 w-72",
            "animate-fade-scale"
          )}
        >
          {/* Month nav */}
          <div className="flex items-center justify-between mb-3">
            <button
              type="button"
              onClick={() => setViewDate((d) => subMonths(d, 1))}
              disabled={isBefore(startOfMonth(subMonths(viewDate, 1)), startOfMonth(minDate))}
              className={cn(
                "p-1.5 rounded-lg text-neutral-400",
                "hover:bg-neutral-100 hover:text-neutral-600",
                "disabled:opacity-30 disabled:cursor-not-allowed",
                "transition-colors duration-150"
              )}
            >
              <ChevronUpIcon size="sm" className="rotate-[-90deg]" />
            </button>

            <span className="text-sm font-semibold text-neutral-600 capitalize">
              {format(viewDate, "MMMM yyyy", { locale: es })}
            </span>

            <button
              type="button"
              onClick={() => setViewDate((d) => addMonths(d, 1))}
              className={cn(
                "p-1.5 rounded-lg text-neutral-400",
                "hover:bg-neutral-100 hover:text-neutral-600",
                "transition-colors duration-150"
              )}
            >
              <ChevronDownIcon size="sm" className="rotate-[-90deg]" />
            </button>
          </div>

          {/* Weekday headers */}
          <div className="grid grid-cols-7 mb-1">
            {WEEKDAYS.map((d) => (
              <div key={d} className="text-center text-2xs font-semibold text-neutral-300 py-1">
                {d}
              </div>
            ))}
          </div>

          {/* Days grid */}
          <div className="grid grid-cols-7 gap-y-0.5">
            {/* Offset empty cells */}
            {Array.from({ length: firstDayOffset }).map((_, i) => (
              <div key={`empty-${i}`} />
            ))}

            {days.map((day) => {
              const disabled = isDisabled(day);
              const selected = value ? isSameDay(day, value) : false;
              const today = isToday(day);
              const inRange = isInRange(day);
              const rangeStart = isRangeStart(day);
              const rangeEnd = isRangeEnd(day);
              const otherMonth = !isSameMonth(day, viewDate);

              return (
                <button
                  key={day.toISOString()}
                  type="button"
                  disabled={disabled}
                  onClick={() => {
                    onChange(day);
                    setIsOpen(false);
                  }}
                  className={cn(
                    "relative h-8 w-8 mx-auto flex items-center justify-center",
                    "text-sm rounded-full font-medium transition-all duration-150",
                    "focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500",
                    // Normal state
                    !disabled && !selected && !inRange &&
                      "text-neutral-600 hover:bg-neutral-100",
                    // Today
                    today && !selected && "font-bold text-primary-500",
                    // In range
                    inRange && !rangeStart && !rangeEnd &&
                      "bg-primary-50 text-primary-600 rounded-none",
                    // Range endpoints
                    (rangeStart || rangeEnd) &&
                      "bg-primary-500 text-white shadow-sm",
                    // Single selected (not range)
                    selected && !highlightRange?.end &&
                      "bg-primary-500 text-white shadow-sm",
                    // Disabled
                    disabled && "text-neutral-200 cursor-not-allowed",
                    // Other month
                    otherMonth && "text-neutral-300"
                  )}
                >
                  {format(day, "d")}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

export default DatePickerField;
