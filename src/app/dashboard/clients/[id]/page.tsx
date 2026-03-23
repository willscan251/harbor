import { notFound } from 'next/navigation'
import { db } from '@/lib/db'
import { formatDate } from '@/lib/utils'
import { FileText, Calendar, ListTodo, Mail, Phone, ExternalLink, Edit3, Archive, Eye, Plus } from 'lucide-react'
import Link from 'next/link'

interface Props {
  params: Promise<{ id: string }>
}

export default async function ClientDetailPage(props: Props) {
  const params = await props.params
  const clientId = parseInt(params.id)
  
  if (isNaN(clientId)) notFound()

  const client = await db.client.findUnique({
    where: { id: clientId },
    include: {
      tasks: { orderBy: { createdAt: 'desc' }, take: 10 },
      documents: { orderBy: { createdAt: 'desc' }, take: 10 },
      meetings: { orderBy: { meetingDate: 'desc' }, take: 5 },
      contacts: true,
      aliases: true,
    },
  })
  if (!client) notFound()
  const pendingTasks = client.tasks.filter(t => t.status === 'pending')

  return (
    <div className="animate-in">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">{client.name}</h1>
          <p className="text-sm text-[var(--text-muted)]">{client.shortName} · {client.code}</p>
        </div>
        <div className="flex items-center gap-2">
          <Link href={`/portal/preview/${client.id}`} className="btn-ghost text-[12px]">
            <Eye className="w-3.5 h-3.5" /> Preview Portal
          </Link>
          <button className="btn-ghost text-[12px]"><Edit3 className="w-3.5 h-3.5" /> Edit</button>
          <button className="btn-ghost text-[12px] text-[var(--red)] border-red-500/20 hover:bg-red-500/10">
            <Archive className="w-3.5 h-3.5" /> Archive
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 space-y-4">
          {/* Tasks */}
          <div className="card p-0 overflow-hidden">
            <div className="px-5 py-3.5 border-b border-white/[0.04] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ListTodo className="w-4 h-4 text-[var(--teal)]" />
                <h2 className="text-[13px] font-semibold">Tasks ({pendingTasks.length} pending)</h2>
              </div>
              <button className="btn-ghost text-[10px] py-1 px-2"><Plus className="w-3 h-3" /> Add Task</button>
            </div>
            <div className="divide-y divide-white/[0.03]">
              {pendingTasks.length === 0 && <p className="text-[13px] text-[var(--text-muted)] px-5 py-6">No pending tasks</p>}
              {pendingTasks.map(task => (
                <div key={task.id} className="px-5 py-3 flex items-center justify-between hover:bg-white/[0.015] transition">
                  <div>
                    <p className="text-[13px] font-medium">{task.title}</p>
                    <p className="text-[11px] text-[var(--text-muted)]">
                      {task.assignedTo && `${task.assignedTo}`}
                      {task.dueDate && ` · Due ${formatDate(task.dueDate)}`}
                    </p>
                  </div>
                  <span className={`badge-sm ${
                    task.priority === 'high' ? 'bg-red-500/10 text-red-400' :
                    task.priority === 'medium' ? 'bg-amber-500/10 text-amber-400' : 'bg-white/5 text-white/40'
                  }`}>{task.priority}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Documents */}
          <div className="card p-0 overflow-hidden">
            <div className="px-5 py-3.5 border-b border-white/[0.04] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-[var(--seafoam)]" />
                <h2 className="text-[13px] font-semibold">Documents ({client.documents.length})</h2>
              </div>
              <button className="btn-ghost text-[10px] py-1 px-2"><Plus className="w-3 h-3" /> Upload</button>
            </div>
            <div className="divide-y divide-white/[0.03]">
              {client.documents.length === 0 && <p className="text-[13px] text-[var(--text-muted)] px-5 py-6">No documents yet</p>}
              {client.documents.map(doc => (
                <div key={doc.id} className="px-5 py-3 hover:bg-white/[0.015] transition">
                  <p className="text-[13px] font-medium">{doc.displayName || doc.filename}</p>
                  <p className="text-[11px] text-[var(--text-muted)]">{doc.category} · {formatDate(doc.createdAt)}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Meetings */}
          <div className="card p-0 overflow-hidden">
            <div className="px-5 py-3.5 border-b border-white/[0.04] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4 text-[var(--accent)]" />
                <h2 className="text-[13px] font-semibold">Meetings</h2>
              </div>
              <button className="btn-ghost text-[10px] py-1 px-2"><Plus className="w-3 h-3" /> Schedule</button>
            </div>
            <div className="divide-y divide-white/[0.03]">
              {client.meetings.length === 0 && <p className="text-[13px] text-[var(--text-muted)] px-5 py-6">No meetings yet</p>}
              {client.meetings.map(m => (
                <div key={m.id} className="px-5 py-3 hover:bg-white/[0.015] transition">
                  <p className="text-[13px] font-medium">{m.title}</p>
                  <p className="text-[11px] text-[var(--text-muted)]">{formatDate(m.meetingDate)}</p>
                  {m.aiSummary && <p className="text-[12px] text-[var(--text-secondary)] mt-1 line-clamp-2">{m.aiSummary}</p>}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          <div className="card p-5">
            <h3 className="text-[13px] font-semibold mb-3">Contact Info</h3>
            {client.primaryContactName && <p className="text-[13px] text-[var(--text-secondary)] mb-2">{client.primaryContactName}</p>}
            {client.primaryContactEmail && <div className="flex items-center gap-2 text-[12px] text-[var(--text-muted)] mb-1"><Mail className="w-3.5 h-3.5" /> {client.primaryContactEmail}</div>}
            {client.primaryContactPhone && <div className="flex items-center gap-2 text-[12px] text-[var(--text-muted)]"><Phone className="w-3.5 h-3.5" /> {client.primaryContactPhone}</div>}
            {!client.primaryContactName && !client.primaryContactEmail && <p className="text-[12px] text-[var(--text-muted)]">No contact info added</p>}
          </div>

          {client.aliases.length > 0 && (
            <div className="card p-5">
              <h3 className="text-[13px] font-semibold mb-3">Known Aliases</h3>
              {client.aliases.map(a => (
                <div key={a.id} className="text-[12px] mb-1">
                  <span className="text-[var(--text-secondary)]">{a.alias}</span>
                  <span className="text-[var(--text-muted)] ml-1.5">({a.aliasType})</span>
                </div>
              ))}
            </div>
          )}

          <div className="card p-5">
            <h3 className="text-[13px] font-semibold mb-3">Harbor Files</h3>
            <a href={`https://scanland.sharepoint.com/sites/TheScanlandGroup/Shared%20Documents/The%20Scanland%20Group/Clients/${encodeURIComponent(client.name)}`}
              target="_blank" className="text-[12px] text-[var(--teal)] hover:underline flex items-center gap-1">
              <ExternalLink className="w-3.5 h-3.5" /> Open client folder
            </a>
          </div>

          <div className="card p-5">
            <h3 className="text-[13px] font-semibold mb-2">Client Portal</h3>
            <p className="text-[11px] text-[var(--text-muted)] mb-3">Access code: <span className="font-mono text-[var(--seafoam)]">{client.code}</span></p>
            <Link href={`/portal/preview/${client.id}`} className="btn-ghost text-[11px] w-full justify-center">
              <Eye className="w-3.5 h-3.5" /> Preview as Client
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
