/**
 * Travel API Client — typed HTTP client using axios + React Query
 *
 * All endpoints mirror the FastAPI backend (api/v1/).
 */
import axios, { AxiosInstance, AxiosResponse } from "axios";

// ─── Types ─────────────────────────────────────────────────────────────────

export type TransportType = "flight" | "train" | "accommodation";

export interface SearchParams {
  origin?: string;
  destination?: string;
  date_from?: string;     // YYYY-MM-DD
  date_to?: string;       // YYYY-MM-DD
  passengers?: number;
  type?: TransportType;
  page?: number;
  page_size?: number;
}

export interface FlightResult {
  id: string;
  origin: string;
  destination: string;
  departure_at: string;
  arrival_at: string;
  airline: string;
  flight_number: string;
  price_cents: number;
  currency: string;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface TrainResult {
  id: string;
  origin_station: string;
  destination_station: string;
  departure_at: string;
  arrival_at: string;
  operator: string;
  train_number: string;
  service_class: string;
  price_cents: number;
  currency: string;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface AccommodationResult {
  id: string;
  name: string;
  address: string;
  city: string;
  country_code: string;
  check_in: string;
  check_out: string;
  room_type: string;
  price_per_night_cents: number;
  currency: string;
  star_rating: number | null;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export type TravelResult = FlightResult | TrainResult | AccommodationResult;

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

// ─── Aggregated search types ────────────────────────────────────────────────

export interface ProviderInfo {
  domain: string;
  display_name: string;
}

export interface ProviderResult {
  provider: string;
  provider_display_name: string;
  price_raw: string | null;
  price_cents: number | null;
  currency: string;
  departure_time: string | null;
  arrival_time: string | null;
  duration: string | null;
  name: string | null;
  operator: string | null;
  extra: Record<string, unknown>;
  url: string | null;
}

export interface AggregatedSearchResponse {
  transport_type: TransportType;
  origin: string;
  destination: string;
  date_from: string;
  date_to: string | null;
  providers_queried: string[];
  providers_succeeded: string[];
  providers_failed: string[];
  results: ProviderResult[];
  total_results: number;
  search_timestamp: string;
}

export interface TriggerScrapingResponse {
  task_id: string;
  transport_type: string;
  providers: string[];
  provider_names: Record<string, string>;
  status: string;
}

// ─── Provider display names (client-side fallback) ──────────────────────────

export const PROVIDER_DISPLAY_NAMES: Record<string, string> = {
  // Trains
  "renfe.com": "Renfe",
  "trenes.com": "Trenes.com",
  "sncf-connect.com": "SNCF Connect",
  "thetrainline.com": "Trainline",
  "ouigo.com": "Ouigo",
  "iryo.eu": "Iryo",
  // Flights
  "iberia.com": "Iberia",
  "ryanair.com": "Ryanair",
  "vueling.com": "Vueling",
  "easyjet.com": "EasyJet",
  "skyscanner.es": "Skyscanner",
  "google.com/travel/flights": "Google Flights",
  // Accommodations
  "booking.com": "Booking.com",
  "airbnb.com": "Airbnb",
  "vrbo.com": "Vrbo",
  "ruralia.com": "Ruralia",
  "escapadarural.com": "Escapada Rural",
  "idealista.com": "Idealista",
  "trivago.es": "Trivago",
};

export const PROVIDER_COLORS: Record<string, string> = {
  // Trains
  "renfe.com": "bg-purple-100 text-purple-700",
  "trenes.com": "bg-blue-100 text-blue-700",
  "sncf-connect.com": "bg-indigo-100 text-indigo-700",
  "thetrainline.com": "bg-cyan-100 text-cyan-700",
  "ouigo.com": "bg-pink-100 text-pink-700",
  "iryo.eu": "bg-red-100 text-red-700",
  // Flights
  "iberia.com": "bg-red-100 text-red-700",
  "ryanair.com": "bg-blue-100 text-blue-700",
  "vueling.com": "bg-yellow-100 text-yellow-700",
  "easyjet.com": "bg-orange-100 text-orange-700",
  "skyscanner.es": "bg-sky-100 text-sky-700",
  "google.com/travel/flights": "bg-green-100 text-green-700",
  // Accommodations
  "booking.com": "bg-blue-100 text-blue-700",
  "airbnb.com": "bg-rose-100 text-rose-700",
  "vrbo.com": "bg-indigo-100 text-indigo-700",
  "ruralia.com": "bg-emerald-100 text-emerald-700",
  "escapadarural.com": "bg-green-100 text-green-700",
  "idealista.com": "bg-lime-100 text-lime-700",
  "trivago.es": "bg-teal-100 text-teal-700",
};

// ─── Client factory ─────────────────────────────────────────────────────────

function createApiClient(): AxiosInstance {
  const client = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
    timeout: 30_000,
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
  });

  // Request interceptor — attach auth token if present
  client.interceptors.request.use((config) => {
    if (typeof window !== "undefined") {
      const token = sessionStorage.getItem("auth_token");
      if (token) config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  // Response interceptor — normalize errors
  client.interceptors.response.use(
    (response: AxiosResponse) => response,
    (error) => {
      const message =
        error.response?.data?.detail ??
        error.response?.data?.message ??
        error.message ??
        "Unknown error";
      return Promise.reject(new Error(String(message)));
    }
  );

  return client;
}

export const apiClient = createApiClient();

// ─── API functions ──────────────────────────────────────────────────────────

export const travelApi = {
  /** Fetch flights with optional filters */
  getFlights: async (
    params?: SearchParams
  ): Promise<PaginatedResponse<FlightResult>> => {
    const { data } = await apiClient.get<PaginatedResponse<FlightResult>>(
      "/api/v1/flights",
      { params }
    );
    return data;
  },

  /** Fetch trains with optional filters */
  getTrains: async (
    params?: SearchParams
  ): Promise<PaginatedResponse<TrainResult>> => {
    const { data } = await apiClient.get<PaginatedResponse<TrainResult>>(
      "/api/v1/trains",
      { params }
    );
    return data;
  },

  /** Fetch accommodations with optional filters */
  getAccommodations: async (
    params?: SearchParams
  ): Promise<PaginatedResponse<AccommodationResult>> => {
    const { data } = await apiClient.get<PaginatedResponse<AccommodationResult>>(
      "/api/v1/accommodations",
      { params }
    );
    return data;
  },

  /** Aggregated search across all providers for a transport type */
  searchAggregated: async (
    params: SearchParams
  ): Promise<AggregatedSearchResponse> => {
    const { data } = await apiClient.post<AggregatedSearchResponse>(
      "/api/v1/search",
      {
        origin: params.origin,
        destination: params.destination,
        date_from: params.date_from,
        date_to: params.date_to,
        passengers: params.passengers ?? 1,
        transport_type: params.type ?? "flight",
      }
    );
    return data;
  },

  /** Get available providers grouped by transport type */
  getProviders: async (): Promise<Record<string, ProviderInfo[]>> => {
    const { data } = await apiClient.get<Record<string, ProviderInfo[]>>(
      "/api/v1/search/providers"
    );
    return data;
  },

  /** Trigger background scraping for the specified transport type */
  triggerScraping: async (
    params: SearchParams
  ): Promise<TriggerScrapingResponse> => {
    const { data } = await apiClient.post<TriggerScrapingResponse>(
      "/api/v1/search/trigger",
      {
        origin: params.origin,
        destination: params.destination,
        date_from: params.date_from,
        date_to: params.date_to,
        passengers: params.passengers ?? 1,
        transport_type: params.type ?? "flight",
      }
    );
    return data;
  },
};

// ─── React Query key factory ────────────────────────────────────────────────

export const queryKeys = {
  flights: (params?: SearchParams) =>
    params ? (["flights", params] as const) : (["flights"] as const),
  trains: (params?: SearchParams) =>
    params ? (["trains", params] as const) : (["trains"] as const),
  accommodations: (params?: SearchParams) =>
    params
      ? (["accommodations", params] as const)
      : (["accommodations"] as const),
  search: (params?: SearchParams) =>
    params ? (["search", params] as const) : (["search"] as const),
  providers: () => (["providers"] as const),
  all: ["travel"] as const,
} as const;
