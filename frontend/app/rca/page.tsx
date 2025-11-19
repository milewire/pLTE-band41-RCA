'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import axios from 'axios'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { AlertTriangle, CheckCircle2, XCircle, Info } from 'lucide-react'

interface Evidence {
  [kpi: string]: {
    mean: number
    min: number
    max: number
    median?: number
    stdev?: number
    count: number
  }
}

interface RCAResults {
  root_cause: string
  severity: string
  evidence: Evidence
  anomalies: Array<{
    kpi: string
    type: string
    value: number
    threshold: number
    severity: string
  }>
  recommendations: string[]
  kpi_data: any[]
  // AI-enhanced fields
  ai_summary?: string
  anomaly_detection?: {
    scores?: number[]
    flags?: boolean[]
    anomaly_count?: number
    anomaly_periods?: string[]
  }
  drift?: {
    drift_score?: number
    parameters_of_interest?: string[]
    drift_details?: Record<string, any>
  }
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function RCAPage() {
  const router = useRouter()
  const [rcaResults, setRcaResults] = useState<RCAResults | null>(null)
  const [loading, setLoading] = useState(true)
  const [reportLoading, setReportLoading] = useState(false)
  const [reportError, setReportError] = useState<string | null>(null)

  useEffect(() => {
    // Check if we're in the browser
    if (typeof window === 'undefined') return

    try {
      const storedResults = sessionStorage.getItem('rcaResults')
      if (storedResults) {
        setRcaResults(JSON.parse(storedResults))
        setLoading(false)
      } else {
        router.push('/upload')
      }
    } catch (error) {
      console.error('Error loading RCA data:', error)
      router.push('/upload')
    }
  }, [router])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <p className="text-muted-foreground">Loading RCA analysis...</p>
      </div>
    )
  }

  if (!rcaResults) {
    return null
  }

  const severityConfig = {
    high: {
      color: 'destructive',
      icon: XCircle,
      label: 'High',
    },
    medium: {
      color: 'bg-yellow-500/10 text-yellow-600 dark:text-yellow-400',
      icon: AlertTriangle,
      label: 'Medium',
    },
    low: {
      color: 'bg-green-500/10 text-green-600 dark:text-green-400',
      icon: CheckCircle2,
      label: 'Low',
    },
  }

  const severity = severityConfig[rcaResults.severity as keyof typeof severityConfig] || severityConfig.low
  const SeverityIcon = severity.icon

  const handleGenerateReport = async () => {
    if (typeof window === 'undefined') return
    setReportLoading(true)
    setReportError(null)

    try {
      const alarmSummary = sessionStorage.getItem('alarmSummary')
      const backhaulSummary = sessionStorage.getItem('backhaulSummary')
      const attachSummary = sessionStorage.getItem('attachSummary')

      const payload = {
        siteId: rcaResults.kpi_data?.[0]?.site ?? 'Unknown',
        timestampRange: {
          start: rcaResults.kpi_data?.[0]?.timestamp ?? null,
          end: rcaResults.kpi_data?.[rcaResults.kpi_data.length - 1]?.timestamp ?? null,
        },
        rcaResult: rcaResults,
        kpiSummary: rcaResults.evidence,
        alarmSummary: alarmSummary ? JSON.parse(alarmSummary) : null,
        backhaulSummary: backhaulSummary ? JSON.parse(backhaulSummary) : null,
        attachSummary: attachSummary ? JSON.parse(attachSummary) : null,
      }

      const response = await axios.post(`${API_URL}/incident-report`, payload, {
        responseType: 'blob',
      })

      const blob = new Blob([response.data], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'ran_copilot_incident_report.pdf'
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)
    } catch (err: any) {
      setReportError(err.response?.data?.detail || 'Failed to generate incident report')
    } finally {
      setReportLoading(false)
    }
  }

  return (
    <div className="space-y-6 px-4 sm:px-6">
      <div>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold mb-2">Root Cause Analysis</h1>
            <p className="text-sm sm:text-base text-muted-foreground">
              Detailed analysis results and recommendations
            </p>
          </div>
          <button
            type="button"
            onClick={handleGenerateReport}
            disabled={reportLoading}
            className="inline-flex items-center justify-center px-4 py-2.5 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed text-sm sm:text-base min-h-[44px]"
          >
            {reportLoading ? 'Generating Report…' : 'Generate Incident Report (PDF)'}
          </button>
        </div>
        {reportError && (
          <p className="mt-2 text-xs text-destructive">
            {reportError}
          </p>
        )}
      </div>

      {/* AI RCA Summary - Feature A */}
      {rcaResults.ai_summary && (
        <Card>
          <CardHeader>
            <CardTitle>AI RCA Summary</CardTitle>
            <CardDescription>AI-generated analysis summary</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <pre className="whitespace-pre-wrap font-sans text-sm">{rcaResults.ai_summary}</pre>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Root Cause Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Root Cause Classification</CardTitle>
          <CardDescription>Primary issue identified</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-4">
            <SeverityIcon className={`h-8 w-8 ${severity.color.includes('text-') ? severity.color : ''}`} />
            <div>
              <p className="text-2xl font-bold">{rcaResults.root_cause}</p>
              <p className={`text-sm ${severity.color}`}>
                Severity: {severity.label.toUpperCase()}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Anomaly Detection Flags - Feature B */}
      {rcaResults.anomaly_detection && (
        <Card>
          <CardHeader>
            <CardTitle>Anomaly Detection (ML Model)</CardTitle>
            <CardDescription>IsolationForest-based anomaly detection results</CardDescription>
          </CardHeader>
          <CardContent>
            {rcaResults.anomaly_detection.anomaly_count !== undefined && (
              <div className="space-y-4">
                <div className="flex items-center gap-4">
                  <AlertTriangle className="h-6 w-6 text-yellow-600 dark:text-yellow-400" />
                  <div>
                    <p className="text-lg font-semibold">
                      {rcaResults.anomaly_detection.anomaly_count} Anomalous Periods Detected
                    </p>
                    {rcaResults.anomaly_detection.scores && rcaResults.anomaly_detection.scores.length > 0 && (
                      <p className="text-sm text-muted-foreground">
                        Max Anomaly Score: {Math.max(...rcaResults.anomaly_detection.scores).toFixed(2)}
                      </p>
                    )}
                  </div>
                </div>
                {rcaResults.anomaly_detection.anomaly_periods && rcaResults.anomaly_detection.anomaly_periods.length > 0 && (
                  <div>
                    <p className="text-sm font-medium mb-2">Anomaly Periods:</p>
                    <div className="flex flex-wrap gap-2">
                      {rcaResults.anomaly_detection.anomaly_periods.slice(0, 10).map((period, idx) => (
                        <span key={idx} className="px-2 py-1 bg-destructive/10 text-destructive rounded text-xs">
                          {period}
                        </span>
                      ))}
                      {rcaResults.anomaly_detection.anomaly_periods.length > 10 && (
                        <span className="px-2 py-1 text-muted-foreground text-xs">
                          +{rcaResults.anomaly_detection.anomaly_periods.length - 10} more
                        </span>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Drift Indicator - Feature C */}
      {rcaResults.drift && rcaResults.drift.drift_score !== undefined && (
        <Card>
          <CardHeader>
            <CardTitle>Parameter Drift Detection</CardTitle>
            <CardDescription>Baseline comparison and drift analysis</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                {rcaResults.drift.drift_score > 0.3 ? (
                  <AlertTriangle className="h-6 w-6 text-yellow-600 dark:text-yellow-400" />
                ) : (
                  <CheckCircle2 className="h-6 w-6 text-green-600 dark:text-green-400" />
                )}
                <div>
                  <p className="text-lg font-semibold">
                    Drift Score: {(rcaResults.drift.drift_score * 100).toFixed(1)}%
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {rcaResults.drift.drift_score > 0.3
                      ? 'Significant drift detected'
                      : 'Parameters within normal range'}
                  </p>
                </div>
              </div>
              {rcaResults.drift.parameters_of_interest && rcaResults.drift.parameters_of_interest.length > 0 && (
                <div>
                  <p className="text-sm font-medium mb-2">Parameters Showing Drift:</p>
                  <div className="flex flex-wrap gap-2">
                    {rcaResults.drift.parameters_of_interest.map((param, idx) => (
                      <span key={idx} className="px-2 py-1 bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 rounded text-xs">
                        {param}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Anomalies */}
      {rcaResults.anomalies && Array.isArray(rcaResults.anomalies) && rcaResults.anomalies.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Detected Anomalies</CardTitle>
            <CardDescription>{rcaResults.anomalies.length} anomaly(ies) found</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {rcaResults.anomalies.map((anomaly, idx) => {
                const anomalySeverity = severityConfig[anomaly.severity as keyof typeof severityConfig] || severityConfig.medium
                const AnomalyIcon = anomalySeverity.icon
                return (
                  <Alert key={idx} className={anomalySeverity.color}>
                    <AnomalyIcon className="h-4 w-4" />
                    <AlertTitle>{anomaly.kpi}</AlertTitle>
                    <AlertDescription>
                      <div className="space-y-1 mt-2">
                        <p>
                          <span className="font-medium">Type:</span> {anomaly.type}
                        </p>
                        <p>
                          <span className="font-medium">Value:</span> {anomaly.value.toFixed(2)}
                        </p>
                        <p>
                          <span className="font-medium">Threshold:</span> {anomaly.threshold}
                        </p>
                        <p>
                          <span className="font-medium">Severity:</span> {anomaly.severity}
                        </p>
                      </div>
                    </AlertDescription>
                  </Alert>
                )
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Evidence */}
      {rcaResults.evidence && Object.keys(rcaResults.evidence).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Evidence</CardTitle>
            <CardDescription>KPI statistics and measurements</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(rcaResults.evidence).map(([kpi, stats]) => (
              <div key={kpi} className="p-4 border rounded-lg">
                <h3 className="font-semibold mb-2 text-sm">{kpi}</h3>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Mean:</span>
                    <span className="font-medium">{stats.mean.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Range:</span>
                    <span>{stats.min.toFixed(2)} - {stats.max.toFixed(2)}</span>
                  </div>
                  {stats.median !== undefined && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Median:</span>
                      <span>{stats.median.toFixed(2)}</span>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Samples:</span>
                    <span>{stats.count}</span>
                  </div>
                </div>
              </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recommendations */}
      <Card>
        <CardHeader>
          <CardTitle>Recommendations</CardTitle>
          <CardDescription>Recommended actions to resolve issues</CardDescription>
        </CardHeader>
        <CardContent>
          {rcaResults.recommendations && Array.isArray(rcaResults.recommendations) && rcaResults.recommendations.length > 0 ? (
            <ul className="space-y-2">
              {rcaResults.recommendations.map((rec, idx) => (
                <li key={idx} className="flex gap-3">
                  <Info className="h-5 w-5 text-primary mt-0.5 flex-shrink-0" />
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-muted-foreground">No specific recommendations available.</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

