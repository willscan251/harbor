import { SessionProvider } from '@/components/SessionProvider'

export default function PortalLayout({ children }: { children: React.ReactNode }) {
  return <SessionProvider>{children}</SessionProvider>
}
