// src/types/api.ts
export type EventItem = {
  id: string;
  title: string;
  location?: string;
  start?: string;
  organizer?: string;
  rawEmailId?: string;
  processed?: boolean;
};

export type Airport = {
  code: string;
  label?: string;
};

export type EssentialInfo = {
  meetingId: string;
  from: Airport;
  to: Airport;
  class: 'economy' | 'premium_economy' | 'business' | 'first';
  tripType: 'one-way' | 'round-trip';
  stayRange: { minDays: number; maxDays: number };
  arriveBeforeDays: { min: number; max: number };
};

export type AgentLogItem = {
  ts: string;
  type: 'step' | 'stage' | 'info' | string;
  text: string;
  meta?: Record<string, any>;
};

export type AgentReasoning = {
  meetingId: string;
  log: AgentLogItem[];
};

export type FlightCandidate = {
  id: string;
  price: number;
  itinerary: string;
  provider?: string;
  details?: Record<string, any>;
};

export type FlightSearchResponse = {
  searchId: string;
  status: 'queued' | 'completed' | 'failed';
  candidates?: FlightCandidate[];
};

export type Booking = {
  bookingId: string;
  status: string;
  confirmationNumber?: string;
  itinerary?: any;
};