// aiso_frontend/lib/api.ts
// Centralized API client that can talk to local Next mock routes or a remote backend
import type {
  EventItem,
  EssentialInfo,
  AgentReasoning,
  FlightSearchResponse,
  Booking,
} from '../types/api';

const USE_MOCK = (process.env.NEXT_PUBLIC_USE_MOCK ?? 'true') === 'true';
const EXTERNAL_BASE = process.env.NEXT_PUBLIC_API_BASE ?? ''; // e.g. https://api.example.com

// baseUrl: if using mock => '' so fetch('/api/xxx') hits local Next API routes.
// if using real backend => EXTERNAL_BASE (must not end with a trailing slash)
const baseUrl = USE_MOCK ? '' : (EXTERNAL_BASE.replace(/\/$/, '') || '');

// helper to build url: returns '/api/...' for mock, or `${EXTERNAL_BASE}/api/...` for real backend
function apiUrl(path: string) {
  // path should be like '/api/events' (leading slash)
  return baseUrl ? `${baseUrl}${path}` : path;
}

const withCredentials = (opts: RequestInit = {}) => ({
  ...opts,
  headers: {
    'Content-Type': 'application/json',
    ...(opts.headers || {}),
  },
  credentials: 'include' as RequestCredentials,
});

export async function fetchEvents(): Promise<EventItem[]> {
  const res = await fetch(apiUrl('/api/events'), withCredentials());
  if (!res.ok) throw new Error(`fetchEvents: ${res.status}`);
  return res.json();
}

export async function fetchEssential(meetingId: string): Promise<EssentialInfo> {
  const res = await fetch(apiUrl(`/api/meetings/${meetingId}/essential`), withCredentials());
  if (!res.ok) throw new Error(`fetchEssential: ${res.status}`);
  return res.json();
}

export async function confirmEssential(
  meetingId: string,
  payload: Partial<EssentialInfo>
): Promise<{ taskId: string; status: string }> {
  const res = await fetch(
    apiUrl(`/api/meetings/${meetingId}/essential/confirm`),
    withCredentials({
      method: 'POST',
      body: JSON.stringify(payload),
    })
  );
  if (res.status === 202) return res.json();
  if (!res.ok) throw new Error(`confirmEssential: ${res.status}`);
  return res.json();
}

export async function fetchReasoning(meetingId: string): Promise<AgentReasoning> {
  const res = await fetch(apiUrl(`/api/agent/reasoning/${meetingId}`), withCredentials());
  if (!res.ok) throw new Error(`fetchReasoning: ${res.status}`);
  return res.json();
}

export async function postFlightSearch(body: Record<string, any>): Promise<FlightSearchResponse> {
  const res = await fetch(apiUrl('/api/flights/search'), withCredentials({ method: 'POST', body: JSON.stringify(body) }));
  if (!res.ok) throw new Error(`postFlightSearch: ${res.status}`);
  return res.json();
}

export async function fetchBooking(id: string): Promise<Booking> {
  const res = await fetch(apiUrl(`/api/bookings/${id}`), withCredentials());
  if (!res.ok) throw new Error(`fetchBooking: ${res.status}`);
  return res.json();
}

export async function createBooking(body: Record<string, any>): Promise<Booking> {
  const res = await fetch(apiUrl('/api/bookings'), withCredentials({ method: 'POST', body: JSON.stringify(body) }));
  if (!res.ok) throw new Error(`createBooking: ${res.status}`);
  return res.json();
}