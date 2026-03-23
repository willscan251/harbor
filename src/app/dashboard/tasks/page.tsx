import { db } from '@/lib/db'
import { formatDate } from '@/lib/utils'
import { ListTodo } from 'lucide-react'

export default async function TasksPage() {
  const tasks = await db.task.findMany({ where: { status: 'pending' }, orderBy: [{ dueDate: 'asc' }], include: { client: { select: { name: true } } } })
  return (
    <div className="animate-in">
      <div className="mb-6"><h1 className="text-2xl font-bold">Tasks</h1><p className="text-sm text-[var(--text-muted)] mt-1">{tasks.length} pending</p></div>
      <div className="card p-0 overflow-hidden">
        {tasks.length === 0 && (
          <div className="px-5 py-14 text-center">
            <ListTodo className="w-10 h-10 text-[var(--text-muted)] mx-auto mb-3 opacity-20" />
            <p className="text-[14px] font-medium text-[var(--text-secondary)]">All caught up!</p>
            <p className="text-[12px] text-[var(--text-muted)] mt-1">Tasks come from meeting action items or manual creation.</p>
          </div>
        )}
        {tasks.map(t => (
          <div key={t.id} className="px-5 py-3.5 border-b border-white/[0.03] flex items-center justify-between hover:bg-white/[0.015] transition">
            <div><p className="text-[13px] font-medium">{t.title}</p><p className="text-[11px] text-[var(--text-muted)]">{t.client?.name}{t.dueDate && ` · Due ${formatDate(t.dueDate)}`}</p></div>
            <span className={`badge-sm ${t.priority==='high'?'bg-red-500/10 text-red-400':t.priority==='medium'?'bg-orange-500/10 text-orange-400':'bg-white/5 text-white/40'}`}>{t.priority}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
