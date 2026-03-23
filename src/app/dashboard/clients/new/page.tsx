'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft } from 'lucide-react'
import Link from 'next/link'

export default function NewClientPage() {
  const router = useRouter()
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState({
    name: '', shortName: '', primaryContactName: '',
    primaryContactEmail: '', primaryContactPhone: '',
  })

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)

    // Generate a code from the name
    const code = form.shortName
      ? form.shortName.toLowerCase().replace(/\s+/g, '') + Math.floor(Math.random() * 9000 + 1000)
      : form.name.toLowerCase().replace(/\s+/g, '').slice(0, 3) + Math.floor(Math.random() * 9000 + 1000)

    const res = await fetch('/api/clients', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...form, code }),
    })

    if (res.ok) {
      const client = await res.json()
      router.push(`/dashboard/clients/${client.id}`)
    } else {
      setSaving(false)
      alert('Failed to create client')
    }
  }

  return (
    <div className="animate-in max-w-2xl">
      <Link href="/dashboard/clients" className="flex items-center gap-2 text-[13px] text-[var(--text-muted)] hover:text-[var(--text)] mb-4 transition">
        <ArrowLeft className="w-4 h-4" /> Back to Clients
      </Link>

      <h1 className="text-2xl font-bold mb-6">Add New Client</h1>

      <form onSubmit={handleSubmit} className="card p-6 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-1.5">Client Name *</label>
            <input className="input-dark" placeholder="e.g. Baldwin ARC" required value={form.name} onChange={e => setForm({...form, name: e.target.value})} />
          </div>
          <div>
            <label className="block text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-1.5">Short Name</label>
            <input className="input-dark" placeholder="e.g. ARC" value={form.shortName} onChange={e => setForm({...form, shortName: e.target.value})} />
          </div>
        </div>

        <div className="h-px bg-white/[0.04]" />
        <h3 className="text-[13px] font-semibold text-[var(--text-secondary)]">Primary Contact</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-1.5">Contact Name</label>
            <input className="input-dark" placeholder="Full name" value={form.primaryContactName} onChange={e => setForm({...form, primaryContactName: e.target.value})} />
          </div>
          <div>
            <label className="block text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-1.5">Email</label>
            <input className="input-dark" type="email" placeholder="email@example.com" value={form.primaryContactEmail} onChange={e => setForm({...form, primaryContactEmail: e.target.value})} />
          </div>
          <div>
            <label className="block text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-1.5">Phone</label>
            <input className="input-dark" placeholder="(555) 123-4567" value={form.primaryContactPhone} onChange={e => setForm({...form, primaryContactPhone: e.target.value})} />
          </div>
        </div>

        <div className="pt-2 flex gap-3">
          <button type="submit" disabled={saving} className="btn-accent text-[13px]">
            {saving ? 'Creating...' : 'Create Client'}
          </button>
          <Link href="/dashboard/clients" className="btn-ghost text-[13px]">Cancel</Link>
        </div>
      </form>
    </div>
  )
}
