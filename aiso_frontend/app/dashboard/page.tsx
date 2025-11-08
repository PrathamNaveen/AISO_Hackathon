// src/app/dashboard/page.tsx
'use client';
import React, { useState } from 'react';
import EventsList from '../../components/EventList';
import EssentialInfo from '../../components/EssentialInfo';
import ReasoningPanel from '../../components/ReasoningPanel';
import FlightSearchPanel from '../../components/FlightSearchPanel';
import type { EventItem } from '../../types/api';
export default function DashboardPage() {
  const [selected, setSelected] = useState<EventItem | null>(null);
  const [agentTaskId, setAgentTaskId] = useState<string | null>(null);

  return (
    <div style={{ display: 'flex', height: '100vh', gap: 12 }}>
      {/* Left column */}
      <div style={{ width: 320, background: '#222', color: '#fff', overflow: 'auto', paddingTop: 12 }}>
        <div style={{ padding: '0 12px' }}>
          <h2>Meetings</h2>
        </div>
        <EventsList onSelect={(e) => setSelected(e)} />
        <div style={{ padding: 12 }}>
          <button style={{ padding: '8px 12px', borderRadius: 12, background: '#444', color: '#fff' }}>Log out</button>
        </div>
      </div>

      {/* Middle column */}
      <div style={{ flex: 1, background: '#3a3636', color: '#fff', overflow: 'auto' }}>
        <div style={{ padding: 12 }}>
          <EssentialInfo
            meetingId={selected?.id ?? null}
            onConfirmed={(taskId) => {
              setAgentTaskId(taskId);
            }}
          />
        </div>

        <div style={{ padding: 12 }}>
          <ReasoningPanel meetingId={selected?.id ?? null} />
        </div>
      </div>

      {/* Right column */}
      <div style={{ width: 520, background: '#f1f1f1', overflow: 'auto' }}>
        <div style={{ padding: 12 }}>
          <h2>Tell us more about your preference</h2>
          {/* You can add a small chat or preference UI here */}
        </div>

        <div style={{ padding: 12 }}>
          <FlightSearchPanel meetingId={selected?.id ?? null} />
        </div>

        {/* <div style={{ padding: 12 }}>
          <div style={{ background: '#ddd', padding: 12, borderRadius: 12 }}>
            <h3>Confirm details</h3>
            <button style={{ padding: '8px 12px', borderRadius: 8, background: '#3478f6', color: '#fff' }}>
              Confirm
            </button>
          </div>
        </div> */}
      </div>
    </div>
  );
}