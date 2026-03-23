import { NextResponse } from 'next/server'
import Anthropic from '@anthropic-ai/sdk'
import { db } from '@/lib/db'

const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY })

export async function POST(request: Request) {
  const { filename, content } = await request.json()

  const clients = await db.client.findMany({
    where: { status: 'active' },
    include: { aliases: true },
  })

  const clientsText = clients.map(c =>
    `- ID:${c.id} | Name:${c.name} | Short:${c.shortName || 'N/A'}`
  ).join('\n')

  const aliasesText = clients.flatMap(c =>
    c.aliases.map(a => `  - "${a.alias}" → ${c.name} (ID:${c.id})`)
  ).join('\n')

  const response = await anthropic.messages.create({
    model: process.env.AI_MODEL || 'claude-sonnet-4-20250514',
    max_tokens: 300,
    messages: [{
      role: 'user',
      content: `Categorize this document for filing.

FILENAME: ${filename}
${content ? `CONTENT:\n${content.slice(0, 3000)}` : ''}

CLIENTS:\n${clientsText}

ALIASES:\n${aliasesText}

Respond as JSON: { "clientId": number|null, "destination": "path", "category": "folder", "confidence": "high|medium|low", "reason": "why" }`
    }],
  })

  const text = response.content[0].type === 'text' ? response.content[0].text : ''

  try {
    const result = JSON.parse(text.replace(/```json?|```/g, '').trim())
    return NextResponse.json(result)
  } catch {
    return NextResponse.json({ raw: text, error: 'Parse failed' }, { status: 422 })
  }
}
