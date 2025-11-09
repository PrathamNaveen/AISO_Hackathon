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
  const [essentialOpen, setEssentialOpen] = useState<boolean>(false); // collapsed by default
  const [leftOpen, setLeftOpen] = useState<boolean>(true); // left column collapsecollapsed by default

  return (
    <div className="flex h-screen">
      <div className={`relative bg-[#222] text-white flex flex-col overflow-hidden transition-all duration-200 ${leftOpen ? 'w-80' : 'w-16'}`}>
        {/* toggle button on the right edge of left column */}
        <button
          aria-label="Toggle left panel"
          onClick={() => setLeftOpen((s) => !s)}
          className="absolute right-3 top-4 z-10 w-6 h-6 bg-[#444] rounded-full flex items-center justify-center text-white shadow"
        >
          {leftOpen ? '<' : '>'}
        </button>

        <div className="px-3">
          <h2 className={`text-[40px] font-semibold py-[10px] transition-opacity duration-200 ${leftOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}>Meetings</h2>
        </div>

        <div className="flex-1 px-3 overflow-auto">
          <EventsList onSelect={(e) => setSelected(e)} />
        </div>

        <div className="p-3">
          <button className="w-full px-3 py-2 rounded-xl bg-[#444] text-white">Log out</button>
        </div>
      </div>

      {/* Middle column (collapsible) */}
      <div
        className={`relative bg-[#353232]  text-white transition-all duration-200 flex flex-col ${
          essentialOpen ? 'w-80' : 'w-16'
        }`}
      >
        {/* toggle button on the left edge */}
        <button
          aria-label="Toggle essential panel"
          onClick={() => setEssentialOpen((s) => !s)}
          className="absolute right-3 top-4 z-10 w-6 h-6 bg-[#444] rounded-full flex items-center justify-center text-white shadow"
        >
          {essentialOpen ? '<' : '>'}
        </button>

        {/* content - hidden when collapsed */}
        <div className={`${essentialOpen ? 'p-3 block' : 'hidden'}`}>
          <EssentialInfo
            meetingId={selected?.id ?? null}
            onConfirmed={(taskId) => {
              setAgentTaskId(taskId);
            }}
          />
        </div>
      </div>

      {/* Right column */}
      <div className="flex-1 bg-gray-100 overflow-auto">
        <div className="p-3">
          <h2 className="text-[30px] text-center font-semibold">Tell us more about your preference</h2>
        </div>

        <div className="p-3">
          <FlightSearchPanel meetingId={selected?.id ?? null} />
        </div>
      </div>
    </div>
  );
}