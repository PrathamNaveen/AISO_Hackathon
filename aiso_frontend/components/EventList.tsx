// src/components/EventsList.tsx
import React, { useEffect, useState } from 'react';
import type { EventItem } from '../types/api';

interface EventsListProps {
  onSelect: (evt: EventItem) => void;
}

export default function EventsList({ onSelect }: EventsListProps) {
  const [events, setEvents] = useState<EventItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const userId = '3';
  const BASE_URL = "http://localhost:8000"; // replace with your FastAPI URL


  useEffect(() => {
    let mounted = true;

    const fetchEvents = async () => {
      try {
        const res = await fetch(`${BASE_URL}/api/invitations?user_id=userId}`);
        
        if (!res.ok) throw new Error(`Failed to fetch invitations: ${res.statusText}`);
        const data: EventItem[] = await res.json();
        if (!mounted) return;
        setEvents(data);
      } catch (err: any) {
        if (!mounted) return;
        setError(err.message || "Unknown error");
      } finally {
        if (mounted) setLoading(false);
      }
    };

    fetchEvents();

    return () => {
      mounted = false;
    };
  }, []); // no dependency, runs once

  if (loading) return <div className="p-3">Loading events...</div>;
  if (error) return <div className="p-3 text-red-600">Error: {error}</div>;
  if (events.length === 0) return <div className="p-3">No events found</div>;

  return (
    <div className="p-3">
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
