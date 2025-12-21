'use client'

import { useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Monitor, api } from "@/lib/api"
import { Button } from "@/components/ui/Button"
import { Badge } from "@/components/ui/Badge"
import { formatDate } from "@/lib/utils"
import { Trash2, ExternalLink, Clock, Activity, Loader2 } from "lucide-react"

interface MonitorsTableProps {
  monitors: Monitor[]
}

export function MonitorsTable({ monitors }: MonitorsTableProps) {
  const queryClient = useQueryClient()
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.deleteMonitor(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['monitors'] })
      // Also invalidate stats on dashboard if needed
      queryClient.invalidateQueries({ queryKey: ['scrapers'] })
    },
    onSettled: () => {
      setDeletingId(null)
    }
  })

  const handleDelete = (id: string) => {
    if (confirm("Are you sure you want to delete this monitor?")) {
      setDeletingId(id)
      deleteMutation.mutate(id)
    }
  }

  if (monitors.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 border border-dashed border-zinc-800 rounded-lg bg-zinc-900/30 text-center">
        <Activity className="h-10 w-10 text-zinc-600 mb-3" />
        <h3 className="text-lg font-medium mb-1">No active monitors</h3>
        <p className="text-zinc-400 max-w-sm">
          Monitors are created automatically when you create a scraper with a schedule and URLs to monitor.
        </p>
      </div>
    )
  }

  return (
    <div className="border border-zinc-800 rounded-lg overflow-hidden bg-zinc-900/30">
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="bg-zinc-900/50 text-zinc-400 font-medium border-b border-zinc-800">
            <tr>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">URL</th>
              <th className="px-4 py-3">Schedule</th>
              <th className="px-4 py-3">Last Run</th>
              <th className="px-4 py-3">Next Run</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800">
            {monitors.map((monitor) => (
              <tr key={monitor.monitor_id} className="hover:bg-zinc-900/50 transition-colors">
                <td className="px-4 py-3">
                  <Badge variant={monitor.active ? "success" : "secondary"} className="capitalize">
                    {monitor.active ? "Active" : "Inactive"}
                  </Badge>
                </td>
                <td className="px-4 py-3 max-w-[300px]">
                  <div className="flex items-center gap-2 overflow-hidden">
                    <span className="truncate font-mono text-xs text-zinc-300" title={monitor.url}>
                      {monitor.url}
                    </span>
                    <a 
                      href={monitor.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-zinc-500 hover:text-amber-500 flex-shrink-0"
                    >
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  </div>
                  <div className="text-xs text-zinc-500 mt-0.5">
                    Scraper: {monitor.scraper_id}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-1.5 text-zinc-300">
                    <Clock className="h-3.5 w-3.5 text-zinc-500" />
                    {/* Assuming we might want to display interval or cron here if available in the monitor object, 
                        but standard Monitor interface might abstract this. 
                        Let's infer from context or just show 'Scheduled' if detail missing */}
                    <span>Scheduled</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-zinc-400">
                  {formatDate(monitor.last_run)}
                  {monitor.run_count !== undefined && monitor.run_count > 0 && (
                    <span className="ml-2 text-xs text-zinc-600">({monitor.run_count} runs)</span>
                  )}
                </td>
                <td className="px-4 py-3 text-zinc-400">
                  {formatDate(monitor.next_run)}
                </td>
                <td className="px-4 py-3 text-right">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 w-8 p-0 text-zinc-500 hover:text-red-500 hover:bg-red-950/30"
                    onClick={() => handleDelete(monitor.monitor_id)}
                    disabled={deletingId === monitor.monitor_id}
                  >
                    {deletingId === monitor.monitor_id ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Trash2 className="h-4 w-4" />
                    )}
                    <span className="sr-only">Delete</span>
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

