'use client'

import { useState } from 'react'
import { signIn } from 'next-auth/react'
import { useRouter } from 'next/navigation'
import { Anchor, ArrowRight } from 'lucide-react'

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const router = useRouter()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    const result = await signIn('staff-login', { username, password, redirect: false })
    setLoading(false)
    if (result?.error) setError('Invalid credentials')
    else router.push('/dashboard')
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#060D14] relative overflow-hidden">
      {/* Ambient ocean glow */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[500px] bg-[#0EA5E9] rounded-full opacity-[0.03] blur-[150px]" />
      <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-[#14B8A6] rounded-full opacity-[0.025] blur-[120px]" />
      <div className="absolute top-0 right-0 w-[300px] h-[300px] bg-[#06B6D4] rounded-full opacity-[0.02] blur-[100px]" />

      <div className="w-full max-w-[380px] relative z-10">
        <div className="text-center mb-10">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-sky-500 to-teal-500 flex items-center justify-center mx-auto mb-4 shadow-xl shadow-sky-500/20">
            <Anchor className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Harbor</h1>
          <p className="text-[13px] text-[var(--text-muted)] mt-1">Business Management System</p>
        </div>

        <div className="card p-7">
          <h2 className="text-[15px] font-semibold text-white mb-5">Sign in to continue</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-1.5">Username</label>
              <input type="text" value={username} onChange={e => setUsername(e.target.value)}
                className="input-dark" placeholder="Enter username" required autoFocus />
            </div>
            <div>
              <label className="block text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-1.5">Password</label>
              <input type="password" value={password} onChange={e => setPassword(e.target.value)}
                className="input-dark" placeholder="Enter password" required />
            </div>
            {error && <div className="bg-red-500/10 border border-red-500/20 text-red-400 text-[13px] px-3 py-2 rounded-lg">{error}</div>}
            <button type="submit" disabled={loading} className="btn-accent w-full justify-center py-2.5 text-[13px]">
              {loading ? 'Signing in...' : <><span>Sign In</span><ArrowRight className="w-4 h-4" /></>}
            </button>
          </form>
        </div>
        <p className="text-center text-[11px] text-[var(--text-muted)] mt-6 opacity-40">Powered by Harbor · Scanland & Co</p>
      </div>
    </div>
  )
}
