// src/components/EssentialInfo.tsx
import React, { useEffect, useState } from 'react';
import type { EssentialInfo } from '../types/api';
import { fetchEssential, confirmEssential } from '../lib/api';

export default function EssentialInfo({
  meetingId,
  onConfirmed,
}: {
  meetingId: string | null;
  onConfirmed?: (taskId: string) => void;
}) {
  const [data, setData] = useState<EssentialInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!meetingId) {
      setData(null);
      return;
    }
    setLoading(true);
    fetchEssential(meetingId)
      .then((d) => setData(d))
      .catch((err) => setError(String(err)))
      .finally(() => setLoading(false));
  }, [meetingId]);

  function update<K extends keyof EssentialInfo>(key: K, value: any) {
    setData((prev) => (prev ? { ...prev, [key]: value } : prev));
  }

  function updateNested(path: string, value: any) {
    // simple helper for nested objects (stayRange, arriveBeforeDays, from/to)
    setData((prev) => {
      if (!prev) return prev;
      const copy = JSON.parse(JSON.stringify(prev));
      const parts = path.split('.');
      let cur: any = copy;
      for (let i = 0; i < parts.length - 1; i++) {
        cur = cur[parts[i]];
      }
      cur[parts[parts.length - 1]] = value;
      return copy;
    });
  }

  async function handleConfirm() {
    if (!meetingId || !data) return;
    setSaving(true);
    setError(null);
    try {
      const res = await confirmEssential(meetingId, data as any);
      if (res?.taskId && onConfirmed) onConfirmed(res.taskId);
      // show brief feedback (you may wire this to agent SSE)
    } catch (err: any) {
      setError(String(err));
    } finally {
      setSaving(false);
    }
  }

  if (!meetingId) return <div style={{ padding: 12 }}>Select a meeting to view essential info</div>;
  if (loading || !data) return <div style={{ padding: 12 }}>Loading essential info...</div>;

  return (
    <div style={{ padding: 12 }}>
      <div style={{ background: '#666', borderRadius: 12, padding: 12, color: '#fff' }}>
        <h3 style={{ marginTop: 0 }}>Essential information</h3>

        <div style={{ marginBottom: 8 }}>
          <label style={{ fontSize: 12 }}>From</label>
          <input
            value={data.from?.code ?? ''}
            onChange={(e) => updateNested('from.code', e.target.value)}
            style={{ width: '100%', padding: 8, borderRadius: 6, marginTop: 4 }}
          />
        </div>

        <div style={{ marginBottom: 8 }}>
          <label style={{ fontSize: 12 }}>To</label>
          <input
            value={data.to?.code ?? ''}
            onChange={(e) => updateNested('to.code', e.target.value)}
            style={{ width: '100%', padding: 8, borderRadius: 6, marginTop: 4 }}
          />
        </div>

        <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
          <div style={{ flex: 1 }}>
            <label style={{ fontSize: 12 }}>Class</label>
            <select
              value={data.class}
              onChange={(e) => update('class', e.target.value)}
              style={{ width: '100%', padding: 8, borderRadius: 6, marginTop: 4 }}
            >
              <option value="economy">Economy</option>
              <option value="premium_economy">Premium Economy</option>
              <option value="business">Business</option>
              <option value="first">First</option>
            </select>
          </div>

          <div style={{ flex: 1 }}>
            <label style={{ fontSize: 12 }}>Trip type</label>
            <select
              value={data.tripType}
              onChange={(e) => update('tripType', e.target.value)}
              style={{ width: '100%', padding: 8, borderRadius: 6, marginTop: 4 }}
            >
              <option value="round-trip">Round-trip</option>
              <option value="one-way">One-way</option>
            </select>
          </div>
        </div>

        <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
          <div style={{ flex: 1 }}>
            <label style={{ fontSize: 12 }}>Stay range (days)</label>
            <div style={{ display: 'flex', gap: 8 }}>
              <input
                type="number"
                value={data.stayRange.minDays}
                onChange={(e) => updateNested('stayRange.minDays', Number(e.target.value))}
                style={{ flex: 1, padding: 8, borderRadius: 6 }}
              />
              <input
                type="number"
                value={data.stayRange.maxDays}
                onChange={(e) => updateNested('stayRange.maxDays', Number(e.target.value))}
                style={{ flex: 1, padding: 8, borderRadius: 6 }}
              />
            </div>
          </div>

          <div style={{ flex: 1 }}>
            <label style={{ fontSize: 12 }}>Arrive before (days)</label>
            <div style={{ display: 'flex', gap: 8 }}>
              <input
                type="number"
                value={data.arriveBeforeDays.min}
                onChange={(e) => updateNested('arriveBeforeDays.min', Number(e.target.value))}
                style={{ flex: 1, padding: 8, borderRadius: 6 }}
              />
              <input
                type="number"
                value={data.arriveBeforeDays.max}
                onChange={(e) => updateNested('arriveBeforeDays.max', Number(e.target.value))}
                style={{ flex: 1, padding: 8, borderRadius: 6 }}
              />
            </div>
          </div>
        </div>

        {error && <div style={{ color: 'salmon', marginBottom: 8 }}>{error}</div>}

        <button
          onClick={handleConfirm}
          disabled={saving}
          style={{
            marginTop: 8,
            padding: '8px 14px',
            background: '#3478f6',
            color: '#fff',
            borderRadius: 8,
            border: 'none',
            cursor: 'pointer',
          }}
        >
          {saving ? 'Saving...' : 'Confirm'}
        </button>
      </div>
    </div>
  );
}