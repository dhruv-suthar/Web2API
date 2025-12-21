'use client'

import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"
import { MonitorsTable } from "@/components/MonitorsTable"
import { Loader2, Activity } from "lucide-react"
import { Button } from "@/components/ui/Button"

export default function MonitorsPage() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['monitors'],
    queryFn: () => api.listMonitors(),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Loader2 className="h-8 w-8 animate-spin text-amber-500" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] text-center">
        <h2 className="text-xl font-bold text-red-500 mb-2">Failed to load monitors</h2>
        <p className="text-zinc-400 mb-4">{(error as Error).message}</p>
        <Button onClick={() => refetch()}>Retry</Button>
      </div>
    )
  }

  const monitors = data?.monitors || []

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight mb-2">Monitors</h1>
          <p className="text-zinc-400">Manage your scheduled scraping jobs.</p>
        </div>
        <div className="flex items-center gap-2 bg-zinc-900/50 px-3 py-1.5 rounded-md border border-zinc-800">
          <Activity className="h-4 w-4 text-amber-500" />
          <span className="text-sm font-medium">{data?.active_count || 0} Active</span>
        </div>
      </div>

      <MonitorsTable monitors={monitors} />
    </div>
  )
}

