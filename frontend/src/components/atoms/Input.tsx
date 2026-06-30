/**
 * Input — Atom
 *
 * A labeled text input with left/right addornments, error state and hint text.
 */
import React, { forwardRef } from "react";
import { cn } from "@/lib/utils";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  hint?: string;
  error?: string;
  leftAdornment?: React.ReactNode;
  rightAdornment?: React.ReactNode;
  fullWidth?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      hint,
      error,
      leftAdornment,
      rightAdornment,
      fullWidth = false,
      className,
      id,
      ...props
    },
    ref
  ) => {
    const inputId = id ?? label?.toLowerCase().replace(/\s+/g, "-");

    return (
      <div className={cn("flex flex-col gap-1", fullWidth && "w-full")}>
        {label && (
          <label
            htmlFor={inputId}
            className="text-xs font-semibold text-neutral-500 uppercase tracking-wider"
          >
            {label}
          </label>
        )}

        <div className="relative flex items-center">
          {leftAdornment && (
            <span className="absolute left-3 text-neutral-400 flex items-center pointer-events-none">
              {leftAdornment}
            </span>
          )}

          <input
            ref={ref}
            id={inputId}
            className={cn(
              // Base
              "w-full bg-white text-neutral-600 placeholder-neutral-300",
              "rounded-xl border border-neutral-200",
              "py-3 text-base transition-all duration-200",
              // Padding adjustments for adornments
              leftAdornment ? "pl-10 pr-4" : "px-4",
              rightAdornment ? "pr-10" : "",
              // States
              "hover:border-neutral-400",
              "focus:outline-none focus:border-neutral-600 focus:ring-0",
              // Error
              error
                ? "border-primary-400 focus:border-primary-500 bg-primary-50"
                : "",
              className
            )}
            aria-invalid={!!error}
            aria-describedby={error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined}
            {...props}
          />

          {rightAdornment && (
            <span className="absolute right-3 text-neutral-400 flex items-center">
              {rightAdornment}
            </span>
          )}
        </div>

        {error && (
          <p id={`${inputId}-error`} className="text-xs text-primary-500 mt-0.5">
            {error}
          </p>
        )}
        {hint && !error && (
          <p id={`${inputId}-hint`} className="text-xs text-neutral-400 mt-0.5">
            {hint}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";
export default Input;
