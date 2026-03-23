'use client'

import { useSession } from 'next-auth/react'
import { useEffect, useState } from 'react'
import { FileText, Calendar, CheckSquare, LogOut } from 'lucide-react'
import { signOut } from 'next-auth/react'

export default function PortalDashboard() {
  const { data: session } = useSession()
  const [data, setData] = useState<any>(null)

  useEffect(() => {
    if (session?.user) {
      fetch(`/api/portal/overview`)
        .then(r => r.json())
        .then(setData)
        .catch(console.error)
    }
  }, [session])

  if (!session) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold text-gray-900">{session.user?.name}</h1>
            <p className="text-sm text-gray-500">Client Portal · The Scanland Group</p>
          </div>
          <button
            onClick={() => signOut({ callbackUrl: '/portal' })}
            className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700"
          >
            <LogOut className="w-4 h-4" /> Sign Out
          </button>
        </div>
      </header>

      <main className="max-w-5xl mx-auto py-8 px-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <StatCard icon={CheckSquare} label="Active Tasks" value={data?.taskCount ?? '—'} />
          <StatCard icon={FileText} label="Documents" value={data?.documentCount ?? '—'} />
          <StatCard icon={Calendar} label="Upcoming Meetings" value={data?.meetingCount ?? '—'} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="font-semibold text-gray-900 mb-4">Your Tasks</h2>
            {!data?.tasks?.length && <p className="text-sm text-gray-500">No tasks right now.</p>}
            {data?.tasks?.map((task: any) => (
              <div key={task.id} className="py-2 border-b border-gray-100 last:border-0">
                <p className="text-sm font-medium text-gray-900">{task.title}</p>
                {task.dueDate && <p className="text-xs text-gray-500">Due: {new Date(task.dueDate).toLocaleDateString()}</p>}
              </div>
            ))}
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="font-semibold text-gray-900 mb-4">Recent Documents</h2>
            {!data?.documents?.length && <p className="text-sm text-gray-500">No documents shared yet.</p>}
            {data?.documents?.map((doc: any) => (
              <div key={doc.id} className="py-2 border-b border-gray-100 last:border-0">
                <p className="text-sm font-medium text-gray-900">{doc.displayName || doc.filename}</p>
                <p className="text-xs text-gray-500">{doc.category} · {new Date(doc.createdAt).toLocaleDateString()}</p>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  )
}

function StatCard({ icon: Icon, label, value }: { icon: any; label: string; value: string | number }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <div className="flex items-center gap-3">
        <div className="bg-gray-100 p-2 rounded-lg"><Icon className="w-5 h-5 text-gray-600" /></div>
        <div>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          <p className="text-xs text-gray-500">{label}</p>
        </div>
      </div>
    </div>
  )
}
