
import { useState, useRef, useEffect } from 'react'
import { sendChatMessage, type ChatSource } from '../services/api'

interface Message {
  role: 'user' | 'assistant'
  content: string
  sources?: ChatSource[]
  contextUsed?: boolean
  latency?: number
}

const STORAGE_KEY = 'smart-farming-chat-history'

const WELCOME_MESSAGE: Message = {
  role: 'assistant',
  content:
    'Vanakkam! Welcome to Smart Farming AI. Ask me any question about agriculture, crops, soil or farming practices.',
}

export default function ChatBot() {
  const [messages, setMessages] = useState<Message[]>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved) return JSON.parse(saved) as Message[]
    } catch {
      console.error('Could not load chat history')
    }
    return [WELCOME_MESSAGE]
  })

  const [question, setQuestion] = useState('')
  const [language, setLanguage] = useState<'English' | 'Tamil'>('English')
  const [loading, setLoading] = useState(false)

  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(messages))
    } catch {
      console.error('Could not save chat history')
    }
  }, [messages])

  async function handleSend() {
    const text = question.trim()
    if (!text || loading) return

    setMessages((prev) => [...prev, { role: 'user', content: text }])
    setQuestion('')
    setLoading(true)

    try {
      const response = await sendChatMessage({
        question: text,
        language,
      })

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: response.answer,
          sources: response.sources,
          contextUsed: response.context_used,
          latency: response.latency_seconds,
        },
      ])
    } catch (error) {
      console.error('Chat request failed:', error)

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content:
            'Sorry, I could not connect to the farming assistant. Please check whether the backend is running and try again.',
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  function clearChat() {
    setMessages([WELCOME_MESSAGE])
    localStorage.removeItem(STORAGE_KEY)
  }

  return (
    <div className="min-h-screen bg-green-50 p-4 md:p-8">
      <div className="mx-auto flex max-w-4xl flex-col overflow-hidden rounded-2xl bg-white shadow-lg">

        <div className="bg-green-700 p-6 text-white">
          <h1 className="text-2xl font-bold">🌾 Smart Farming AI</h1>
          <p className="mt-1 text-sm text-green-100">
            Your AI-powered agricultural assistant
          </p>
        </div>

        <div className="flex items-center justify-between border-b p-4">
          <span className="font-medium text-gray-700">
            Agricultural Assistant
          </span>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={clearChat}
              className="rounded-lg border border-red-200 px-3 py-2 text-sm text-red-600 hover:bg-red-50"
            >
              Clear Chat
            </button>

            <select
              value={language}
              onChange={(e) =>
                setLanguage(e.target.value as 'English' | 'Tamil')
              }
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
            >
              <option value="English">English</option>
              <option value="Tamil">தமிழ்</option>
            </select>
          </div>
        </div>

        <div className="flex min-h-[400px] flex-1 flex-col gap-4 overflow-y-auto bg-gray-50 p-4 md:p-6">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`max-w-[90%] rounded-xl p-4 ${
                message.role === 'user'
                  ? 'self-end bg-green-700 text-white'
                  : 'self-start border bg-white text-gray-800 shadow-sm'
              }`}
            >
              <p className="whitespace-pre-wrap text-sm leading-6">
                {message.content}
              </p>

              {message.role === 'assistant' &&
                message.sources &&
                message.sources.length > 0 && (
                  <div className="mt-4 border-t pt-3">
                    <p className="mb-2 text-xs font-semibold text-gray-600">
                      📚 Sources
                    </p>

                    {message.sources.map((source, i) => (
                      <div
                        key={`${source.source}-${source.page}-${i}`}
                        className="mb-1 text-xs text-gray-500"
                      >
                        {source.source} — Page {source.page}
                        {' '}({(source.score * 100).toFixed(1)}% similarity)
                      </div>
                    ))}
                  </div>
                )}

              {message.role === 'assistant' &&
                message.contextUsed !== undefined && (
                  <p className="mt-3 text-xs text-gray-400">
                    {message.contextUsed
                      ? 'Knowledge base context used'
                      : 'No relevant knowledge base context found'}
                    {message.latency !== undefined &&
                      ` • ${message.latency.toFixed(2)}s`}
                  </p>
                )}
            </div>
          ))}

          {loading && (
            <div className="self-start rounded-xl border bg-white p-4 text-sm text-gray-500">
              🌱 Thinking... Generating your farming advice
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        <div className="border-t bg-white p-4">
          <form
            onSubmit={(e) => {
              e.preventDefault()
              void handleSend()
            }}
            className="flex gap-2"
          >
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask your farming question..."
              disabled={loading}
              className="min-w-0 flex-1 rounded-xl border border-gray-300 px-4 py-3 text-sm outline-none focus:border-green-600 focus:ring-2 focus:ring-green-100"
            />

            <button
              type="submit"
              disabled={loading || !question.trim()}
              className="rounded-xl bg-green-700 px-5 py-3 font-medium text-white hover:bg-green-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Send
            </button>
          </form>

          <p className="mt-2 text-center text-xs text-gray-400">
            Powered by IBM Granite and agricultural knowledge retrieval
          </p>
        </div>

      </div>
    </div>
  )
}
