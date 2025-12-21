'use client'

import React, { useState } from 'react'
import { Dialog } from './ui/Dialog'
import { Scraper } from '@/lib/api'
import { Copy, Check, Code, Terminal, FileJson, Info } from 'lucide-react'
import { Button } from './ui/Button'
import Editor from "react-simple-code-editor"
import Prism from "prismjs"
import "prismjs/components/prism-clike"
import "prismjs/components/prism-javascript"
import "prismjs/components/prism-json"
import "prismjs/components/prism-bash"

interface ApiUsageModalProps {
  scraper: Scraper
  open: boolean
  onClose: () => void
}

export function ApiUsageModal({ scraper, open, onClose }: ApiUsageModalProps) {
  const [copiedEndpoint, setCopiedEndpoint] = useState(false)
  const [copiedCurl, setCopiedCurl] = useState(false)
  const [copiedBody, setCopiedBody] = useState(false)

  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000/api'
  // Remove trailing slash if present
  const normalizedBaseUrl = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl
  const endpoint = `${normalizedBaseUrl}/scrape/${scraper.scraper_id}`
  
  const requestBody = JSON.stringify({
    url: scraper.example_url || "https://example.com/product/123"
  }, null, 2)

  const curlExample = `curl -X POST \\
  '${endpoint}' \\
  -H 'Content-Type: application/json' \\
  -d '${requestBody.replace(/\n/g, '\n  ')}'`

  const copyToClipboard = async (text: string, setter: (v: boolean) => void) => {
    await navigator.clipboard.writeText(text)
    setter(true)
    setTimeout(() => setter(false), 2000)
  }

  const schemaString = typeof scraper.schema === 'string' 
    ? (scraper.schema.trim().startsWith('{') ? scraper.schema : JSON.stringify({ extraction_prompt: scraper.schema }, null, 2))
    : JSON.stringify(scraper.schema, null, 2)

  const highlightCode = (code: string, lang: string) => {
    try {
      const grammar = Prism.languages[lang] || Prism.languages.javascript || Prism.languages.markup;
      return Prism.highlight(code, grammar, lang);
    } catch (e) {
      return code;
    }
  }

  return (
    <Dialog 
      open={open} 
      onClose={onClose} 
      title={scraper.name}
      description="API Integration Guide"
    >
      <div className="space-y-8 pb-4">
        {/* Endpoint Section */}
        <section className="space-y-3">
          <h4 className="text-sm font-semibold text-zinc-400 flex items-center gap-2 uppercase tracking-wider">
            <Code className="h-4 w-4" />
            Endpoint URL
          </h4>
          <div className="flex gap-2">
            <div className="flex-1 font-mono text-sm p-3 bg-zinc-900 border border-zinc-800 rounded-lg text-zinc-300 overflow-x-auto whitespace-nowrap">
              <span className="text-amber-500 mr-2 font-bold">POST</span>
              {endpoint}
            </div>
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => copyToClipboard(endpoint, setCopiedEndpoint)}
              className="shrink-0 h-[46px]"
            >
              {copiedEndpoint ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
            </Button>
          </div>
        </section>

        {/* Request Body Section */}
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-semibold text-zinc-400 flex items-center gap-2 uppercase tracking-wider">
              <FileJson className="h-4 w-4" />
              Request Body
            </h4>
            <button 
              onClick={() => copyToClipboard(requestBody, setCopiedBody)}
              className="text-xs text-zinc-500 hover:text-zinc-300 flex items-center gap-1 transition-colors"
            >
              {copiedBody ? (
                <><Check className="h-3 w-3 text-green-500" /> Copied</>
              ) : (
                <><Copy className="h-3 w-3" /> Copy JSON</>
              )}
            </button>
          </div>
          <div className="bg-[#1e1e1e] border border-zinc-800 rounded-lg overflow-hidden">
            <Editor
              value={requestBody}
              onValueChange={() => {}}
              highlight={(code) => highlightCode(code, 'json')}
              padding={16}
              readOnly
              style={{
                fontFamily: '"JetBrains Mono", "Fira Code", monospace',
                fontSize: 13,
                backgroundColor: "#1e1e1e",
              }}
            />
          </div>
          <div className="grid grid-cols-1 gap-2 mt-2">
            <div className="text-xs flex gap-2">
              <span className="font-mono text-amber-500 font-bold shrink-0">url</span>
              <span className="text-zinc-500">(string, required) The target URL to scrape</span>
            </div>
          </div>
        </section>

        {/* cURL Example Section */}
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-semibold text-zinc-400 flex items-center gap-2 uppercase tracking-wider">
              <Terminal className="h-4 w-4" />
              cURL Example
            </h4>
            <button 
              onClick={() => copyToClipboard(curlExample, setCopiedCurl)}
              className="text-xs text-zinc-500 hover:text-zinc-300 flex items-center gap-1 transition-colors"
            >
              {copiedCurl ? (
                <><Check className="h-3 w-3 text-green-500" /> Copied</>
              ) : (
                <><Copy className="h-3 w-3" /> Copy Example</>
              )}
            </button>
          </div>
          <div className="bg-[#1e1e1e] border border-zinc-800 rounded-lg overflow-hidden">
            <Editor
              value={curlExample}
              onValueChange={() => {}}
              highlight={(code) => highlightCode(code, 'bash')}
              padding={16}
              readOnly
              style={{
                fontFamily: '"JetBrains Mono", "Fira Code", monospace',
                fontSize: 13,
                backgroundColor: "#1e1e1e",
              }}
            />
          </div>
        </section>

        {/* Response Schema Section */}
        <section className="space-y-3">
          <h4 className="text-sm font-semibold text-zinc-400 flex items-center gap-2 uppercase tracking-wider">
            <FileJson className="h-4 w-4" />
            Response Schema
          </h4>
          <div className="bg-[#1e1e1e] border border-zinc-800 rounded-lg overflow-hidden max-h-[300px] overflow-y-auto">
            <Editor
              value={schemaString}
              onValueChange={() => {}}
              highlight={(code) => highlightCode(code, 'json')}
              padding={16}
              readOnly
              style={{
                fontFamily: '"JetBrains Mono", "Fira Code", monospace',
                fontSize: 13,
                backgroundColor: "#1e1e1e",
              }}
            />
          </div>
        </section>

        <div className="bg-blue-900/10 border border-blue-900/30 rounded-lg p-4 text-blue-200/70 text-sm flex gap-3">
          <Info className="h-5 w-5 shrink-0 text-blue-400" />
          <div>
            <p className="font-semibold text-blue-300 mb-1">Synchronous by Default</p>
            This endpoint returns the extracted data directly in the response. For long-running scrapes, add <code className="text-amber-500">"async": true</code> to options to get a <code className="text-amber-500">job_id</code> and poll the status endpoint.
          </div>
        </div>
      </div>
    </Dialog>
  )
}
