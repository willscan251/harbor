import { db } from '@/lib/db'
import { Users, FileText, Calendar, ListTodo, ArrowUpRight, Clock, FolderOpen, TrendingUp } from 'lucide-react'
import Link from 'next/link'

async function getStats() {
  const [clients, documents, meetings, tasks] = await Promise.all([
    db.client.count({ where: { status: 'active' } }),
    db.document.count(),
    db.meeting.count(),
    db.task.count({ where: { status: 'pending' } }),
  ])
  return { clients, documents, meetings, tasks }
}

async function getRecentActivity() {
  return db.activityLog.findMany({
    orderBy: { createdAt: 'desc' },
    take: 8,
    include: { client: { select: { name: true } } },
  })
}

async function getUpcomingTasks() {
  return db.task.findMany({
    where: { status: 'pending' },
    orderBy: { dueDate: 'asc' },
    take: 5,
    include: { client: { select: { name: true } } },
  })
}

export default async function DashboardPage() {
  const stats = await getStats()
  const activity = await getRecentActivity()
  const tasks = await getUpcomingTasks()

  return (
    <div className="animate-in">
      <div className="mb-8">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-sm text-[var(--text-muted)] mt-1">Welcome back. Here&apos;s your overview.</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard label="ACTIVE CLIENTS" value={stats.clients} icon={Users} color="green" href="/dashboard/clients" />
        <StatCard label="DOCUMENTS" value={stats.documents} icon={FileText} color="blue" href="/dashboard/files" />
        <StatCard label="MEETINGS" value={stats.meetings} icon={Calendar} color="purple" href="/dashboard/meetings" />
        <StatCard label="PENDING TASKS" value={stats.tasks} icon={ListTodo} color="orange" href="/dashboard/tasks" />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4 mb-6">
        {/* Activity */}
        <div className="lg:col-span-3 card p-0 overflow-hidden">
          <div className="px-5 py-3.5 border-b border-white/[0.04] flex items-center justify-between">
            <h2 className="text-[13px] font-semibold">Recent Activity</h2>
            <span className="text-[11px] text-[var(--text-muted)]">{activity.length} events</span>
          </div>
          <div className="divide-y divide-white/[0.03]">
            {activity.length === 0 && (
              <div className="px-5 py-12 text-center">
                <Clock className="w-8 h-8 text-[var(--text-muted)] mx-auto mb-2 opacity-30" />
                <p className="text-sm text-[var(--text-muted)]">No activity yet.</p>
                <p className="text-xs text-[var(--text-muted)] mt-1 opacity-60">Drop files into Harbor Inbox to get started.</p>
              </div>
            )}
            {activity.map(log => (
              <div key={log.id} className="px-5 py-3 flex items-start gap-3 hover:bg-white/[0.015] transition">
                <div className="w-1.5 h-1.5 bg-[var(--accent)] rounded-full mt-2 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-[13px] text-[var(--text-secondary)] leading-snug">{log.description}</p>
                  <div className="flex items-center gap-2 mt-0.5">
                    {log.client?.name && <span className="text-[11px] font-semibold text-[var(--accent)]">{log.client.name}</span>}
                    <span className="text-[11px] text-[var(--text-muted)]">
                      {new Date(log.createdAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Tasks */}
        <div className="lg:col-span-2 card p-0 overflow-hidden">
          <div className="px-5 py-3.5 border-b border-white/[0.04] flex items-center justify-between">
            <h2 className="text-[13px] font-semibold">Upcoming Tasks</h2>
            <Link href="/dashboard/tasks" className="text-[11px] text-[var(--accent)] hover:text-[var(--accent)] font-medium">View all</Link>
          </div>
          <div className="divide-y divide-white/[0.03]">
            {tasks.length === 0 && (
              <div className="px-5 py-12 text-center">
                <ListTodo className="w-8 h-8 text-[var(--text-muted)] mx-auto mb-2 opacity-30" />
                <p className="text-sm text-[var(--text-muted)]">All caught up!</p>
              </div>
            )}
            {tasks.map(task => (
              <div key={task.id} className="px-5 py-3 hover:bg-white/[0.015] transition">
                <div className="flex items-center justify-between">
                  <p className="text-[13px] font-medium truncate flex-1">{task.title}</p>
                  <span className={`badge-sm ml-2 ${
                    task.priority === 'high' ? 'bg-red-500/10 text-red-400' :
                    task.priority === 'medium' ? 'bg-orange-500/10 text-orange-400' : 'bg-white/5 text-white/40'
                  }`}>{task.priority}</span>
                </div>
                <p className="text-[11px] text-[var(--text-muted)] mt-0.5">{task.client?.name}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <QuickAction href="https://scanland.sharepoint.com/sites/TheScanlandGroup" icon={FolderOpen} label="Harbor Files" desc="Open shared drive" color="blue" external />
        <QuickAction href="/dashboard/clients" icon={Users} label="Manage Clients" desc={`${stats.clients} active clients`} color="green" />
        <QuickAction href="/dashboard/settings" icon={TrendingUp} label="Settings" desc="Integrations & config" color="purple" />
      </div>
    </div>
  )
}

function StatCard({ label, value, icon: Icon, color, href }: { label: string; value: number; icon: any; color: string; href: string }) {
  const colors: Record<string, string> = {
    green: 'card-glow-green text-[var(--green)]',
    blue: 'card-glow-blue text-[var(--blue)]',
    purple: 'card-glow-purple text-[var(--accent)]',
    orange: 'card-glow-orange text-[var(--orange)]',
  }
  const iconBg: Record<string, string> = {
    green: 'bg-[var(--green-glow)]', blue: 'bg-[var(--blue-glow)]',
    purple: 'bg-[var(--accent-glow)]', orange: 'bg-[var(--orange-glow)]',
  }

  return (
    <Link href={href} className={`card ${colors[color]} p-5 group`}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-[10px] font-bold tracking-widest text-[var(--text-muted)]">{label}</span>
        <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${iconBg[color]}`}>
          <Icon className="w-[18px] h-[18px]" />
        </div>
      </div>
      <p className="text-3xl font-extrabold tracking-tight text-white">{value}</p>
    </Link>
  )
}

function QuickAction({ href, icon: Icon, label, desc, color, external }: { href: string; icon: any; label: string; desc: string; color: string; external?: boolean }) {
  const bg: Record<string, string> = { blue: 'bg-[var(--blue-glow)]', green: 'bg-[var(--green-glow)]', purple: 'bg-[var(--accent-glow)]' }
  const tc: Record<string, string> = { blue: 'text-[var(--blue)]', green: 'text-[var(--green)]', purple: 'text-[var(--accent)]' }
  const Tag = external ? 'a' : Link
  const extra = external ? { target: '_blank', rel: 'noopener' } : {}
  
  return (
    <Tag href={href} {...extra as any} className="card px-4 py-3.5 flex items-center gap-4 group hover:border-white/[0.1]">
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${bg[color]}`}>
        <Icon className={`w-5 h-5 ${tc[color]}`} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-[13px] font-semibold">{label}</p>
        <p className="text-[11px] text-[var(--text-muted)]">{desc}</p>
      </div>
      <ArrowUpRight className="w-4 h-4 text-white/10 group-hover:text-white/30 transition" />
    </Tag>
  )
}
