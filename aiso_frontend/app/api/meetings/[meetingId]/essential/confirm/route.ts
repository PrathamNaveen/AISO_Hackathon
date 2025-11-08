import { NextResponse } from 'next/server';
import { db } from '../../../../../../mock/db';

export async function POST(req: Request, { params }: { params: { meetingId: string } }) {
  const meetingId = params.meetingId;
  const body = await req.json();
  // save to short-term memory
  db.shortTerm[meetingId] = body;
  // push a reasoning step
  const taskId = 'agent_task_' + Math.random().toString(36).slice(2, 8);
  db.reasoning[meetingId] = db.reasoning[meetingId] || [];
  db.reasoning[meetingId].push({ ts: new Date().toISOString(), type: 'stage', text: 'Planning started' });
  return NextResponse.json({ taskId, meetingId, status: 'accepted', message: 'Agent planning started' }, { status: 202 });
}
