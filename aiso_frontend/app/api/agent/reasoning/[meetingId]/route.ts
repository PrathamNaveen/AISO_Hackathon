import { NextResponse } from 'next/server';
import { db } from '../../../../../mock/db';

export async function GET(req: Request, { params }: { params: { meetingId: string } }) {
  const meetingId = params.meetingId;
  const log = db.reasoning[meetingId] ?? [];
  return NextResponse.json({ meetingId, log });
}
