import { NextResponse } from 'next/server';
import { db } from '../../../mock/db';

export async function GET() {
  return NextResponse.json(db.events);
}
