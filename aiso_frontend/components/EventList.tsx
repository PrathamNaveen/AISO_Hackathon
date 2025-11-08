// src/components/EventsList.tsx
import React, { useEffect, useState } from 'react';
import type { EventItem } from '../types/api';
import { fetchEvents } from '../lib/api';

export default function EventsList({ onSelect }: { onSelect: (evt: EventItem) => void }) {
  const [events, setEvents] = useState<EventItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    fetchEvents()
      .then((data) => {
        if (!mounted) return;
        setEvents(data);
      })
      .catch((err) => {
        if (!mounted) return;
        setError(String(err));
      })
      .finally(() => mounted && setLoading(false));
    return () => {
      mounted = false;
    };
  }, []);

  if (loading) return <div style={{ padding: 12 }}>Loading events...</div>;
  if (error) return <div style={{ padding: 12, color: 'crimson' }}>Error: {error}</div>;
  if (events.length === 0) return <div style={{ padding: 12 }}>No events found</div>;

  return (
    <div style={{ padding: 12 }}>
      {events.map((e) => (
        <div
          key={e.id}
          onClick={() => onSelect(e)}
          style={{
            cursor: 'pointer',
            marginBottom: 12,
            background: '#2c2c2c',
            color: '#fff',
            padding: 12,
            borderRadius: 10,
          }}
        >
          <div style={{ fontWeight: 700 }}>{e.title}</div>
          <div style={{ fontSize: 12 }}>{`LOCATION: ${e.location ?? '—'}`}</div>
          <div style={{ fontSize: 12 }}>{`Time: ${e.start ? new Date(e.start).toLocaleString() : '—'}`}</div>
        </div>
      ))}
    </div>
  );
}