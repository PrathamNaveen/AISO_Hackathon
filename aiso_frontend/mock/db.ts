// mock/db.ts
// Simple in-memory mock database for local frontend testing.

type Event = {
  id: string;
  title: string;
  location?: string;
  start?: string;
  organizer?: string;
  rawEmailId?: string;
  processed?: boolean;
};

type Essential = {
  meetingId: string;
  from: { code: string; label?: string };
  to: { code: string; label?: string };
  class: 'economy' | 'premium_economy' | 'business' | 'first';
  tripType: 'one-way' | 'round-trip';
  stayRange: { minDays: number; maxDays: number };
  arriveBeforeDays: { min: number; max: number };
};

type Candidate = {
  id: string;
  price: number;
  itinerary: string;
  provider?: string;
  details?: Record<string, any>;
};

type Booking = {
  bookingId: string;
  status: string;
  confirmationNumber?: string;
  itinerary?: any;
};

function randId(prefix = '') {
  return prefix + Math.random().toString(36).slice(2, 9);
}

const now = new Date();

export const db = {
  events: <Event[]>[
    {
      id: 'evt_1',
      title: 'AI - AISO Meetup',
      location: 'Amsterdam',
      start: new Date(now.getTime() + 1000 * 60 * 60 * 24 * 7).toISOString(),
      organizer: 'bob@company.com',
      rawEmailId: 'gmail_msg_abc',
      processed: false,
    },
    {
      id: 'evt_2',
      title: 'Sales Offsite',
      location: 'New York',
      start: new Date(now.getTime() + 1000 * 60 * 60 * 24 * 14).toISOString(),
      organizer: 'sarah@company.com',
      rawEmailId: 'gmail_msg_def',
      processed: false,
    },
  ],

  essential: <Record<string, Essential>>{
    meeting_1: {
      meetingId: 'meeting_1',
      from: { code: 'JFK', label: 'John F. Kennedy (JFK)' },
      to: { code: 'AMS', label: 'Amsterdam (AMS)' },
      class: 'business',
      tripType: 'round-trip',
      stayRange: { minDays: 2, maxDays: 5 },
      arriveBeforeDays: { min: 0, max: 1 },
    },
  },

  // short-term memory per meeting (updated when confirm is called)
  shortTerm: <Record<string, Partial<Essential>>>{},

  reasoning: <Record<string, any[]>>{
    meeting_1: [
      { ts: new Date().toISOString(), type: 'step', text: 'Prefill origin detected: JFK', meta: { confidence: 0.92 } },
    ],
  },

  searches: <Record<string, { searchId: string; candidates: Candidate[] }>>{},

  bookings: <Record<string, Booking>>{},

  createCandidates(meetingId?: string) {
    const base = meetingId === 'meeting_1' ? 'JFK→AMS' : 'LAX→AMS';
    const candidates: Candidate[] = [0, 1, 2].map((i) => ({
      id: randId('f_'),
      price: Math.round((800 + Math.random() * 1200) * 100) / 100,
      itinerary: `${base} — ${i === 0 ? 'non-stop' : i === 1 ? '1 stop' : '2 stops'}`,
      provider: ['AirX', 'FlyFast', 'CloudAir'][i % 3],
      details: { seatsLeft: Math.floor(1 + Math.random() * 6) },
    }));
    return candidates;
  },
  createBooking(candidateId: string) {
    const id = randId('b_');
    const confirmation = randId('C-');
    const booking: Booking = { bookingId: id, status: 'confirmed', confirmationNumber: confirmation, itinerary: { candidateId } };
    db.bookings[id] = booking;
    return booking;
  },
};

export default db;
