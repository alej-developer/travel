/**
 * Skeleton — Atom
 * Shimmer placeholder for loading states.
 */
import React from "react";
import { cn } from "@/lib/utils";

interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  rounded?: "sm" | "md" | "lg" | "pill" | "circle";
  className?: string;
  count?: number;
}

const roundedMap = {
  sm:     "rounded-lg",
  md:     "rounded-xl",
  lg:     "rounded-2xl",
  pill:   "rounded-full",
  circle: "rounded-full",
};

function SkeletonItem({ width, height, rounded = "md", className }: Omit<SkeletonProps, "count">) {
  return (
    <div
      className={cn("skeleton", roundedMap[rounded], className)}
      style={{
        width:  width  ?? "100%",
        height: height ?? "1rem",
      }}
      role="status"
      aria-label="Loading..."
    />
  );
}

export function Skeleton({ count = 1, ...props }: SkeletonProps) {
  if (count === 1) return <SkeletonItem {...props} />;

  return (
    <div className="flex flex-col gap-2">
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonItem key={i} {...props} />
      ))}
    </div>
  );
}

/* ─── Card Skeleton (composite) ──────────────────────────────────────────── */
export function CardSkeleton() {
  return (
    <div className="bg-white rounded-2xl overflow-hidden shadow-sm border border-neutral-100 animate-pulse-slow">
      {/* Image placeholder */}
      <div className="skeleton h-48 w-full rounded-none" />
      <div className="p-4 space-y-3">
        {/* Title */}
        <div className="skeleton h-4 w-3/4 rounded-lg" />
        {/* Subtitle */}
        <div className="skeleton h-3 w-1/2 rounded-lg" />
        {/* Price row */}
        <div className="flex items-center justify-between pt-2">
          <div className="skeleton h-5 w-24 rounded-lg" />
          <div className="skeleton h-8 w-20 rounded-xl" />
        </div>
      </div>
    </div>
  );
}

export default Skeleton;
