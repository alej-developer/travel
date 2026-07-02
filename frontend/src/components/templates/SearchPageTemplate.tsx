/**
 * SearchPageTemplate — Template
 * Composes Navbar + SearchHero + ResultsGrid into the full page layout.
 */
"use client";

import React, { useState } from "react";
import { Navbar } from "@/components/organisms/Navbar";
import { SearchHero } from "@/components/organisms/SearchHero";
import { ResultsGrid } from "@/components/organisms/ResultsGrid";
import type { SearchParams } from "@/lib/api-client";

export function SearchPageTemplate() {
  const [searchParams, setSearchParams] = useState<SearchParams | null>(null);
  const [isSearching, setIsSearching] = useState(false);

  async function handleSearch(params: SearchParams) {
    setIsSearching(true);
    setSearchParams(params);
    // isSearching will turn off when React Query finishes
    setTimeout(() => setIsSearching(false), 300);
  }

  return (
    <div className="min-h-screen bg-neutral-50">
      <Navbar />

      {/* Hero — full width with gradient */}
      <SearchHero
        onSearch={handleSearch}
        isLoading={isSearching}
      />

      {/* Results */}
      <ResultsGrid params={searchParams} />

      {/* Footer spacer */}
      <div className="h-16" />
    </div>
  );
}

export default SearchPageTemplate;
