'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Send, Loader2, Bot } from 'lucide-react'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function AskAIPage() {
  const router = useRouter()
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [answer, setAnswer] = useState<string | null>(null)
  const [confidence, setConfidence] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [hasData, setHasData] = useState(false)

  useEffect(() => {
    // Check if we're in the browser
    if (typeof window === 'undefined') return

    try {
      // Check if we have RCA results in session
      const storedResults = sessionStorage.getItem('rcaResults')
      const storedKpiData = sessionStorage.getItem('kpiData')
      setHasData(!!(storedResults && storedKpiData))
    } catch (error) {
      console.error('Error checking session data:', error)
      setHasData(false)
    }
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!question.trim()) {
      setError('Please enter a question')
      return
    }

    if (!hasData) {
      setError('Please upload and analyze a PM file first')
      return
    }

    setLoading(true)
    setError(null)
    setAnswer(null)
    setConfidence(null)

    try {
      // Check if we're in the browser
      if (typeof window === 'undefined') {
        setError('Browser environment required')
        setLoading(false)
        return
      }

      // Get stored data from session
      const storedResults = sessionStorage.getItem('rcaResults')
      const storedKpiData = sessionStorage.getItem('kpiData')

      const rcaResult = storedResults ? JSON.parse(storedResults) : null
      const kpiData = storedKpiData ? JSON.parse(storedKpiData) : []

      // Call the AI endpoint
      const response = await axios.post(`${API_URL}/ask-ai`, {
        question: question,
        kpi_data: kpiData,
        rca_result: rcaResult,
      })

      setAnswer(response.data.answer)
      setConfidence(response.data.confidence)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to get AI response')
    } finally {
      setLoading(false)
    }
  }

  const exampleQuestions = [
    "What is the root cause of the performance issues?",
    "What is the average RRC setup success rate?",
    "Are there any anomalies in the data?",
    "How is the PRB utilization trending?",
    "Compare performance across different sites",
  ]

  return (
    <div className="max-w-4xl mx-auto space-y-6 px-4 sm:px-6">
      <div>
        <h1 className="text-2xl sm:text-3xl font-bold mb-2">Ask RCA AI</h1>
        <p className="text-sm sm:text-base text-muted-foreground">
          Ask natural language questions about your KPI data and RCA analysis
        </p>
      </div>

      {!hasData && (
        <Alert>
          <AlertDescription>
            Please upload and analyze a PM file first to ask questions about the data.
            <button
              onClick={() => router.push('/upload')}
              className="ml-2 text-primary underline hover:no-underline"
            >
              Go to Upload
            </button>
          </AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Ask a Question</CardTitle>
          <CardDescription>Enter your question in plain English</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="e.g., What is the root cause of the performance issues?"
                className="w-full min-h-[120px] p-4 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-primary text-sm sm:text-base"
                disabled={loading || !hasData}
              />
            </div>
            <div className="flex items-center justify-between">
              <button
                type="submit"
                disabled={loading || !hasData || !question.trim()}
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-2.5 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm sm:text-base min-h-[44px]"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Asking AI...
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4" />
                    Ask RCA AI
                  </>
                )}
              </button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Example Questions */}
      <Card>
        <CardHeader>
          <CardTitle>Example Questions</CardTitle>
          <CardDescription>Try asking these questions</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {exampleQuestions.map((example, idx) => (
              <button
                key={idx}
                onClick={() => setQuestion(example)}
                className="block w-full text-left p-3 border rounded-lg hover:bg-accent transition-colors text-sm"
                disabled={loading || !hasData}
              >
                {example}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* AI Response */}
      {answer && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bot className="h-5 w-5" />
              AI Response
            </CardTitle>
            {confidence !== null && (
              <CardDescription>
                Confidence: {(confidence * 100).toFixed(0)}%
              </CardDescription>
            )}
          </CardHeader>
          <CardContent>
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <div className="whitespace-pre-wrap text-sm leading-relaxed space-y-3">
                {answer.split('\n').map((line, idx) => {
                  // Format numbered lists
                  if (/^\d+\.\s/.test(line)) {
                    return (
                      <div key={idx} className="ml-4">
                        <span className="font-semibold">{line.match(/^\d+\./)?.[0]}</span>
                        <span>{line.replace(/^\d+\.\s/, ' ')}</span>
                      </div>
                    )
                  }
                  // Format bold text (markdown **text**)
                  if (line.includes('**')) {
                    const parts = line.split(/(\*\*[^*]+\*\*)/g)
                    return (
                      <p key={idx}>
                        {parts.map((part, pIdx) => 
                          part.startsWith('**') && part.endsWith('**') ? (
                            <strong key={pIdx} className="font-semibold">
                              {part.slice(2, -2)}
                            </strong>
                          ) : (
                            <span key={pIdx}>{part}</span>
                          )
                        )}
                      </p>
                    )
                  }
                  // Regular paragraphs
                  return <p key={idx}>{line || '\u00A0'}</p>
                })}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Error Display */}
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
    </div>
  )
}

