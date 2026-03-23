import { NextResponse } from 'next/server'
import { db } from '@/lib/db'

export async function GET() {
  const clients = await db.client.findMany({
    where: { status: 'active' },
    orderBy: { name: 'asc' },
    include: {
      _count: { select: { tasks: { where: { status: 'pending' } }, documents: true } },
      aliases: { select: { alias: true, aliasType: true } },
    },
  })
  return NextResponse.json(clients)
}

export async function POST(request: Request) {
  const body = await request.json()
  const client = await db.client.create({
    data: {
      code: body.code,
      name: body.name,
      shortName: body.shortName,
      primaryContactName: body.primaryContactName,
      primaryContactEmail: body.primaryContactEmail,
      primaryContactPhone: body.primaryContactPhone,
    },
  })
  return NextResponse.json(client, { status: 201 })
}
