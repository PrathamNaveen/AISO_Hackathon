// src/app/dashboard/page.tsx
'use client';
import React, { useState } from 'react';
import EventsList from '../../components/EventList';
import EssentialInfo from '../../components/EssentialInfo';
import FlightSearchPanel from '../../components/FlightSearchPanel';
import type { EventItem } from '../../types/api';
export default function DashboardPage() {
  const [selected, setSelected] = useState<EventItem | null>(null);
  const [agentTaskId, setAgentTaskId] = useState<string | null>(null);

  return (
    <div className="flex h-screen gap-3">
      {/* Left column */}
      <div className="w-80 bg-[#222] text-white overflow-auto pt-3">
        <div className="px-3">
          <h2 className="text-[40px] font-semibold py-[10px]">Meetings</h2>
        </div>
        <EventsList onSelect={(e) => setSelected(e)} />
        <div className="p-3">
          <button className="px-3 py-2 rounded-xl bg-[#444] text-white">Log out</button>
        </div>
      </div>

      {/* Middle column */}
      <div className="flex-1 bg-[#3a3636] text-white overflow-auto">
        <div className="p-3">
          <EssentialInfo
            meetingId={selected?.id ?? null}
            onConfirmed={(taskId) => {
              setAgentTaskId(taskId);
            }}
          />
        </div>

      </div>

      {/* Right column */}
      <div className="w-[520px] bg-gray-100 overflow-auto">
        <div className="p-3">
          <h2 className="text-xl font-semibold">Tell us more about your preference</h2>
          {/* You can add a small chat or preference UI here */}
        </div>

        <div className="p-3">
          <FlightSearchPanel meetingId={selected?.id ?? null} />
        </div>

      </div>
    </div>
  );
}