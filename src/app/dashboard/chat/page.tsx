'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Anchor, Paperclip, FileText, Users, FolderOpen } from 'lucide-react'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

const suggestions = [
  { icon: Users, text: 'What meetings do we have this week?' },
  { icon: FileText, text: 'Summarize our last meeting with Baldwin ARC' },
  { icon: FolderOpen, text: 'Find the Striving for Greatness contract' },
  { icon: Users, text: 'How many pending tasks do we have?' },
]

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function handleSend() {
    if (!input.trim() || loading) return

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const res = await fetch('/api/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMsg.content,
          history: messages.map(m => ({ role: m.role, content: m.content })),
        }),
      })

      if (res.ok) {
        const data = await res.json()
        setMessages(prev => [...prev, {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: data.response || 'I couldn\'t process that request.',
          timestamp: new Date(),
        }])
      } else {
        setMessages(prev => [...prev, {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: 'Sorry, I encountered an error. Make sure the Anthropic API key is configured in Settings > Admin Keys.',
          timestamp: new Date(),
        }])
      }
    } catch (err) {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Connection error. Please check that the server is running.',
        timestamp: new Date(),
      }])
    }

    setLoading(false)
  }

  function handleSuggestion(text: string) {
    setInput(text)
  }

  return (
    <div className="animate-in flex flex-col" style={{ height: 'calc(100vh - 3rem)' }}>
      {/* Header */}
      <div className="mb-4">
        <h1 className="text-2xl font-bold">AI Assistant</h1>
        <p className="text-sm text-[var(--text-muted)] mt-1">Ask about clients, search files, get summaries, and manage tasks.</p>
      </div>

      {/* Chat Area */}
      <div className="flex-1 card p-0 flex flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center py-12">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-sky-600/20 to-teal-600/20 flex items-center justify-center mb-4">
                <Anchor className="w-7 h-7 text-[var(--teal)]" />
              </div>
              <h2 className="text-[16px] font-semibold mb-1">Harbor AI Assistant</h2>
              <p className="text-[13px] text-[var(--text-muted)] mb-6 max-w-md">
                I know about your clients, documents, meetings, and tasks. Ask me anything about your business.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-w-lg w-full">
                {suggestions.map((s, i) => (
                  <button key={i} onClick={() => handleSuggestion(s.text)}
                    className="flex items-center gap-2.5 px-4 py-3 rounded-xl bg-[var(--bg)] border border-[var(--border)] hover:border-[var(--teal)]/30 text-left transition text-[12px] text-[var(--text-secondary)] hover:text-[var(--text)]">
                    <s.icon className="w-4 h-4 text-[var(--teal)] shrink-0" />
                    <span>{s.text}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map(msg => (
            <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[75%] rounded-2xl px-4 py-3 ${
                msg.role === 'user'
                  ? 'bg-gradient-to-r from-sky-600/20 to-teal-600/20 border border-sky-500/10'
                  : 'bg-[var(--bg-raised)] border border-[var(--border)]'
              }`}>
                <p className="text-[13px] leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                <p className="text-[10px] text-[var(--text-muted)] mt-1.5">
                  {msg.timestamp.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}
                </p>
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-[var(--bg-raised)] border border-[var(--border)] rounded-2xl px-4 py-3">
                <div className="flex gap-1.5">
                  <div className="w-2 h-2 bg-[var(--teal)] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 bg-[var(--teal)] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 bg-[var(--teal)] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="p-4 border-t border-[var(--border)]">
          <div className="flex items-center gap-2">
            <button className="p-2.5 rounded-xl text-[var(--text-muted)] hover:text-[var(--text)] hover:bg-[var(--surface-hover)] transition" title="Attach file">
              <Paperclip className="w-4 h-4" />
            </button>
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleSend()}
              placeholder="Ask about clients, files, meetings..."
              className="input-dark flex-1"
              autoFocus
            />
            <button onClick={handleSend} disabled={!input.trim() || loading}
              className="btn-accent px-3 py-2.5 disabled:opacity-30 disabled:cursor-not-allowed">
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
