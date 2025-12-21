'use client'

import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"
import { ScraperCard } from "@/components/ScraperCard"
import { Button } from "@/components/ui/Button"
import { Plus, Loader2, Database, Activity } from "lucide-react"
import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card"

export default function Dashboard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['scrapers'],
    queryFn: api.listScrapers,
  })

  const { data: monitors } = useQuery({
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
        <h2 className="text-xl font-bold text-red-500 mb-2">Failed to load scrapers</h2>
        <p className="text-zinc-400 mb-4">{(error as Error).message}</p>
        <Button onClick={() => window.location.reload()}>Retry</Button>
      </div>
    )
  }

  const scrapers = data?.scrapers || []
  const activeMonitors = monitors?.active_count || 0

  return (
    <div className="space-y-8">
      {/* Stats Section */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Scrapers</CardTitle>
            <Database className="h-4 w-4 text-zinc-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{scrapers.length}</div>
          </CardContent>
        </Card>
        
        <Card className="bg-zinc-900/50 border-zinc-800">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Monitors</CardTitle>
            <Activity className="h-4 w-4 text-amber-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-500">{activeMonitors}</div>
          </CardContent>
        </Card>
      </div>

      {/* Scrapers List */}
      <div className="flex flex-col gap-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold tracking-tight">Your Scrapers</h2>
          <Link href="/scrapers/new">
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              New Scraper
            </Button>
          </Link>
        </div>

        {scrapers.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 border border-dashed border-zinc-800 rounded-lg bg-zinc-900/30">
            <Database className="h-12 w-12 text-zinc-600 mb-4" />
            <h3 className="text-lg font-medium mb-2">No scrapers yet</h3>
            <p className="text-zinc-400 mb-6 text-center max-w-md">
              Create your first scraper to start extracting data from any website using AI.
            </p>
            <Link href="/scrapers/new">
              <Button>Create Scraper</Button>
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {scrapers.map((scraper) => (
              <ScraperCard key={scraper.scraper_id} scraper={scraper} />
            ))}
          </div>
        )}
        </div>
    </div>
  )
}
