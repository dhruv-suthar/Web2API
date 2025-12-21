'use client'

import { JobResult } from "@/lib/api"
import { cn } from "@/lib/utils"
import { Loader2, CheckCircle2, XCircle, Clock } from "lucide-react"

interface JobProgressProps {
  job: JobResult
}

export function JobProgress({ job }: JobProgressProps) {
  const percent = job.percent || 0
  const isCompleted = job.status === "completed"
  const isFailed = job.status === "failed"
  const isProcessing = !isCompleted && !isFailed

  return (
    <div className="space-y-4 w-full">
      <div className="flex justify-between items-end mb-1">
        <div className="flex items-center gap-2">
          {isProcessing && <Loader2 className="h-4 w-4 animate-spin text-amber-500" />}
          {isCompleted && <CheckCircle2 className="h-4 w-4 text-green-500" />}
          {isFailed && <XCircle className="h-4 w-4 text-red-500" />}
          <span className="font-medium capitalize text-zinc-200">
            {job.status === "queued" ? "Queued..." : 
             job.status === "fetching" ? "Fetching content..." :
             job.status === "extracting" ? "Extracting data..." :
             job.status === "completed" ? "Extraction Complete" :
             job.status === "failed" ? "Extraction Failed" : job.status}
          </span>
        </div>
        <span className="text-sm font-mono text-zinc-400">{percent}%</span>
      </div>
      
      <div className="h-2 w-full bg-zinc-800 rounded-full overflow-hidden">
        <div 
          className={cn(
            "h-full transition-all duration-500 ease-out",
            {
              "bg-amber-500": isProcessing,
              "bg-green-500": isCompleted,
              "bg-red-500": isFailed,
              "animate-pulse": isProcessing && percent < 100
            }
          )}
          style={{ width: `${Math.max(5, percent)}%` }}
        />
      </div>

      {job.message && (
        <p className="text-sm text-zinc-500">{job.message}</p>
      )}
      
      {job.error && (
        <div className="p-3 bg-red-900/20 border border-red-900/50 rounded text-red-400 text-sm flex gap-2 items-start">
          <XCircle className="h-4 w-4 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold block mb-1">Error in {job.stage || "process"}</span>
            {job.error}
          </div>
        </div>
      )}
    </div>
  )
}

