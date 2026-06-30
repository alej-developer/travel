/**
 * Badge — Atom
 * Transport type badge, status indicator, tag.
 */
import React from "react";
import { cn } from "@/lib/utils";

type BadgeVariant = "default" | "primary" | "accent" | "success" | "warning" | "error" | "neutral";

interface BadgeProps {
  variant?: BadgeVariant;
  size?: "sm" | "md";
  dot?: boolean;
  children: React.ReactNode;
  className?: string;
}

const variantClasses: Record<BadgeVariant, string> = {
  default: "bg-neutral-100 text-neutral-600",
  primary: "bg-primary-50 text-primary-600",
  accent:  "bg-accent-50 text-accent-700",
  success: "bg-green-50 text-green-700",
  warning: "bg-amber-50 text-amber-700",
  error:   "bg-red-50 text-red-600",
  neutral: "bg-neutral-200 text-neutral-500",
};

const dotColors: Record<BadgeVariant, string> = {
  default: "bg-neutral-400",
  primary: "bg-primary-500",
  accent:  "bg-accent-500",
  success: "bg-green-500",
  warning: "bg-amber-500",
  error:   "bg-red-500",
  neutral: "bg-neutral-400",
};

export function Badge({
  variant = "default",
  size = "md",
  dot = false,
  children,
  className,
}: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 font-medium rounded-pill",
        size === "sm" ? "text-2xs px-2 py-0.5" : "text-xs px-2.5 py-1",
        variantClasses[variant],
        className
      )}
    >
      {dot && (
        <span
          className={cn(
            "flex-shrink-0 rounded-full",
            size === "sm" ? "w-1.5 h-1.5" : "w-2 h-2",
            dotColors[variant]
          )}
        />
      )}
      {children}
    </span>
  );
}

export default Badge;
