'use client'

import { use } from "react"
import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"
import { Button } from "@/components/ui/Button"
import { JobProgress } from "@/components/JobProgress"
import { ResultsViewer } from "@/components/ResultsViewer"
import { ArrowLeft, ExternalLink, RefreshCw, Play } from "lucide-react"
import Link from "next/link"
import { useEffect, useState } from "react"

export default function JobPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const [shouldPoll, setShouldPoll] = useState(true)

  const { data: job, isLoading, error, refetch } = useQuery({
    queryKey: ['job', id],
    queryFn: () => api.getStatus(id),
    refetchInterval: (query) => {
      // Stop polling if completed or failed, or if we explicitly stopped
      if (!shouldPoll || query.state.data?.status === 'completed' || query.state.data?.status === 'failed') {
        return false
      }
      return 1000 // Poll every 1s
    },
  })

  // Results query - only fetch when job is completed
  const { data: results } = useQuery({
    queryKey: ['results', id],
    queryFn: () => api.getResults(id),
    enabled: job?.status === 'completed',
  })

  useEffect(() => {
    if (job?.status === 'completed' || job?.status === 'failed') {
      setShouldPoll(false)
    }
  }, [job?.status])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-4 border-amber-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-zinc-400">Loading job details...</p>
        </div>
      </div>
    )
  }

  if (error || !job) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] text-center">
        <h2 className="text-xl font-bold text-red-500 mb-2">Failed to load job</h2>
        <p className="text-zinc-400 mb-4">{(error as Error)?.message || "Job not found"}</p>
        <Link href="/">
          <Button>Back to Dashboard</Button>
        </Link>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <div className="flex items-center justify-between mb-4">
          <Link 
            href={job.scraper_id ? `/scrapers/${job.scraper_id}` : "/"} 
            className="inline-flex items-center text-sm text-zinc-500 hover:text-zinc-300 transition-colors"
          >
            <ArrowLeft className="mr-1 h-4 w-4" />
            Back to Scraper
          </Link>
          
          <div className="font-mono text-xs text-zinc-600">
            Job ID: {id}
          </div>
        </div>
        
        <div className="flex items-center justify-between mb-2">
          <h1 className="text-2xl font-bold tracking-tight">Extraction Job</h1>
          {job.scraper_id && (
            <Link href={`/scrapers/${job.scraper_id}?url=${encodeURIComponent(job.url || '')}`}>
              <Button size="sm" variant="secondary">
                <Play className="h-4 w-4 mr-2" />
                Run Again
              </Button>
            </Link>
          )}
        </div>
        
        {job.url && (
          <div className="flex items-center gap-2 text-zinc-400 mb-6 bg-zinc-900/50 p-3 rounded-lg border border-zinc-800">
            <span className="text-sm font-medium text-zinc-500">Target:</span>
            <code className="text-sm flex-1 truncate">{job.url}</code>
            <a href={job.url} target="_blank" rel="noopener noreferrer" className="hover:text-amber-500 transition-colors">
              <ExternalLink className="h-4 w-4" />
            </a>
          </div>
        )}
      </div>

      {/* Progress Section */}
      <div className="bg-zinc-900/30 border border-zinc-800 rounded-xl p-6">
        <JobProgress job={job} />
      </div>

      {/* Results Section */}
      {job.status === 'completed' && results && (
        <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-700">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold">Extraction Results</h2>
            <Button size="sm" variant="outline" onClick={() => refetch()}>
              <RefreshCw className="h-3 w-3 mr-2" />
              Refresh
            </Button>
          </div>
          
          <ResultsViewer data={results.data} />
          
          {results.metadata && (
            <div className="bg-zinc-900/30 border border-zinc-800 rounded-lg p-4">
              <h3 className="text-sm font-medium text-zinc-400 mb-2">Metadata</h3>
              <pre className="text-xs text-zinc-500 overflow-auto max-h-40">
                {JSON.stringify(results.metadata, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
