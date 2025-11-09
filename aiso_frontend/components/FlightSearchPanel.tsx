// components/FlightSearchPanel.tsx
import React, { useState } from 'react';
import { postFlightSearch, createBooking } from '../lib/api';
import type { FlightCandidate } from '../types/api';

export default function FlightSearchPanel({ meetingId }: { meetingId: string | null }) {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<{ id: string; role: 'user' | 'agent'; text?: string; candidates?: FlightCandidate[] }[]>([]);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState<FlightCandidate | null>(null);
  const [bookingResult, setBookingResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  function push(msg: { id: string; role: 'user' | 'agent'; text?: string; candidates?: FlightCandidate[] }) {
    setMessages((m) => [...m, msg]);
  }

  function uid(prefix = '') {
    return `${prefix}${Math.random().toString(36).slice(2, 9)}`;
  }

  async function handleSend() {
    if (!meetingId) return setError('Select a meeting first');
    if (!input.trim()) return;
    setError(null);
    const text = input.trim();
    push({ id: uid('u_'), role: 'user', text });
    setInput('');
    setLoading(true);

    try {
      const body = { meetingId, preferences: { freeText: text } };
      const res = await postFlightSearch(body);
      // Agent always returns flight list
      push({ id: uid('a_'), role: 'agent', text: `Found ${res.candidates?.length ?? 0} option(s)`, candidates: res.candidates ?? [] });
    } catch (err: any) {
      setError(String(err));
      push({ id: uid('a_'), role: 'agent', text: 'Sorry, search failed.' });
    } finally {
      setLoading(false);
    }
  }

  async function handleConfirmBooking(candidate: FlightCandidate) {
    if (!meetingId) return setError('Missing meeting');
    setError(null);
    try {
      const payload = { meetingId, candidateId: candidate.id };
      const booking = await createBooking(payload);
      setBookingResult(booking);
      push({ id: uid('a_'), role: 'agent', text: `Booking created: ${booking.confirmationNumber ?? booking.bookingId}` });
      setSelected(null);
    } catch (err: any) {
      setError(String(err));
    }
  }

  return (
    <div className="p-3 flex flex-col h-full">
      <div className="mb-2">
        <h3 className="m-0 text-lg font-medium">Assistant (chat)</h3>
        <div className="text-sm text-gray-500">Type preferences, then press send. Agent will return flight lists.</div>
      </div>

      <div className="flex-1 overflow-auto p-2 flex flex-col gap-2">
        {messages.length === 0 && <div className="text-gray-500">No messages yet. Ask to "find flights" or type preferences.</div>}
        {messages.map((m) => (
          <div key={m.id} className="flex flex-col gap-2">
            <div className={`${m.role === 'user' ? 'self-end' : 'self-start'} max-w-[80%]`}>
              <div className={`${m.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-black'} p-3 rounded-lg whitespace-pre-wrap`}>
                <div>{m.text}</div>
              </div>
            </div>

            {m.candidates && m.candidates.length > 0 && (
              <div className="grid gap-2 mt-2">
                {m.candidates.map((c) => (
                  <div key={c.id} className="bg-[#222] text-white p-3 rounded-lg">
                    <div className="font-semibold">{c.itinerary}</div>
                    <div className="text-sm">Provider: {c.provider ?? '—'}</div>
                    <div className="text-sm">Price: ${c.price?.toFixed(2)}</div>
                    <div className="mt-3 flex gap-2">
                      <button
                        onClick={() => setSelected(c)}
                        className="px-3 py-2 rounded-md bg-orange-500 hover:bg-orange-600 text-white"
                      >
                        Book this
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {selected && (
        <div className="mt-2 bg-white p-3 rounded-lg shadow">
          <div className="font-semibold">{selected.itinerary}</div>
          <div>Price: ${selected.price?.toFixed(2)}</div>
          <div className="flex gap-2 mt-3">
            <button onClick={() => handleConfirmBooking(selected)} className="px-3 py-2 rounded-md bg-blue-600 text-white">
              Confirm booking
            </button>
            <button onClick={() => setSelected(null)} className="px-3 py-2 rounded-md bg-gray-200 text-gray-800">
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className="flex gap-2 mt-3">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="e.g. morning flights, business class"
          className="flex-1 p-2 rounded-md border border-gray-200"
        />
        <button onClick={handleSend} disabled={loading} className="px-3 py-2 rounded-md bg-blue-600 text-white disabled:opacity-60">
          {loading ? 'Searching...' : 'Send'}
        </button>
      </div>

      {bookingResult && (
        <div className="mt-3 bg-green-50 p-2 rounded-md text-sm">
          <div>Booking result: {JSON.stringify(bookingResult)}</div>
        </div>
      )}

      {error && <div className="text-red-500 mt-2">{error}</div>}
    </div>
  );
}