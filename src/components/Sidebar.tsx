'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { signOut, useSession } from 'next-auth/react'
import {
  LayoutDashboard, Users, FolderOpen, Calendar, ListTodo,
  BarChart3, Settings, LogOut, MessageCircle, ChevronRight, Anchor
} from 'lucide-react'

const nav = [
  { href: '/dashboard', icon: LayoutDashboard, label: 'Overview' },
  { href: '/dashboard/clients', icon: Users, label: 'Clients' },
  { href: '/dashboard/files', icon: FolderOpen, label: 'Harbor Files' },
  { href: '/dashboard/meetings', icon: Calendar, label: 'Meetings' },
  { href: '/dashboard/tasks', icon: ListTodo, label: 'Tasks' },
  { href: '/dashboard/reports', icon: BarChart3, label: 'Reports' },
]

export default function Sidebar() {
  const pathname = usePathname()
  const { data: session, status } = useSession()

  const isLoaded = status === 'authenticated' && session?.user
  const userName = isLoaded ? (session.user.name || 'User') : ''
  const userRole = isLoaded ? ((session.user as any).role || 'staff') : ''
  const initials = userName ? userName.split(' ').map((n: string) => n[0]).join('').toUpperCase().slice(0, 2) : ''

  return (
    <aside className="w-[72px] hover:w-[240px] group/sb bg-[#060D14] flex flex-col min-h-screen border-r border-[rgba(70,130,160,0.08)] transition-all duration-300 overflow-hidden">
      <div className="px-4 py-5 flex items-center gap-3 border-b border-[rgba(70,130,160,0.08)]">
        <div className="w-10 h-10 shrink-0 rounded-xl bg-gradient-to-br from-[#0C7BB3] to-[#0F9B8E] flex items-center justify-center shadow-lg shadow-[#0C7BB3]/15">
          <Anchor className="w-5 h-5 text-white" />
        </div>
        <div className="opacity-0 group-hover/sb:opacity-100 transition-opacity duration-200 whitespace-nowrap">
          <h1 className="text-[14px] font-bold text-white tracking-tight">Harbor</h1>
          <p className="text-[9px] text-[#0C7BB3]/50 font-semibold uppercase tracking-widest">The Scanland Group</p>
        </div>
      </div>

      <nav className="flex-1 py-3 px-2.5 space-y-0.5">
        {nav.map(item => {
          const active = pathname === item.href || (item.href !== '/dashboard' && pathname.startsWith(item.href))
          return (
            <Link key={item.href} href={item.href}
              className={`flex items-center gap-3 px-2.5 py-2 rounded-xl text-[13px] font-medium transition-all ${
                active ? 'bg-[#0C7BB3]/10 text-[#4DB8D4]' : 'text-white/30 hover:text-white/70 hover:bg-white/[0.03]'
              }`}>
              <item.icon className={`w-[18px] h-[18px] shrink-0 ${active ? 'text-[#4DB8D4]' : ''}`} />
              <span className="opacity-0 group-hover/sb:opacity-100 transition-opacity duration-200 whitespace-nowrap">{item.label}</span>
              {active && <ChevronRight className="w-3 h-3 text-[#4DB8D4]/30 ml-auto opacity-0 group-hover/sb:opacity-100 transition-opacity" />}
            </Link>
          )
        })}

        <div className="h-px bg-[rgba(70,130,160,0.08)] my-2" />

        <Link href="/dashboard/settings"
          className={`flex items-center gap-3 px-2.5 py-2 rounded-xl text-[13px] font-medium transition-all ${
            pathname.startsWith('/dashboard/settings') ? 'bg-[#0C7BB3]/10 text-[#4DB8D4]' : 'text-white/30 hover:text-white/70 hover:bg-white/[0.03]'
          }`}>
          <Settings className="w-[18px] h-[18px] shrink-0" />
          <span className="opacity-0 group-hover/sb:opacity-100 transition-opacity duration-200 whitespace-nowrap">Settings</span>
        </Link>

        <Link href="/dashboard/chat"
          className={`flex items-center gap-3 px-2.5 py-2 rounded-xl text-[13px] font-medium transition-all ${
            pathname === '/dashboard/chat' ? 'bg-[#0C7BB3]/10 text-[#4DB8D4]' : 'text-white/30 hover:text-white/70 hover:bg-white/[0.03]'
          }`}>
          <MessageCircle className="w-[18px] h-[18px] shrink-0" />
          <span className="opacity-0 group-hover/sb:opacity-100 transition-opacity duration-200 whitespace-nowrap">AI Assistant</span>
        </Link>
      </nav>

      <div className="p-2.5 border-t border-[rgba(70,130,160,0.08)]">
        {isLoaded ? (
          <div className="flex items-center gap-3 px-2 py-2 rounded-xl hover:bg-white/[0.03] transition">
            <div className="w-9 h-9 shrink-0 rounded-full bg-gradient-to-br from-[#0F9B8E] to-[#0C7BB3] flex items-center justify-center text-[11px] font-bold text-white">{initials}</div>
            <div className="opacity-0 group-hover/sb:opacity-100 transition-opacity duration-200 whitespace-nowrap flex-1 min-w-0">
              <p className="text-[12px] font-semibold text-white/80 truncate">{userName}</p>
              <p className="text-[10px] text-white/25 capitalize">{userRole}</p>
            </div>
            <button onClick={() => signOut({ callbackUrl: '/login' })} className="opacity-0 group-hover/sb:opacity-100 p-1.5 rounded-lg text-white/15 hover:text-white/50 hover:bg-white/[0.06] transition" title="Sign out">
              <LogOut className="w-3.5 h-3.5" />
            </button>
          </div>
        ) : <div className="h-[52px]" />}
      </div>
    </aside>
  )
}
