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
    if (!meetingId || !data) return setError('Missing meeting or data');
    setSaving(true);
    setError(null);
    try {
      // ensure outbound_date is string or null, airports are either object or code
      const payload: any = {
        ...data,
        departure_airport:
          typeof data.departure_airport === 'object'
            ? data.departure_airport
            : { code: String(data.departure_airport || '').toUpperCase() },
        arrival_airport:
          typeof data.arrival_airport === 'object'
            ? data.arrival_airport
            : { code: String(data.arrival_airport || '').toUpperCase() },
        outbound_date: data.outbound_date ? String(data.outbound_date) : null,
        budget: data.budget ?? null,
        currency: data.currency ?? null,
      };
      const res = await confirmEssential(meetingId, payload);
      if (res?.taskId && onConfirmed) onConfirmed(res.taskId);
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
      <div className="bg-[#FFFFFF]/10 rounded-lg p-3 text-white max-w-[240px] w-full">
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
      </div>
    </div>
  );
}