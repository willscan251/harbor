import Link from 'next/link'
import { db } from '@/lib/db'
import { getInitials } from '@/lib/utils'
import { Plus, ExternalLink } from 'lucide-react'

export default async function ClientsPage() {
  const clients = await db.client.findMany({
    where: { status: 'active' },
    orderBy: { name: 'asc' },
    include: {
      _count: { select: { tasks: { where: { status: 'pending' } }, documents: true, meetings: true } },
    },
  })

  return (
    <div className="animate-in">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Clients</h1>
          <p className="text-sm text-[var(--text-muted)] mt-1">{clients.length} active clients</p>
        </div>
        <Link href="/dashboard/clients/new" className="btn-accent text-[12px]">
          <Plus className="w-4 h-4" /> Add Client
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {clients.map(client => (
          <Link key={client.id} href={`/dashboard/clients/${client.id}`}
            className="card px-5 py-4 group hover:border-[var(--accent)]/30">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[var(--accent)]/20 to-[var(--accent)]/5 flex items-center justify-center text-[12px] font-bold text-[var(--accent)]">
                {getInitials(client.name)}
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-[14px] font-semibold truncate group-hover:text-[var(--accent)] transition">{client.name}</h3>
                <p className="text-[11px] text-[var(--text-muted)]">{client.shortName || client.code}</p>
              </div>
            </div>
            <div className="flex gap-4 text-[11px] text-[var(--text-muted)]">
              <span>{client._count.tasks} tasks</span>
              <span>{client._count.documents} docs</span>
              <span>{client._count.meetings} meetings</span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}
