// src/components/ReasoningPanel.tsx
import React, { useEffect, useState } from 'react';
import type { AgentReasoning } from '../types/api';
import { fetchReasoning } from '../lib/api';

export default function ReasoningPanel({ meetingId }: { meetingId: string | null }) {
  const [reasoning, setReasoning] = useState<AgentReasoning | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!meetingId) {
      setReasoning(null);
      return;
    }
    setLoading(true);
    fetchReasoning(meetingId)
      .then((r) => setReasoning(r))
      .catch((err) => setError(String(err)))
      .finally(() => setLoading(false));
  }, [meetingId]);

  // Optional: use SSE for live reasoning updates. (Backend: /api/agent/reasoning/stream?meetingId=...)
  // if you implement SSE, create an EventSource and append new events to reasoning.log

  if (!meetingId) return <div style={{ padding: 12 }}>Select a meeting to see agent reasoning</div>;
  if (loading || !reasoning) return <div style={{ padding: 12 }}>Loading reasoning...</div>;
  if (error) return <div style={{ padding: 12, color: 'salmon' }}>Error: {error}</div>;

  return (
    <div style={{ padding: 12 }}>
      <div style={{ background: '#666', color: '#fff', padding: 12, borderRadius: 12 }}>
        <h3 style={{ marginTop: 0 }}>AI Agent Reasoning</h3>
        <div style={{ maxHeight: 300, overflow: 'auto' }}>
          {reasoning.log.map((item, idx) => (
            <div key={idx} style={{ marginBottom: 8 }}>
              <div style={{ fontSize: 12, color: '#ddd' }}>
                {new Date(item.ts).toLocaleString()} • {item.type}
              </div>
              <div>{item.text}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}