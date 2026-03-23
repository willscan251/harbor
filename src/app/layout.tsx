import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Harbor — Business Management System',
  description: 'Harbor by Scanland & Co',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#0A0A0F] text-white">{children}</body>
    </html>
  )
}
