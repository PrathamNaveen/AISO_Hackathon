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
    <div style={{ padding: 12, display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ marginBottom: 8 }}>
        <h3 style={{ margin: 0 }}>Assistant (chat)</h3>
        <div style={{ fontSize: 12, color: '#555' }}>Type preferences, then press send. Agent will return flight lists.</div>
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: 8, display: 'flex', flexDirection: 'column', gap: 8 }}>
        {messages.length === 0 && <div style={{ color: '#888' }}>No messages yet. Ask to "find flights" or type preferences.</div>}
        {messages.map((m) => (
          <div key={m.id} style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            <div style={{ alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start', maxWidth: '80%' }}>
              <div style={{ background: m.role === 'user' ? '#3478f6' : '#eee', color: m.role === 'user' ? '#fff' : '#111', padding: 10, borderRadius: 8 }}>
                <div style={{ whiteSpace: 'pre-wrap' }}>{m.text}</div>
              </div>
            </div>

            {m.candidates && m.candidates.length > 0 && (
              <div style={{ display: 'grid', gap: 8, marginTop: 6 }}>
                {m.candidates.map((c) => (
                  <div key={c.id} style={{ background: '#222', color: '#fff', padding: 10, borderRadius: 8 }}>
                    <div style={{ fontWeight: 700 }}>{c.itinerary}</div>
                    <div style={{ fontSize: 13 }}>Provider: {c.provider ?? '—'}</div>
                    <div style={{ fontSize: 13 }}>Price: ${c.price?.toFixed(2)}</div>
                    <div style={{ marginTop: 8, display: 'flex', gap: 8 }}>
                      <button
                        onClick={() => setSelected(c)}
                        style={{ padding: '6px 10px', borderRadius: 8, background: '#ff8c00', color: '#fff', border: 'none' }}
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
        <div style={{ marginTop: 8, background: '#fff', padding: 12, borderRadius: 8 }}>
          <div style={{ fontWeight: 700 }}>{selected.itinerary}</div>
          <div>Price: ${selected.price?.toFixed(2)}</div>
          <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
            <button onClick={() => handleConfirmBooking(selected)} style={{ padding: '8px 12px', borderRadius: 8, background: '#0b6eff', color: '#fff', border: 'none' }}>
              Confirm booking
            </button>
            <button onClick={() => setSelected(null)} style={{ padding: '8px 12px', borderRadius: 8, background: '#ddd', color: '#111', border: 'none' }}>
              Cancel
            </button>
          </div>
        </div>
      )}

      <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
        <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="e.g. morning flights, business class" style={{ flex: 1, padding: 8, borderRadius: 6 }} />
        <button onClick={handleSend} disabled={loading} style={{ padding: '8px 12px', borderRadius: 8, background: '#3478f6', color: '#fff', border: 'none' }}>
          {loading ? 'Searching...' : 'Send'}
        </button>
      </div>

      {bookingResult && (
        <div style={{ marginTop: 8, background: '#e6ffed', padding: 8, borderRadius: 6 }}>
          <div>Booking result: {JSON.stringify(bookingResult)}</div>
        </div>
      )}

      {error && <div style={{ color: 'salmon', marginTop: 8 }}>{error}</div>}
    </div>
  );
}