import Link from 'next/link'
import { Upload, BarChart3, AlertTriangle, HelpCircle } from 'lucide-react'

export default function Home() {
  return (
    <div className="space-y-8">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold">LTE Band 41 RCA</h1>
        <p className="text-xl text-muted-foreground">
          Network Anomaly Analysis & Root Cause Analysis Tool
        </p>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mt-12">
        <Link
          href="/upload"
          className="p-6 border rounded-lg hover:bg-accent transition-colors"
        >
          <Upload className="h-8 w-8 mb-4" />
          <h2 className="text-xl font-semibold mb-2">Upload PM Data</h2>
          <p className="text-muted-foreground">
            Upload Ericsson ENM PM counter files (.xml.gz) for analysis
          </p>
        </Link>

        <Link
          href="/dashboard"
          className="p-6 border rounded-lg hover:bg-accent transition-colors"
        >
          <BarChart3 className="h-8 w-8 mb-4" />
          <h2 className="text-xl font-semibold mb-2">Dashboard</h2>
          <p className="text-muted-foreground">
            View KPI metrics, trends, and performance indicators
          </p>
        </Link>

        <Link
          href="/rca"
          className="p-6 border rounded-lg hover:bg-accent transition-colors"
        >
          <AlertTriangle className="h-8 w-8 mb-4" />
          <h2 className="text-xl font-semibold mb-2">RCA Analysis</h2>
          <p className="text-muted-foreground">
            Review root cause analysis results and recommendations
          </p>
        </Link>

        <Link
          href="/help"
          className="p-6 border rounded-lg hover:bg-accent transition-colors"
        >
          <HelpCircle className="h-8 w-8 mb-4" />
          <h2 className="text-xl font-semibold mb-2">Help & Reference</h2>
          <p className="text-muted-foreground">
            KPI parameters, ideal values, thresholds, and root cause classifications
          </p>
        </Link>
      </div>
    </div>
  )
}

