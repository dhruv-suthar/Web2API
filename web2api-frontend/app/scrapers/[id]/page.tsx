'use client'

import { use, useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"
import { Button } from "@/components/ui/Button"
import { Badge } from "@/components/ui/Badge"
import { RunScraperForm } from "@/components/RunScraperForm"
import { ApiUsageModal } from "@/components/ApiUsageModal"
import { Loader2, ArrowLeft, Clock, Link as LinkIcon, Code, Play, Terminal } from "lucide-react"
import Link from "next/link"
import Editor from "react-simple-code-editor"
import Prism from "prismjs"
import "prismjs/components/prism-clike"
import "prismjs/components/prism-javascript"
import "prismjs/components/prism-json"
import { formatDate } from "@/lib/utils"

export default function ScraperDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const [showApiModal, setShowApiModal] = useState(false)
  
  const { data: scraper, isLoading, error } = useQuery({
    queryKey: ['scraper', id],
    queryFn: () => api.getScraper(id),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Loader2 className="h-8 w-8 animate-spin text-amber-500" />
      </div>
    )
  }

  if (error || !scraper) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[50vh] text-center">
        <h2 className="text-xl font-bold text-red-500 mb-2">Failed to load scraper</h2>
        <p className="text-zinc-400 mb-4">{(error as Error)?.message || "Scraper not found"}</p>
        <Link href="/">
          <Button>Back to Dashboard</Button>
        </Link>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-12">
      <div className="flex items-center justify-between">
        <Link 
          href="/" 
          className="inline-flex items-center text-sm text-zinc-500 hover:text-zinc-300 transition-colors"
        >
          <ArrowLeft className="mr-1 h-4 w-4" />
          Back to Dashboard
        </Link>
        <Button 
          variant="outline" 
          size="sm" 
          onClick={() => setShowApiModal(true)}
          className="bg-zinc-900 border-zinc-800"
        >
          <Terminal className="h-4 w-4 mr-2" />
          API Endpoint
        </Button>
      </div>

      <div className="flex flex-col md:flex-row justify-between gap-4 md:items-start">
        <div>
          <h1 className="text-3xl font-bold tracking-tight mb-2">{scraper.name}</h1>
          <p className="text-zinc-400 max-w-2xl">{scraper.description || "No description provided"}</p>
        </div>
        <div className="flex gap-2">
          <div className="flex flex-col items-end text-sm text-zinc-500">
            <span>Created {formatDate(scraper.created_at)}</span>
            <span className="font-mono text-xs mt-1">ID: {scraper.scraper_id}</span>
          </div>
        </div>
      </div>

      {/* Main Action Area */}
      <div className="bg-zinc-900/50 border border-amber-500/20 rounded-xl p-6 md:p-8 shadow-lg shadow-amber-900/5 relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-amber-500 to-orange-600" />
        <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
          <Play className="h-5 w-5 text-amber-500" />
          Run Extraction
        </h2>
        <RunScraperForm scraper={scraper} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Configuration */}
        <div className="lg:col-span-2 space-y-8">
          <section>
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Code className="h-4 w-4" />
              Extraction Schema
            </h3>
            <div className="bg-[#1e1e1e] border border-zinc-800 rounded-lg overflow-hidden">
              {typeof scraper.schema === 'string' && !scraper.schema.trim().startsWith('{') ? (
                <div className="p-4 font-mono text-sm whitespace-pre-wrap text-zinc-300">
                  {scraper.schema}
                </div>
              ) : (
                <Editor
                  value={typeof scraper.schema === 'string' ? scraper.schema : JSON.stringify(scraper.schema, null, 2)}
                  onValueChange={() => {}}
                  highlight={(code) => {
                    try {
                      if (Prism.languages.json) return Prism.highlight(code, Prism.languages.json, 'json');
                      if (Prism.languages.javascript) return Prism.highlight(code, Prism.languages.javascript, 'javascript');
                      return Prism.highlight(code, Prism.languages.markup || {}, 'markup');
                    } catch (e) {
                      return code;
                    }
                  }}
                  padding={16}
                  readOnly
                  style={{
                    fontFamily: '"JetBrains Mono", "Fira Mono", monospace',
                    fontSize: 14,
                    backgroundColor: "#1e1e1e",
                  }}
                />
              )}
            </div>
          </section>
        </div>

        {/* Right Column: Metadata */}
        <div className="space-y-6">
          <div className="bg-zinc-900/30 border border-zinc-800 rounded-lg p-5">
            <h3 className="text-sm font-medium text-zinc-400 uppercase tracking-wider mb-4">Configuration</h3>
            
            <dl className="space-y-4 text-sm">
              <div>
                <dt className="text-zinc-500 mb-1">Schedule</dt>
                <dd className="font-medium flex items-center gap-2">
                  {scraper.schedule ? (
                    <>
                      <Clock className="h-4 w-4 text-amber-500" />
                      <span>{scraper.schedule}</span>
                    </>
                  ) : (
                    <span className="text-zinc-600">No schedule</span>
                  )}
                </dd>
              </div>
              
              <div>
                <dt className="text-zinc-500 mb-1">Webhook URL</dt>
                <dd className="font-mono text-xs truncate" title={scraper.webhook_url}>
                  {scraper.webhook_url || <span className="text-zinc-600">None</span>}
                </dd>
              </div>

              <div>
                <dt className="text-zinc-500 mb-1">Base URL</dt>
                <dd className="truncate">
                  {scraper.example_url ? (
                    <div className="flex items-center gap-1">
                      <LinkIcon className="h-3 w-3 text-zinc-500" />
                      <a href={scraper.example_url} target="_blank" rel="noopener noreferrer" className="hover:text-amber-500 transition-colors">
                        {new URL(scraper.example_url).hostname}
                      </a>
                    </div>
                  ) : (
                    <span className="text-zinc-600">None</span>
                  )}
                </dd>
              </div>
            </dl>
          </div>
        </div>
      </div>

      <ApiUsageModal 
        scraper={scraper} 
        open={showApiModal} 
        onClose={() => setShowApiModal(false)} 
      />
    </div>
  )
}
