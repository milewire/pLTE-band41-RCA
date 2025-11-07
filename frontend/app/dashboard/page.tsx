'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { AlertTriangle } from 'lucide-react'
import Link from 'next/link'

interface KPIData {
  timestamp: string
  site: string
  kpi: string
  value: number
}

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
  kpi_data: KPIData[]
}

export default function DashboardPage() {
  const router = useRouter()
  const [rcaResults, setRcaResults] = useState<RCAResults | null>(null)
  const [kpiData, setKpiData] = useState<KPIData[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check if we're in the browser
    if (typeof window === 'undefined') return

    try {
      const storedResults = sessionStorage.getItem('rcaResults')
      const storedKpiData = sessionStorage.getItem('kpiData')

      if (storedResults && storedKpiData) {
        setRcaResults(JSON.parse(storedResults))
        setKpiData(JSON.parse(storedKpiData))
      }
      setLoading(false)
    } catch (error) {
      console.error('Error loading dashboard data:', error)
      setLoading(false)
    }
  }, [router])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <p className="text-muted-foreground">Loading dashboard...</p>
      </div>
    )
  }

  if (!rcaResults || !kpiData.length) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold mb-2">Dashboard</h1>
          <p className="text-muted-foreground">KPI metrics and performance indicators</p>
        </div>
        <Card>
          <CardHeader>
            <CardTitle>No Data Available</CardTitle>
            <CardDescription>Upload and analyze PM data to view the dashboard</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              The dashboard displays KPI metrics, charts, and performance indicators from your analyzed PM data.
            </p>
            <Link
              href="/upload"
              className="inline-flex items-center px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
            >
              Go to Upload Page
            </Link>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Prepare time-series data
  const timeSeriesData = kpiData.reduce((acc, entry) => {
    const key = entry.timestamp
    if (!acc[key]) {
      acc[key] = { timestamp: entry.timestamp }
    }
    acc[key][entry.kpi] = entry.value
    return acc
  }, {} as Record<string, any>)

  const chartData = Object.values(timeSeriesData).slice(0, 50) // Limit to 50 points

  // Group KPIs by site
  const siteData = kpiData.reduce((acc, entry) => {
    if (!acc[entry.site]) {
      acc[entry.site] = {}
    }
    if (!acc[entry.site][entry.kpi]) {
      acc[entry.site][entry.kpi] = []
    }
    acc[entry.site][entry.kpi].push(entry.value)
    return acc
  }, {} as Record<string, Record<string, number[]>>)

  const siteSummary = Object.entries(siteData).map(([site, kpis]) => {
    const summary: any = { site }
    Object.entries(kpis).forEach(([kpi, values]) => {
      summary[kpi] = values.reduce((a, b) => a + b, 0) / values.length
    })
    return summary
  })

  const severityColors = {
    high: 'destructive',
    medium: 'bg-yellow-500/10 text-yellow-600 dark:text-yellow-400',
    low: 'bg-green-500/10 text-green-600 dark:text-green-400',
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">Dashboard</h1>
        <p className="text-muted-foreground">KPI metrics and performance indicators</p>
      </div>

      {/* Root Cause Summary */}
      {rcaResults.root_cause && (
        <Alert className={severityColors[rcaResults.severity as keyof typeof severityColors] || ''}>
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Root Cause: {rcaResults.root_cause}</AlertTitle>
          <AlertDescription>
            Severity: <span className="font-semibold">{rcaResults.severity?.toUpperCase() || 'UNKNOWN'}</span>
          </AlertDescription>
        </Alert>
      )}

      {/* KPI Statistics */}
      {rcaResults.evidence && Object.keys(rcaResults.evidence).length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-4 gap-4">
          {Object.entries(rcaResults.evidence).map(([kpi, stats]) => (
          <Card key={kpi}>
            <CardHeader>
              <CardTitle className="text-sm font-medium">{kpi}</CardTitle>
              <CardDescription>Statistics</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Mean:</span>
                  <span className="font-medium">{stats.mean.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Min:</span>
                  <span>{stats.min.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Max:</span>
                  <span>{stats.max.toFixed(2)}</span>
                </div>
                {stats.median !== undefined && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Median:</span>
                    <span>{stats.median.toFixed(2)}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Count:</span>
                  <span>{stats.count}</span>
                </div>
              </div>
            </CardContent>
          </Card>
          ))}
        </div>
      )}

      {/* Time Series Chart */}
      {chartData.length > 0 && rcaResults.evidence && (
        <Card>
          <CardHeader>
            <CardTitle>KPI Time Series</CardTitle>
            <CardDescription>Performance trends over time</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="timestamp" />
                <YAxis />
                <Tooltip />
                <Legend />
                {Object.keys(rcaResults.evidence || {}).slice(0, 5).map((kpi, idx) => (
                  <Line
                    key={kpi}
                    type="monotone"
                    dataKey={kpi}
                    stroke={`hsl(${idx * 60}, 70%, 50%)`}
                    strokeWidth={2}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* Site Comparison */}
      {siteSummary.length > 0 && rcaResults.evidence && (
        <Card>
          <CardHeader>
            <CardTitle>Site Comparison</CardTitle>
            <CardDescription>Average KPI values by site</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={siteSummary}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="site" />
                <YAxis />
                <Tooltip />
                <Legend />
                {Object.keys(rcaResults.evidence || {}).slice(0, 3).map((kpi, idx) => (
                  <Bar
                    key={kpi}
                    dataKey={kpi}
                    fill={`hsl(${idx * 60}, 70%, 50%)`}
                  />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

