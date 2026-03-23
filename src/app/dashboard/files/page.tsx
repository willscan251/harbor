'use client'
import { useState } from 'react'
import { FolderOpen, FileText, ExternalLink, RefreshCw } from 'lucide-react'

export default function FilesPage() {
  const [view, setView] = useState<'browser' | 'log'>('browser')
  const spUrl = 'https://scanland.sharepoint.com/sites/TheScanlandGroup/Shared%20Documents/Forms/AllItems.aspx'

  return (
    <div className="animate-in" style={{ height: 'calc(100vh - 3rem)' }}>
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-2xl font-bold">Harbor Files</h1>
          <p className="text-sm text-[var(--text-muted)] mt-0.5">Browse your shared drive and sorted documents.</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="tab-bar">
            <button onClick={() => setView('browser')} className={`tab-item ${view === 'browser' ? 'active' : ''}`}>Browser</button>
            <button onClick={() => setView('log')} className={`tab-item ${view === 'log' ? 'active' : ''}`}>Sorted Log</button>
          </div>
          <a href={spUrl} target="_blank" className="btn-accent text-[11px] py-2"><ExternalLink className="w-3.5 h-3.5" /> Open External</a>
        </div>
      </div>

      {view === 'browser' ? (
        <div className="card overflow-hidden" style={{ height: 'calc(100vh - 10rem)' }}>
          <div className="bg-[var(--bg-raised)] px-4 py-2.5 border-b border-white/[0.04] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FolderOpen className="w-4 h-4 text-[var(--accent)]" />
              <span className="text-[12px] font-semibold text-[var(--text-secondary)]">Scanland & Co — Shared Documents</span>
            </div>
            <button onClick={() => { const f = document.getElementById('sp-frame') as HTMLIFrameElement; if (f) f.src = spUrl }}
              className="text-[11px] text-[var(--text-muted)] hover:text-[var(--text-secondary)] flex items-center gap-1">
              <RefreshCw className="w-3 h-3" /> Refresh
            </button>
          </div>
          <iframe id="sp-frame" src={spUrl} className="w-full border-none" style={{ height: 'calc(100% - 40px)' }} allow="fullscreen" />
        </div>
      ) : (
        <div className="card p-0 overflow-hidden">
          <div className="px-5 py-14 text-center">
            <FileText className="w-10 h-10 text-[var(--text-muted)] mx-auto mb-3 opacity-20" />
            <p className="text-[14px] font-medium text-[var(--text-secondary)]">Document log building</p>
            <p className="text-[12px] text-[var(--text-muted)] mt-1">Drop files into the Harbor Inbox to see sorted results here.</p>
          </div>
        </div>
      )}
    </div>
  )
}
