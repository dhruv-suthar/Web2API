'use client'

import React, { useState } from 'react'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "./ui/Card"
import { Badge } from "./ui/Badge"
import { Button } from "./ui/Button"
import { Play, Clock, Code } from "lucide-react"
import Link from "next/link"
import { Scraper } from "@/lib/api"
import { formatDate } from "@/lib/utils"
import { ApiUsageModal } from './ApiUsageModal'

interface ScraperCardProps {
  scraper: Scraper
}

export function ScraperCard({ scraper }: ScraperCardProps) {
  const [showApiModal, setShowApiModal] = useState(false)

  return (
    <>
      <Card className="flex flex-col h-full hover:border-amber-500/50 transition-colors">
        <CardHeader>
          <div className="flex justify-between items-start gap-2">
            <CardTitle className="text-lg truncate" title={scraper.name}>
              {scraper.name}
            </CardTitle>
            {scraper.schedule && (
              <Badge variant="secondary" className="shrink-0 flex items-center gap-1">
                <Clock className="h-3 w-3" />
                <span>Scheduled</span>
              </Badge>
            )}
          </div>
          <CardDescription className="line-clamp-2 min-h-[2.5em]">
            {scraper.description || "No description provided"}
          </CardDescription>
        </CardHeader>
        <CardContent className="flex-1">
          <div className="text-xs text-zinc-500 font-mono bg-zinc-900 p-2 rounded truncate flex items-center gap-2">
            <span className="text-amber-500 font-bold">POST</span>
            <span className="truncate">/scrape/{scraper.scraper_id}</span>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            {scraper.example_url && (
              <Badge variant="outline" className="font-normal text-zinc-400">
                {new URL(scraper.example_url).hostname}
              </Badge>
            )}
            <span className="text-xs text-zinc-500 self-center ml-auto">
              Created {formatDate(scraper.created_at)}
            </span>
          </div>
        </CardContent>
        <CardFooter className="flex flex-col gap-2">
          <div className="flex gap-2 w-full">
            <Link href={`/scrapers/${scraper.scraper_id}`} className="flex-1">
              <Button variant="secondary" className="w-full">
                Manage
              </Button>
            </Link>
            <Button 
              variant="outline" 
              className="flex-1"
              onClick={() => setShowApiModal(true)}
            >
              <Code className="h-4 w-4 mr-2" />
              API Endpoint
            </Button>
          </div>
          <Link href={`/scrapers/${scraper.scraper_id}?run=true`} className="w-full">
            <Button className="w-full">
              <Play className="h-4 w-4 mr-2" />
              Run Extraction
            </Button>
          </Link>
        </CardFooter>
      </Card>

      <ApiUsageModal 
        scraper={scraper} 
        open={showApiModal} 
        onClose={() => setShowApiModal(false)} 
      />
    </>
  )
}
