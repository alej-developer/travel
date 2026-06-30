/**
 * Button — Atom
 *
 * Variants: primary | secondary | ghost | danger
 * Sizes: sm | md | lg
 */
import React from "react";
import { cn } from "@/lib/utils";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
type ButtonSize = "sm" | "md" | "lg";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  fullWidth?: boolean;
}

const variantClasses: Record<ButtonVariant, string> = {
  primary: [
    "bg-primary-500 text-white",
    "hover:bg-primary-600 active:bg-primary-700",
    "shadow-sm hover:shadow-md",
    "disabled:bg-neutral-200 disabled:text-neutral-400 disabled:cursor-not-allowed disabled:shadow-none",
  ].join(" "),

  secondary: [
    "bg-white text-neutral-600 border border-neutral-300",
    "hover:bg-neutral-50 hover:border-neutral-400 active:bg-neutral-100",
    "shadow-xs hover:shadow-sm",
    "disabled:bg-neutral-50 disabled:text-neutral-300 disabled:border-neutral-200 disabled:cursor-not-allowed",
  ].join(" "),

  ghost: [
    "bg-transparent text-neutral-600",
    "hover:bg-neutral-100 active:bg-neutral-200",
    "disabled:text-neutral-300 disabled:cursor-not-allowed",
  ].join(" "),

  danger: [
    "bg-white text-primary-500 border border-primary-200",
    "hover:bg-primary-50 hover:border-primary-400",
    "disabled:opacity-50 disabled:cursor-not-allowed",
  ].join(" "),
};

const sizeClasses: Record<ButtonSize, string> = {
  sm: "h-8 px-3 text-sm gap-1.5 rounded-lg",
  md: "h-11 px-5 text-base gap-2 rounded-xl",
  lg: "h-14 px-7 text-lg gap-2.5 rounded-2xl",
};

export function Button({
  variant = "primary",
  size = "md",
  loading = false,
  leftIcon,
  rightIcon,
  fullWidth = false,
  className,
  children,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        // Base
        "inline-flex items-center justify-center font-semibold",
        "transition-all duration-200 ease-smooth",
        "select-none cursor-pointer",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2",
        // Variant + size
        variantClasses[variant],
        sizeClasses[size],
        // Full width
        fullWidth && "w-full",
        // Loading state
        loading && "opacity-75 cursor-wait",
        className
      )}
      disabled={disabled || loading}
      aria-busy={loading}
      {...props}
    >
      {loading ? (
        <span className="inline-block w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
      ) : (
        leftIcon && <span className="flex-shrink-0">{leftIcon}</span>
      )}
      {children && <span>{children}</span>}
      {rightIcon && !loading && (
        <span className="flex-shrink-0">{rightIcon}</span>
      )}
    </button>
  );
}

export default Button;
