// src/components/EssentialInfo.tsx
import React, { useEffect, useState } from 'react';
import type { EssentialInfo } from '../types/api';
import { fetchEssential } from '../lib/api';

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
  const [result, setResult] = useState<any>(null);

  useEffect(() => {
    if (!meetingId) {
      setData(null);
      return;
    }
    setLoading(true);
    fetchEssential(meetingId)
      .then((d: any) => {
        // normalize legacy shapes to new keys
        if (d?.departure_airport || d?.departure_airport === '') {
          setData({
            meetingId: d.meetingId ?? meetingId,
            departure_airport: d.departure_airport ?? d.from?.code ?? '',
            arrival_airport: d.arrival_airport ?? d.to?.code ?? '',
            class: (d.class ?? d.travelClass) ?? 'economy',
            trip_type: d.trip_type ?? d.tripType ?? 'round-trip',
            days: d.days ?? d.stayRange?.maxDays ?? 3,
            currency: d.currency ?? null,
            budget: d.budget ?? null,
            outbound_date: d.outbound_date ?? null,
          });
        } else {
          // legacy shape
          setData({
            meetingId: d?.meetingId ?? meetingId,
            departure_airport: d?.from?.code ?? '',
            arrival_airport: d?.to?.code ?? '',
            class: d?.class ?? 'economy',
            trip_type: d?.tripType ?? 'round-trip',
            days: d?.stayRange?.maxDays ?? 3,
            currency: d?.currency ?? null,
            budget: d?.budget ?? null,
            outbound_date: d?.outbound_date ?? null,
          });
        }
      })
      .catch((err) => setError(String(err)))
      .finally(() => setLoading(false));
  }, [meetingId]);

  function update<K extends keyof EssentialInfo>(key: K, value: any) {
    setData((prev) => (prev ? { ...prev, [key]: value } : prev));
  }

  async function handleConfirm() {
    if (!data) return;
    setSaving(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/preferences', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          departure_airport: data.from?.code,
          arrival_airport: data.to?.code,
          date: data.date ?? '2025-12-25',
          days: data.stayRange?.maxDays ?? 10,
          currency: 'USD',
          budget: data.budget ?? 9999,
        }),
      });

      const res = await response.json();
      if (!response.ok) throw new Error(res.detail || 'Server error');

      setResult(res.data);
      if (onConfirmed) onConfirmed('task_done');
    } catch (err: any) {
      setError(String(err));
    } finally {
      setSaving(false);
    }
  }

  if (!meetingId) return <div className="p-2 text-sm">Select a meeting to view essential info</div>;
  if (loading || !data) return <div className="p-2 text-sm">Loading essential info...</div>;

  return (
    <div className="p-2">
      <div className="bg-[#FFFFFF]/20 rounded-lg p-3 text-white w-full">
        <h3 className="text-lg font-semibold text-center mb-3">Essential information</h3>

        <div className="space-y-2 text-sm">
          <div>
            <div className="text-gray-300 font-semibold text-[14px]">Departure (IATA)</div>
            <input
              value={(data.departure_airport as any)?.code ?? (data.departure_airport as any) ?? ''}
              onChange={(e) =>
                update(
                  'departure_airport',
                  { code: e.target.value.toUpperCase(), label: e.target.value.toUpperCase() }
                )
              }
              className="w-full p-1 rounded-md mt-1 text-black text-sm"
            />
          </div>

          <div>
            <div className="text-gray-300 font-semibold text-[14px]">Arrival (IATA)</div>
            <input
              value={(data.arrival_airport as any)?.code ?? (data.arrival_airport as any) ?? ''}
              onChange={(e) =>
                update(
                  'arrival_airport',
                  { code: e.target.value.toUpperCase(), label: e.target.value.toUpperCase() }
                )
              }
              className="w-full p-1 rounded-md mt-1 text-black text-sm"
            />
          </div>

          <div>
            <div className="text-gray-300 font-semibold text-[14px]">Class</div>
            <select
              value={data.class}
              onChange={(e) => update('class', e.target.value as any)}
              className="w-full p-1 rounded-md mt-1 text-black text-sm"
            >
              <option value="economy">Economy</option>
              <option value="premium_economy">Premium Economy</option>
              <option value="business">Business</option>
              <option value="first">First</option>
            </select>
          </div>

          <div>
            <div className="text-gray-300 font-semibold text-[14px]">Trip type</div>
            <select
              value={data.trip_type ?? (data as any).tripType}
              onChange={(e) => update('trip_type', e.target.value as any)}
              className="w-full p-1 rounded-md mt-1 text-black text-sm"
            >
              <option value="round-trip">Round-trip</option>
              <option value="one-way">One-way</option>
            </select>
          </div>

          <div className="flex gap-2">
            <div className="flex-1">
              <div className="text-gray-300 text-sm font-semibold">Days</div>
              <input
                type="number"
                value={data.days ?? 3}
                onChange={(e) => update('days', Number(e.target.value))}
                className="w-full p-1 rounded-md text-black text-sm"
              />
            </div>

            <div className="flex-1">
              <div className="text-gray-300 text-sm font-semibold">Budget</div>
              <input
                type="number"
                value={data.budget ?? ''}
                onChange={(e) => update('budget', e.target.value ? Number(e.target.value) : null)}
                className="w-full p-1 rounded-md text-black text-sm"
              />
            </div>
          </div>

          <div>
            <div className="text-gray-300 text-sm font-semibold">Currency</div>
            <input
              value={data.currency ?? ''}
              onChange={(e) => update('currency', e.target.value ?? null)}
              className="w-full p-1 rounded-md mt-1 text-black text-sm"
            />
          </div>

          <div>
            <div className="text-gray-300 text-sm font-semibold">Outbound date</div>
            <input
              type="date"
              value={data.outbound_date ?? ''}
              onChange={(e) => update('outbound_date', e.target.value ?? null)}
              className="w-full p-1 rounded-md mt-1 text-black text-sm"
            />
          </div>
        </div>

        {error && <div className="text-rose-300 mt-2 text-sm">{error}</div>}

        <div className="mt-3 flex justify-center">
          <button
            onClick={handleConfirm}
            disabled={saving}
            className={`px-4 py-1 rounded-full text-white text-sm ${saving ? 'bg-gray-500 cursor-not-allowed' : 'bg-[#8D0101]'}`}
          >
            {saving ? 'Saving...' : 'Confirm'}
          </button>
        </div>

        {result && (
          <div className="mt-4 bg-white/10 p-2 rounded text-sm text-gray-100">
            <div className="font-semibold mb-1">Backend Response:</div>
            <pre className="text-xs whitespace-pre-wrap">{JSON.stringify(result, null, 2)}</pre>
          </div>
        )}
      </div>
    </div>
  );
}
