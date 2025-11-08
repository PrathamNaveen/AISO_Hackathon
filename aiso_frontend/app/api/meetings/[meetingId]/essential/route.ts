import { NextResponse } from 'next/server';
import { db } from '../../../../../mock/db';

export async function GET(
  req: Request,
  { params }: { params: { meetingId: string } }
) {
  const meetingId = params.meetingId;
  // try short-term override then long-term prefill
  const short = db.shortTerm[meetingId];
  const pref = db.essential[meetingId] ?? {
    meetingId,
    from: { code: 'LAX', label: 'Los Angeles (LAX)' },
    to: { code: 'AMS', label: 'Amsterdam (AMS)' },
    class: 'business',
    tripType: 'round-trip',
    stayRange: { minDays: 2, maxDays: 5 },
    arriveBeforeDays: { min: 0, max: 1 },
  };

  const merged = { ...pref, ...(short ?? {}) };
  return NextResponse.json(merged);
}
