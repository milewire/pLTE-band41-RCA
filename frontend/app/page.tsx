import Link from 'next/link'
import { Upload, BarChart3, AlertTriangle, HelpCircle } from 'lucide-react'

export default function Home() {
  return (
    <div className="space-y-8 px-4 sm:px-6">
      <div className="text-center space-y-4">
        <h1 className="text-3xl sm:text-4xl font-bold">LTE Band 41 RCA</h1>
        <p className="text-lg sm:text-xl text-muted-foreground">
          Network Anomaly Analysis & Root Cause Analysis Tool
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 mt-8 sm:mt-12">
        <Link
          href="/upload"
          className="p-4 sm:p-6 border rounded-lg hover:bg-accent transition-colors min-h-[44px]"
        >
          <Upload className="h-6 w-6 sm:h-8 sm:w-8 mb-3 sm:mb-4" />
          <h2 className="text-lg sm:text-xl font-semibold mb-2">Upload PM Data</h2>
          <p className="text-sm sm:text-base text-muted-foreground">
            Upload Ericsson ENM PM counter files (.xml.gz) for analysis
          </p>
        </Link>

        <Link
          href="/dashboard"
          className="p-4 sm:p-6 border rounded-lg hover:bg-accent transition-colors min-h-[44px]"
        >
          <BarChart3 className="h-6 w-6 sm:h-8 sm:w-8 mb-3 sm:mb-4" />
          <h2 className="text-lg sm:text-xl font-semibold mb-2">Dashboard</h2>
          <p className="text-sm sm:text-base text-muted-foreground">
            View KPI metrics, trends, and performance indicators
          </p>
        </Link>

        <Link
          href="/rca"
          className="p-4 sm:p-6 border rounded-lg hover:bg-accent transition-colors min-h-[44px]"
        >
          <AlertTriangle className="h-6 w-6 sm:h-8 sm:w-8 mb-3 sm:mb-4" />
          <h2 className="text-lg sm:text-xl font-semibold mb-2">RCA Analysis</h2>
          <p className="text-sm sm:text-base text-muted-foreground">
            Review root cause analysis results and recommendations
          </p>
        </Link>

        <Link
          href="/help"
          className="p-4 sm:p-6 border rounded-lg hover:bg-accent transition-colors min-h-[44px]"
        >
          <HelpCircle className="h-6 w-6 sm:h-8 sm:w-8 mb-3 sm:mb-4" />
          <h2 className="text-lg sm:text-xl font-semibold mb-2">Help & Reference</h2>
          <p className="text-sm sm:text-base text-muted-foreground">
            KPI parameters, ideal values, thresholds, and root cause classifications
          </p>
        </Link>
      </div>
    </div>
  )
}

