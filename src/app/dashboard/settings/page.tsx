'use client'
import { useState } from 'react'
import { useSession } from 'next-auth/react'
import { Cloud, Video, BookOpen, Key, Shield, Users, Building2, Eye, EyeOff, Save, ExternalLink, Globe } from 'lucide-react'

type Tab = 'integrations' | 'admin' | 'team' | 'company'

export default function SettingsPage() {
  const { data: session } = useSession()
  const isAdmin = !session || (session?.user as any)?.role === 'admin'
  const [tab, setTab] = useState<Tab>('integrations')
  const [show, setShow] = useState<Record<string,boolean>>({})
  const [domain, setDomain] = useState('thescanlandgroup.com')

  const tabs: {id:Tab;label:string;icon:any;adminOnly?:boolean}[] = [
    { id: 'integrations', label: 'Integrations', icon: Cloud },
    { id: 'admin', label: 'Admin Keys', icon: Key, adminOnly: true },
    { id: 'team', label: 'Team', icon: Users, adminOnly: true },
    { id: 'company', label: 'Company', icon: Building2, adminOnly: true },
  ]

  return (
    <div className="animate-in">
      <div className="mb-6"><h1 className="text-2xl font-bold">Settings</h1><p className="text-sm text-[var(--text-muted)] mt-1">Manage integrations, API keys, and system configuration.</p></div>

      <div className="tab-bar mb-6">
        {tabs.filter(t => !t.adminOnly || isAdmin).map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} className={`tab-item flex items-center gap-1.5 ${tab===t.id?'active':''}`}>
            <t.icon className="w-3.5 h-3.5" /> {t.label}
          </button>
        ))}
      </div>

      {tab === 'integrations' && (
        <div className="space-y-3">
          <p className="text-[12px] text-[var(--text-muted)] mb-2">Connect your accounts to enable calendar, files, and recording features.</p>
          {[
            { id:'microsoft', name:'Microsoft 365', desc:'Outlook calendar, Harbor Files, email', icon:Cloud, color:'text-[var(--accent)] bg-[var(--accent-glow)]', url:'https://login.microsoftonline.com' },
            { id:'zoom', name:'Zoom', desc:'Meeting recordings and transcript import', icon:Video, color:'text-[var(--teal)] bg-[var(--teal-glow)]', url:'https://zoom.us/oauth/authorize' },
          ].map(i => (
            <div key={i.id} className="card px-5 py-4 flex items-center gap-4">
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${i.color}`}><i.icon className="w-5 h-5" /></div>
              <div className="flex-1"><h3 className="text-[14px] font-semibold">{i.name}</h3><p className="text-[11px] text-[var(--text-muted)]">{i.desc}</p></div>
              <a href={i.url} target="_blank" rel="noopener" className="btn-ghost text-[11px]"><ExternalLink className="w-3 h-3" /> Connect Account</a>
            </div>
          ))}
          {isAdmin && (
            <div className="card px-5 py-4 flex items-center gap-4">
              <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-[var(--seafoam-glow)] text-[var(--seafoam)]"><BookOpen className="w-5 h-5" /></div>
              <div className="flex-1"><h3 className="text-[14px] font-semibold">Zoho Books</h3><p className="text-[11px] text-[var(--text-muted)]">Invoice sync — configure in Admin Keys</p></div>
              <a href="https://accounts.zoho.com/signin" target="_blank" rel="noopener" className="btn-ghost text-[11px]"><ExternalLink className="w-3 h-3" /> Connect</a>
            </div>
          )}
        </div>
      )}

      {tab === 'admin' && isAdmin && (
        <div className="space-y-4">
          <div className="card p-5">
            <div className="flex items-center gap-3 mb-5">
              <div className="w-9 h-9 rounded-xl bg-[var(--sand-glow)] flex items-center justify-center"><Shield className="w-5 h-5 text-[var(--sand)]" /></div>
              <div><h2 className="text-[14px] font-semibold">Super Admin Settings</h2><p className="text-[11px] text-[var(--text-muted)]">API keys and system-level configuration.</p></div>
            </div>
            <div className="space-y-4">
              <Field label="Anthropic API Key" placeholder="sk-ant-..." type="password" showKey="anthropic" show={show} setShow={setShow} hint="Powers AI file sorting, meeting summaries, and the chat agent." />
              <div>
                <label className="block text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-1.5">AI Model</label>
                <select className="input-dark"><option>claude-sonnet-4-20250514</option><option>claude-opus-4-20250514</option><option>claude-haiku-4-20250514</option></select>
              </div>
              <div className="h-px bg-white/[0.04]" />
              <Field label="Microsoft Client ID" placeholder="e47f8359-..." type="text" hint="From Azure App Registration" />
              <Field label="Microsoft Client Secret" placeholder="Your secret" type="password" showKey="ms_secret" show={show} setShow={setShow} />
              <Field label="Microsoft Tenant ID" placeholder="dbf21d9f-..." type="text" />
              <div className="h-px bg-white/[0.04]" />
              <Field label="Zoho Client ID" placeholder="Zoho client ID" type="text" hint="Syncs invoices to client pages" />
              <Field label="Zoho Client Secret" placeholder="Zoho secret" type="password" showKey="zoho_s" show={show} setShow={setShow} />
              <div className="pt-2"><button className="btn-accent text-[12px]"><Save className="w-3.5 h-3.5" /> Save Admin Settings</button></div>
            </div>
          </div>
        </div>
      )}

      {tab === 'team' && isAdmin && (
        <div className="card p-0 overflow-hidden">
          <div className="px-5 py-3.5 border-b border-white/[0.04] flex items-center justify-between">
            <h2 className="text-[13px] font-semibold">Team Members</h2>
            <button className="btn-accent text-[11px] py-1.5">Add Member</button>
          </div>
          <table className="w-full">
            <thead><tr className="border-b border-white/[0.04]">
              <th className="text-left text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider px-5 py-2.5">Member</th>
              <th className="text-left text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider px-5 py-2.5">Role</th>
              <th className="text-left text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider px-5 py-2.5">Microsoft</th>
              <th className="text-left text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider px-5 py-2.5">Zoom</th>
              <th className="text-right text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider px-5 py-2.5">Actions</th>
            </tr></thead>
            <tbody>
              {[
                { name:'Will Scanland', user:'will', role:'Admin', ms:true, zoom:false },
                { name:'Patricia Scanland', user:'patricia', role:'Admin', ms:false, zoom:false },
                { name:'Danny Patterson', user:'danny', role:'Staff', ms:false, zoom:false },
              ].map(m => (
                <tr key={m.user} className="border-b border-white/[0.02] hover:bg-white/[0.015]">
                  <td className="px-5 py-3"><p className="text-[13px] font-medium">{m.name}</p><p className="text-[11px] text-[var(--text-muted)]">{m.user}</p></td>
                  <td className="px-5 py-3"><span className={`badge-sm ${m.role==='Admin'?'bg-[var(--accent-glow)] text-[var(--accent)]':'bg-[var(--sand-glow)] text-[var(--sand)]'}`}>{m.role}</span></td>
                  <td className="px-5 py-3">{m.ms ? <span className="badge-sm bg-[var(--seafoam-glow)] text-[var(--seafoam)]">Connected</span> : <button className="text-[11px] text-[var(--accent)]">Connect</button>}</td>
                  <td className="px-5 py-3">{m.zoom ? <span className="badge-sm bg-[var(--seafoam-glow)] text-[var(--seafoam)]">Connected</span> : <button className="text-[11px] text-[var(--accent)]">Connect</button>}</td>
                  <td className="px-5 py-3 text-right"><button className="text-[11px] text-[var(--text-muted)] hover:text-white">Edit</button><span className="text-white/10 mx-1.5">|</span><button className="text-[11px] text-[var(--text-muted)] hover:text-white">Reset Password</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === 'company' && isAdmin && (
        <div className="space-y-4">
          <div className="card p-5">
            <div className="flex items-center gap-2 mb-4"><Building2 className="w-4 h-4 text-[var(--text-muted)]" /><h2 className="text-[14px] font-semibold">Company Profile</h2></div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <Field label="Company Name" defaultValue="The Scanland Group" type="text" />
              <Field label="Parent Organization" defaultValue="Scanland & Co" type="text" />
              <Field label="Website" defaultValue="https://thescanlandgroup.com" type="text" />
              <Field label="Industry" defaultValue="Nonprofit Consulting" type="text" />
            </div>
            <div className="pt-3"><button className="btn-accent text-[12px]"><Save className="w-3.5 h-3.5" /> Save</button></div>
          </div>
          <div className="card p-5">
            <div className="flex items-center gap-2 mb-4"><Globe className="w-4 h-4 text-[var(--text-muted)]" /><h2 className="text-[14px] font-semibold">Domains</h2></div>
            <p className="text-[11px] text-[var(--text-muted)] mb-3">Your Harbor and Portal URLs are based on your company domain.</p>
            <div className="space-y-3">
              <div>
                <label className="block text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-1.5">Company Domain</label>
                <input className="input-dark" value={domain} onChange={e => setDomain(e.target.value)} placeholder="yourdomain.com" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-[var(--bg)] rounded-lg p-3 border border-white/[0.04]">
                  <p className="text-[10px] text-[var(--text-muted)] mb-1">Staff Dashboard</p>
                  <p className="text-[13px] font-mono text-[var(--accent)]">harbor.{domain}</p>
                </div>
                <div className="bg-[var(--bg)] rounded-lg p-3 border border-white/[0.04]">
                  <p className="text-[10px] text-[var(--text-muted)] mb-1">Client Portal</p>
                  <p className="text-[13px] font-mono text-[var(--teal)]">portal.{domain}</p>
                </div>
              </div>
            </div>
            <div className="pt-3"><button className="btn-accent text-[12px]"><Save className="w-3.5 h-3.5" /> Update Domain</button></div>
          </div>
        </div>
      )}
    </div>
  )
}

function Field({ label, placeholder, defaultValue, type, hint, showKey, show, setShow }: any) {
  const isPassword = type === 'password' && showKey
  return (
    <div>
      <label className="block text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-1.5">{label}</label>
      <div className="relative">
        <input type={isPassword && !show?.[showKey] ? 'password' : 'text'} className="input-dark" placeholder={placeholder} defaultValue={defaultValue} />
        {isPassword && (
          <button type="button" onClick={() => setShow?.((p:any) => ({...p, [showKey]: !p[showKey]}))} className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)] hover:text-[var(--text-secondary)]">
            {show?.[showKey] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
        )}
      </div>
      {hint && <p className="text-[10px] text-[var(--text-muted)] mt-0.5 opacity-60">{hint}</p>}
    </div>
  )
}
