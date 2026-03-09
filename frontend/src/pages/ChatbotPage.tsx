import { motion } from 'framer-motion'
import { useQuery, useMutation } from '@tanstack/react-query'
import { useState, useEffect, useRef } from 'react'
import { Send, Plus, Trash2 } from 'lucide-react'
import api from '@/api/axios'
import { useAuthStore } from '@/store/authStore'

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 px-4 py-3 glass-card w-20">
      {[0, 0.2, 0.4].map((delay) => (
        <motion.div
          key={delay}
          className="w-2 h-2 rounded-full bg-accent-blue"
          animate={{ y: [0, -6, 0] }}
          transition={{ duration: 0.6, delay, repeat: Infinity }}
        />
      ))}
    </div>
  )
}

export default function ChatbotPage() {
  const { accessToken } = useAuthStore()
  const [currentConvId, setCurrentConvId] = useState<string | null>(null)
  const [message, setMessage] = useState('')
  const [messages, setMessages] = useState<Array<{ role: string; content: string }>>([])
  const [isTyping, setIsTyping] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const { data: conversations } = useQuery({
    queryKey: ['conversations'],
    queryFn: () => api.get('/chat/conversations/').then((r) => r.data.results || r.data),
  })

  const { data: history } = useQuery({
    queryKey: ['chat-history', currentConvId],
    queryFn: () =>
      api.get(`/chat/conversations/${currentConvId}/history/`).then((r) => r.data),
    enabled: !!currentConvId,
  })

  // Sync history to messages when loaded
  useEffect(() => {
    if (history) setMessages(history as any[])
  }, [history])

  useEffect(() => {
    if (accessToken) {
      const wsUrl = `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws/chat/${currentConvId ? currentConvId + '/' : ''}?token=${accessToken}`
      const ws = new WebSocket(wsUrl)

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        setIsTyping(false)
        if (data.type === 'bot_message') {
          setMessages((prev) => [...prev, { role: 'bot', content: data.message }])
          if (data.conversation_id && !currentConvId) {
            setCurrentConvId(data.conversation_id)
          }
        }
      }

      ws.onerror = () => setIsTyping(false)
      wsRef.current = ws

      return () => ws.close()
    }
  }, [accessToken, currentConvId])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping])

  const sendMessage = () => {
    if (!message.trim() || !wsRef.current) return
    const userMsg = message.trim()
    setMessages((prev) => [...prev, { role: 'user', content: userMsg }])
    setMessage('')
    setIsTyping(true)
    wsRef.current.send(JSON.stringify({ message: userMsg }))
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="max-w-5xl mx-auto h-[calc(100vh-96px)] flex gap-4">
      {/* Conversation List */}
      <div className="w-64 glass-card p-4 flex flex-col gap-3 overflow-hidden">
        <button
          onClick={() => { setCurrentConvId(null); setMessages([]) }}
          className="flex items-center gap-2 w-full px-3 py-2 rounded-lg glow-button text-white text-sm font-medium"
        >
          <Plus size={16} /> New Chat
        </button>
        <div className="flex-1 overflow-y-auto space-y-1">
          {conversations?.map((conv: any) => (
            <button
              key={conv.id}
              onClick={() => setCurrentConvId(conv.id)}
              className={`w-full text-left px-3 py-2 rounded-lg text-sm truncate transition-all ${
                currentConvId === conv.id
                  ? 'bg-accent-blue/20 text-accent-blue'
                  : 'text-slate-400 hover:bg-white/5 hover:text-white'
              }`}
            >
              {conv.title || 'Chat'}
            </button>
          ))}
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col glass-card overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-white/5 flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-accent-blue to-accent-purple flex items-center justify-center">
            <span className="text-white text-xs font-bold">AI</span>
          </div>
          <div>
            <p className="text-white font-medium text-sm">CareerBot</p>
            <p className="text-slate-500 text-xs">Always here to help</p>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-16">
              <div className="w-16 h-16 rounded-2xl bg-accent-blue/10 border border-accent-blue/20 flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">🤖</span>
              </div>
              <p className="text-white font-medium mb-2">Ask me anything about your career</p>
              <p className="text-slate-500 text-sm">CV tips, job search, interview prep...</p>
            </div>
          )}
          {messages.map((msg, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[70%] px-4 py-3 rounded-2xl text-sm ${
                  msg.role === 'user'
                    ? 'bg-gradient-to-r from-accent-blue to-accent-purple text-white rounded-tr-sm'
                    : 'glass-card text-slate-200 rounded-tl-sm'
                }`}
              >
                {msg.content}
              </div>
            </motion.div>
          ))}
          {isTyping && (
            <div className="flex justify-start">
              <TypingIndicator />
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-4 border-t border-white/5">
          <div className="flex items-end gap-3">
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about your career, CV, interviews..."
              rows={1}
              className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-accent-blue/50 resize-none text-sm"
            />
            <motion.button
              onClick={sendMessage}
              disabled={!message.trim()}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="glow-button p-3 rounded-xl text-white disabled:opacity-40"
            >
              <Send size={18} />
            </motion.button>
          </div>
        </div>
      </div>
    </div>
  )
}
