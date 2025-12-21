'use client'

import { useState } from "react"
import { useMutation } from "@tanstack/react-query"
import { useRouter, useSearchParams } from "next/navigation"
import { api, RunOptions, Scraper } from "@/lib/api"
import { Button } from "@/components/ui/Button"
import { Input } from "@/components/ui/Input"
import { Play, Loader2, Settings2 } from "lucide-react"

interface RunScraperFormProps {
  scraper: Scraper
}

export function RunScraperForm({ scraper }: RunScraperFormProps) {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [url, setUrl] = useState(searchParams.get("url") || scraper.example_url || "")
  const [showOptions, setShowOptions] = useState(false)
  const [options, setOptions] = useState<RunOptions>({
    use_cache: true,
    async: true, // Default to async for better UX with progress bar
    skip_monitoring: false,
  })

  const mutation = useMutation({
    mutationFn: (variables: { url: string; options: RunOptions }) => 
      api.runScraper(scraper.scraper_id, variables.url, variables.options),
    onSuccess: (data) => {
      // Redirect to job results page
      router.push(`/jobs/${data.job_id}`)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!url) return
    mutation.mutate({ url, options })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="flex flex-col sm:flex-row gap-3">
        <Input 
          required
          type="url"
          placeholder="Enter URL to scrape (e.g. https://example.com/product/123)"
          className="flex-1 h-10"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />
        <Button 
          type="submit" 
          size="lg"
          disabled={mutation.isPending || !url}
          className="shrink-0"
        >
          {mutation.isPending ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Play className="mr-2 h-4 w-4" />
          )}
          Run Extraction
        </Button>
      </div>

      <div className="flex items-center justify-between text-sm">
        <button
          type="button"
          onClick={() => setShowOptions(!showOptions)}
          className="flex items-center text-zinc-500 hover:text-zinc-300 transition-colors"
        >
          <Settings2 className="h-4 w-4 mr-1" />
          {showOptions ? "Hide Options" : "Show Options"}
        </button>
      </div>

      {showOptions && (
        <div className="p-4 bg-zinc-900/50 rounded-lg border border-zinc-800 grid grid-cols-1 sm:grid-cols-2 gap-4">
          <label className="flex items-center space-x-2 cursor-pointer">
            <input 
              type="checkbox" 
              className="rounded border-zinc-700 bg-zinc-800 text-amber-600 focus:ring-amber-600"
              checked={options.use_cache}
              onChange={(e) => setOptions({ ...options, use_cache: e.target.checked })}
            />
            <span className="text-sm text-zinc-300">Use Cached Content</span>
          </label>
          
          <label className="flex items-center space-x-2 cursor-pointer">
            <input 
              type="checkbox" 
              className="rounded border-zinc-700 bg-zinc-800 text-amber-600 focus:ring-amber-600"
              checked={!options.skip_monitoring}
              onChange={(e) => setOptions({ ...options, skip_monitoring: !e.target.checked })}
            />
            <span className="text-sm text-zinc-300">Monitor this URL</span>
          </label>
        </div>
      )}

      {mutation.isError && (
        <div className="text-red-400 text-sm mt-2">
          Error: {(mutation.error as Error).message}
        </div>
      )}
    </form>
  )
}

