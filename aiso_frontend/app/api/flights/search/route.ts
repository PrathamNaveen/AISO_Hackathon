import { NextResponse } from 'next/server';
import { db } from '../../../../mock/db';

export async function POST(req: Request) {
  const body = await req.json();
  const meetingId = body?.meetingId ?? null;
  const candidates = db.createCandidates(meetingId ?? undefined);
  const searchId = 's_' + Math.random().toString(36).slice(2, 9);
  db.searches[searchId] = { searchId, candidates };
  return NextResponse.json({ searchId, status: 'completed', candidates });
}
