/**
 * Provider configuration — client-side mirror of the ScraperFactory transport mapping.
 *
 * This provides the same domain-to-transport-type mapping used on the backend,
 * so the frontend can display which providers are being queried without an API call.
 */

import type { TransportType } from "./api-client";

const TRANSPORT_DOMAINS: Record<TransportType, string[]> = {
  train: [
    "renfe.com",
    "trenes.com",
    "sncf-connect.com",
    "thetrainline.com",
    "ouigo.com",
    "iryo.eu",
  ],
  flight: [
    "iberia.com",
    "ryanair.com",
    "vueling.com",
    "easyjet.com",
    "skyscanner.es",
    "google.com/travel/flights",
  ],
  accommodation: [
    "booking.com",
    "airbnb.com",
    "vrbo.com",
    "ruralia.com",
    "escapadarural.com",
    "idealista.com",
    "trivago.es",
  ],
};

export const ScraperFactory = {
  /**
   * Return provider domains for the given transport type.
   */
  for_transport_type(transportType: TransportType): string[] {
    return TRANSPORT_DOMAINS[transportType] ?? [];
  },

  /**
   * Return all registered provider domains.
   */
  available_domains(): string[] {
    return Object.values(TRANSPORT_DOMAINS).flat().sort();
  },

  /**
   * Return the total number of providers.
   */
  total_providers(): number {
    return Object.values(TRANSPORT_DOMAINS).flat().length;
  },
};
