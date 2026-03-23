import Sidebar from '@/components/Sidebar'
import { SessionProvider } from '@/components/SessionProvider'

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <SessionProvider>
      <div className="flex min-h-screen bg-[#0A0A0F]">
        <Sidebar />
        <main className="flex-1 overflow-auto">
          <div className="px-8 py-6 max-w-[1200px]">{children}</div>
        </main>
      </div>
    </SessionProvider>
  )
}
