import { NextResponse } from 'next/server';
import { db } from '../../../../mock/db';

export async function GET(req: Request, { params }: { params: { id: string } }) {
  const id = params.id;
  const booking = db.bookings[id];
  if (!booking) return NextResponse.json({ error: 'not found' }, { status: 404 });
  return NextResponse.json(booking);
}
