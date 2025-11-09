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
    } catch (err: any) {
      setError(String(err));
    } finally {
      setSaving(false);
    }
  }

  if (!meetingId) return <div className="p-3">Select a meeting to view essential info</div>;
  if (loading || !data) return <div className="p-3">Loading essential info...</div>;

  return (
    <div className="p-3">
      <div className="bg-gray-600 rounded-lg p-4 text-white">
        <h3 className="m-0 mb-3 text-lg font-semibold">Essential information</h3>

        <div className="mb-3">
          <label className="text-sm block">From</label>
          <input
            value={data.from?.code ?? ''}
            onChange={(e) => updateNested('from.code', e.target.value)}
            className="w-full p-2 rounded-md mt-1 text-black"
          />
        </div>

        <div className="mb-3">
          <label className="text-sm block">To</label>
          <input
            value={data.to?.code ?? ''}
            onChange={(e) => updateNested('to.code', e.target.value)}
            className="w-full p-2 rounded-md mt-1 text-black"
          />
        </div>

        <div className="flex gap-3 mb-3">
          <div className="flex-1">
            <label className="text-sm block">Class</label>
            <select
              value={data.class}
              onChange={(e) => update('class', e.target.value)}
              className="w-full p-2 rounded-md mt-1 text-black"
            >
              <option value="economy">Economy</option>
              <option value="premium_economy">Premium Economy</option>
              <option value="business">Business</option>
              <option value="first">First</option>
            </select>
          </div>

          <div className="flex-1">
            <label className="text-sm block">Trip type</label>
            <select
              value={data.tripType}
              onChange={(e) => update('tripType', e.target.value)}
              className="w-full p-2 rounded-md mt-1 text-black"
            >
              <option value="round-trip">Round-trip</option>
              <option value="one-way">One-way</option>
            </select>
          </div>
        </div>

        <div className="flex gap-3 mb-3">
          <div className="flex-1">
            <label className="text-sm block">Stay range (days)</label>
            <div className="flex gap-2 mt-1">
              <input
                type="number"
                value={data.stayRange.minDays}
                onChange={(e) => updateNested('stayRange.minDays', Number(e.target.value))}
                className="flex-1 p-2 rounded-md text-black"
              />
              <input
                type="number"
                value={data.stayRange.maxDays}
                onChange={(e) => updateNested('stayRange.maxDays', Number(e.target.value))}
                className="flex-1 p-2 rounded-md text-black"
              />
            </div>
          </div>

          <div className="flex-1">
            <label className="text-sm block">Arrive before (days)</label>
            <div className="flex gap-2 mt-1">
              <input
                type="number"
                value={data.arriveBeforeDays.min}
                onChange={(e) => updateNested('arriveBeforeDays.min', Number(e.target.value))}
                className="flex-1 p-2 rounded-md text-black"
              />
              <input
                type="number"
                value={data.arriveBeforeDays.max}
                onChange={(e) => updateNested('arriveBeforeDays.max', Number(e.target.value))}
                className="flex-1 p-2 rounded-md text-black"
              />
            </div>
          </div>
        </div>

        {error && <div className="text-red-300 mb-3">{error}</div>}

        <button
          onClick={handleConfirm}
          disabled={saving}
          className={`mt-2 px-4 py-2 rounded-md text-white ${saving ? 'bg-gray-500 cursor-not-allowed' : 'bg-blue-600'}`}
        >
          {saving ? 'Saving...' : 'Confirm'}
        </button>
      </div>
    </div>
  );
}