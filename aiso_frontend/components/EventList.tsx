"use client";
import React, { useEffect, useState } from 'react';
import type { EventItem } from '../types/api';

interface EventsListProps {
  onSelect: (evt: EventItem) => void;
}

export default function EventsList({ onSelect }: EventsListProps) {
  const [events, setEvents] = useState<EventItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const BASE_URL = "http://localhost:8000";
  const userId = localStorage.getItem('userId');
  console.log(userId);

  useEffect(() => {
    let mounted = true;

    const fetchEvents = async () => {
      try {
        // Fixed: removed extra backtick and userId literal
        const res = await fetch(`${BASE_URL}/api/invitations/${userId}`);
        
        if (!res.ok) {
          throw new Error(`Failed to fetch invitations: ${res.statusText}`);
        }
        
        const data = await res.json();
        
        // Guard against null/undefined response
        if (!mounted) return;
        
        // Ensure data is an array
        if (Array.isArray(data)) {
          setEvents(data);
        } else {
          setEvents([]);
          setError("Invalid response format");
        }
      } catch (err: any) {
        if (!mounted) return;
        console.error("Fetch error:", err);
        setError(err.message || "Unknown error");
        setEvents([]); // Set to empty array on error
      } finally {
        if (mounted) setLoading(false);
      }
    };

    fetchEvents();

    return () => {
      mounted = false;
    };
  }, [userId]);

  if (loading) {
    return <div className="p-3 text-gray-400">Loading events...</div>;
  }
  
  if (error) {
    return (
      <div className="p-3">
        <div className="text-red-600 mb-2">Error: {error}</div>
        <button 
          onClick={() => window.location.reload()} 
          className="text-sm text-blue-500 underline"
        >
          Retry
        </button>
      </div>
    );
  }
  
  if (!events || events.length === 0) {
    return <div className="p-3 text-gray-400">No events found</div>;
  }

  return (
    <div className="p-3">
      {events.map((e) => (
        <div
          key={e.id}
          onClick={() => onSelect(e)}
          className="cursor-pointer mb-3 bg-gray-800 text-white p-3 rounded-lg hover:bg-gray-700 transition-colors"
        >
          <div className="font-bold">{e.title}</div>
          <div className="text-xs mt-1">LOCATION: {e.location ?? '—'}</div>
          <div className="text-xs">
            Time: {e.start ? new Date(e.start).toLocaleString() : '—'}
          </div>
        </div>
      ))}
    </div>
  );
}