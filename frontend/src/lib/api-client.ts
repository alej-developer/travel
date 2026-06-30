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

  /** Trigger background scraping for all providers */
  triggerScraping: async (params: SearchParams): Promise<{ task_id: string }> => {
    const { data } = await apiClient.post<{ task_id: string }>(
      "/api/v1/scrape",
      params
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
  all: ["travel"] as const,
} as const;
