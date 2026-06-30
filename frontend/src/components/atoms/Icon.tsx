/**
 * Icon — Atom
 * Thin wrapper for SVG icons with consistent sizing.
 * Uses inline SVG — no icon library dependency.
 */
import React from "react";
import { cn } from "@/lib/utils";

type IconSize = "xs" | "sm" | "md" | "lg" | "xl";

const sizeMap: Record<IconSize, number> = {
  xs: 12,
  sm: 16,
  md: 20,
  lg: 24,
  xl: 32,
};

interface IconProps {
  size?: IconSize;
  className?: string;
  "aria-label"?: string;
}

function makeIcon(path: React.ReactNode, viewBox = "0 0 24 24") {
  return function IconComponent({ size = "md", className, "aria-label": label }: IconProps) {
    const px = sizeMap[size];
    return (
      <svg
        width={px}
        height={px}
        viewBox={viewBox}
        fill="none"
        stroke="currentColor"
        strokeWidth={1.75}
        strokeLinecap="round"
        strokeLinejoin="round"
        className={cn("flex-shrink-0", className)}
        aria-label={label}
        aria-hidden={!label}
        role={label ? "img" : undefined}
      >
        {path}
      </svg>
    );
  };
}

// ── Icon catalogue ──────────────────────────────────────────────────────────

export const PlaneIcon = makeIcon(
  <>
    <path d="M17.8 19.2L16 11l3.5-3.5C21 6 21 4 19.5 2.5S18 2 16.5 3.5L13 7 4.8 5.2a1 1 0 0 0-.8.3l-.7.7a1 1 0 0 0 .1 1.4L8 11l-2 3H4l-1 1 3 2 2 3 1-1v-2l3-2 3.5 4.9a1 1 0 0 0 1.4.1l.7-.7a1 1 0 0 0 .2-.9z" />
  </>
);

export const TrainIcon = makeIcon(
  <>
    <rect x="4" y="3" width="16" height="16" rx="2" />
    <path d="M4 11h16" />
    <path d="M12 3v8" />
    <path d="M8 19l-2 3" />
    <path d="M18 22l-2-3" />
    <circle cx="8.5" cy="15.5" r="1.5" fill="currentColor" stroke="none" />
    <circle cx="15.5" cy="15.5" r="1.5" fill="currentColor" stroke="none" />
  </>
);

export const HotelIcon = makeIcon(
  <>
    <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
    <polyline points="9 22 9 12 15 12 15 22" />
  </>
);

export const CalendarIcon = makeIcon(
  <>
    <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
    <line x1="16" y1="2" x2="16" y2="6" />
    <line x1="8" y1="2" x2="8" y2="6" />
    <line x1="3" y1="10" x2="21" y2="10" />
  </>
);

export const UsersIcon = makeIcon(
  <>
    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
    <circle cx="9" cy="7" r="4" />
    <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
    <path d="M16 3.13a4 4 0 0 1 0 7.75" />
  </>
);

export const SearchIcon = makeIcon(
  <>
    <circle cx="11" cy="11" r="8" />
    <line x1="21" y1="21" x2="16.65" y2="16.65" />
  </>
);

export const ChevronDownIcon = makeIcon(
  <polyline points="6 9 12 15 18 9" />
);

export const ChevronUpIcon = makeIcon(
  <polyline points="18 15 12 9 6 15" />
);

export const XIcon = makeIcon(
  <>
    <line x1="18" y1="6" x2="6" y2="18" />
    <line x1="6" y1="6" x2="18" y2="18" />
  </>
);

export const PlusIcon = makeIcon(
  <>
    <line x1="12" y1="5" x2="12" y2="19" />
    <line x1="5" y1="12" x2="19" y2="12" />
  </>
);

export const MinusIcon = makeIcon(
  <line x1="5" y1="12" x2="19" y2="12" />
);

export const LocationIcon = makeIcon(
  <>
    <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
    <circle cx="12" cy="10" r="3" />
  </>
);

export const StarIcon = makeIcon(
  <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
);

export const ArrowRightIcon = makeIcon(
  <>
    <line x1="5" y1="12" x2="19" y2="12" />
    <polyline points="12 5 19 12 12 19" />
  </>
);

export const FilterIcon = makeIcon(
  <>
    <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
  </>
);

export const SpinnerIcon = makeIcon(
  <>
    <path d="M21 12a9 9 0 1 1-6.219-8.56" />
  </>
);
