import { NextResponse } from 'next/server';
import { db } from '../../../mock/db';

export async function POST(req: Request) {
  const body = await req.json();
  const candidateId = body?.candidateId;
  if (!candidateId) return NextResponse.json({ error: 'missing candidateId' }, { status: 400 });
  const booking = db.createBooking(candidateId);
  return NextResponse.json(booking, { status: 201 });
}
