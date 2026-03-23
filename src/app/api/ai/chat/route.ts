import { NextResponse } from 'next/server'
import Anthropic from '@anthropic-ai/sdk'
import { db } from '@/lib/db'

export async function POST(request: Request) {
  const { message, history } = await request.json()

  if (!process.env.ANTHROPIC_API_KEY) {
    return NextResponse.json({ response: 'Anthropic API key not configured. Go to Settings > Admin Keys to add it.' }, { status: 200 })
  }

  // Gather context about the company
  const clients = await db.client.findMany({
    where: { status: 'active' },
    include: {
      _count: { select: { tasks: { where: { status: 'pending' } }, documents: true, meetings: true } },
      aliases: { select: { alias: true } },
    },
  })

  const pendingTasks = await db.task.findMany({
    where: { status: 'pending' },
    include: { client: { select: { name: true } } },
    take: 20,
  })

  const recentActivity = await db.activityLog.findMany({
    orderBy: { createdAt: 'desc' },
    take: 10,
    include: { client: { select: { name: true } } },
  })

  const recentMeetings = await db.meeting.findMany({
    orderBy: { meetingDate: 'desc' },
    take: 10,
    include: { client: { select: { name: true } } },
  })

  const systemPrompt = `You are Harbor AI, the intelligent assistant for The Scanland Group (TSG), a nonprofit consulting firm under Scanland & Co.

You have access to the following company data:

ACTIVE CLIENTS (${clients.length}):
${clients.map(c => `- ${c.name} (${c.shortName || c.code}): ${c._count.tasks} pending tasks, ${c._count.documents} docs, ${c._count.meetings} meetings${c.aliases.length ? ` | Aliases: ${c.aliases.map(a => a.alias).join(', ')}` : ''}`).join('\n')}

PENDING TASKS (${pendingTasks.length}):
${pendingTasks.map(t => `- [${t.priority}] ${t.title} (${t.client?.name || 'Unassigned'})`).join('\n') || 'None'}

RECENT MEETINGS:
${recentMeetings.map(m => `- ${m.title} — ${m.client?.name} — ${new Date(m.meetingDate).toLocaleDateString()}${m.aiSummary ? ` — Summary: ${m.aiSummary.slice(0, 100)}...` : ''}`).join('\n') || 'None yet'}

RECENT ACTIVITY:
${recentActivity.map(a => `- ${a.description}${a.client?.name ? ` (${a.client.name})` : ''}`).join('\n') || 'No recent activity'}

INSTRUCTIONS:
- Answer questions about clients, tasks, meetings, and company operations
- Be concise and professional
- If asked to find files, explain that Harbor Files stores documents in SharePoint organized by client
- If asked about something you don't have data for, say so clearly
- You can suggest actions like "Would you like me to create a task for that?"
- When discussing clients, reference their actual data above`

  try {
    const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY })

    const messages = [
      ...(history || []).map((h: any) => ({ role: h.role, content: h.content })),
      { role: 'user' as const, content: message },
    ]

    const response = await anthropic.messages.create({
      model: process.env.AI_MODEL || 'claude-sonnet-4-20250514',
      max_tokens: 1000,
      system: systemPrompt,
      messages,
    })

    const text = response.content[0].type === 'text' ? response.content[0].text : ''
    return NextResponse.json({ response: text })
  } catch (err: any) {
    console.error('AI Chat error:', err)
    return NextResponse.json({ response: `Error: ${err.message}` }, { status: 200 })
  }
}
