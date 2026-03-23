import { db } from '@/lib/db'
import { formatDate } from '@/lib/utils'
import { Calendar, Video } from 'lucide-react'

export default async function MeetingsPage() {
  const meetings = await db.meeting.findMany({ orderBy: { meetingDate: 'desc' }, take: 20, include: { client: { select: { name: true } } } })
  return (
    <div className="animate-in">
      <div className="mb-6"><h1 className="text-2xl font-bold">Meetings</h1><p className="text-sm text-[var(--text-muted)] mt-1">Your Outlook calendar and meeting history.</p></div>
      <div className="card p-0 overflow-hidden">
        {meetings.length === 0 && (
          <div className="px-5 py-14 text-center">
            <Calendar className="w-10 h-10 text-[var(--text-muted)] mx-auto mb-3 opacity-20" />
            <p className="text-[14px] font-medium text-[var(--text-secondary)]">No meetings yet</p>
            <p className="text-[12px] text-[var(--text-muted)] mt-1">Connect your Microsoft account in Settings to sync your calendar.</p>
            <p className="text-[11px] text-[var(--text-muted)] mt-3 flex items-center justify-center gap-1"><Video className="w-3.5 h-3.5" /> Zoom recordings auto-import once connected.</p>
          </div>
        )}
        {meetings.map(m => (
          <div key={m.id} className="px-5 py-4 border-b border-white/[0.03] hover:bg-white/[0.015] transition">
            <h3 className="text-[14px] font-medium">{m.title}</h3>
            <p className="text-[12px] text-[var(--text-muted)]">{m.client?.name} · {formatDate(m.meetingDate)}</p>
            {m.aiSummary && <p className="text-[12px] text-[var(--text-secondary)] mt-2 line-clamp-2">{m.aiSummary}</p>}
          </div>
        ))}
      </div>
    </div>
  )
}
