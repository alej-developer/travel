/**
 * Navbar — Organism
 * Sticky top navigation bar.
 */
"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { Button } from "@/components/atoms/Button";
import { PlaneIcon } from "@/components/atoms/Icon";

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <header
      className={cn(
        "fixed top-0 left-0 right-0 z-50",
        "transition-all duration-300",
        scrolled
          ? "bg-white/95 backdrop-blur-md shadow-sm border-b border-neutral-100"
          : "bg-transparent"
      )}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className={cn(
            "w-9 h-9 rounded-xl flex items-center justify-center",
            "bg-primary-500 group-hover:bg-primary-600 transition-colors duration-200"
          )}>
            <PlaneIcon size="sm" className="text-white" />
          </div>
          <span className={cn(
            "text-lg font-black tracking-tight",
            scrolled ? "text-neutral-600" : "text-white"
          )}>
            TravelEngine
          </span>
        </Link>

        {/* Nav links */}
        <nav className="hidden md:flex items-center gap-6">
          {["Vuelos", "Trenes", "Hoteles", "Ofertas"].map((item) => (
            <Link
              key={item}
              href={`/${item.toLowerCase()}`}
              className={cn(
                "text-sm font-semibold transition-colors duration-150",
                scrolled
                  ? "text-neutral-500 hover:text-neutral-700"
                  : "text-white/80 hover:text-white"
              )}
            >
              {item}
            </Link>
          ))}
        </nav>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <Button
            variant={scrolled ? "ghost" : "ghost"}
            size="sm"
            className={cn(
              scrolled ? "text-neutral-600" : "text-white hover:bg-white/10"
            )}
          >
            Iniciar sesión
          </Button>
          <Button
            variant="primary"
            size="sm"
            className="hidden sm:flex"
          >
            Registro
          </Button>
        </div>
      </div>
    </header>
  );
}

export default Navbar;
