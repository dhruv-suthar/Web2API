'use client'

import { useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useRouter } from "next/navigation"
import { api, CreateScraperInput } from "@/lib/api"
import { Button } from "@/components/ui/Button"
import { Input, Textarea } from "@/components/ui/Input"
import { Card, CardContent } from "@/components/ui/Card"
import { Loader2, Wand2, Code } from "lucide-react"
import Editor from "react-simple-code-editor"
import Prism from "prismjs"
import "prismjs/components/prism-clike"
import "prismjs/components/prism-javascript"
import "prismjs/components/prism-json"
import "prismjs/themes/prism-dark.css"

export function CreateScraperForm() {
  const router = useRouter()
  const queryClient = useQueryClient()
  const [schemaMode, setSchemaMode] = useState<"nl" | "json">("nl")
  const [formData, setFormData] = useState<CreateScraperInput>({
    name: "",
    description: "",
    example_url: "",
    webhook_url: "",
    schema: "", // Will be string for NL or JSON string for code editor
    schedule: "",
  })
  
  // JSON Schema default template
  const defaultJsonSchema = JSON.stringify({
    type: "object",
    properties: {
      title: { type: "string" },
      price: { type: "number" },
      description: { type: "string" }
    },
    required: ["title", "price"]
  }, null, 2)

  const mutation = useMutation({
    mutationFn: api.createScraper,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['scrapers'] })
      router.push(`/scrapers/${data.scraper_id}`)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    // Prepare payload
    const payload = { ...formData }
    
    // If JSON mode, parse the schema string to object
    if (schemaMode === "json" && typeof payload.schema === "string") {
      try {
        payload.schema = JSON.parse(payload.schema)
      } catch (err) {
        alert("Invalid JSON Schema")
        return
      }
    }
    
    // Convert schedule to number if it's a number string
    if (payload.schedule && !isNaN(Number(payload.schedule))) {
      payload.schedule = Number(payload.schedule)
    } else if (!payload.schedule) {
      delete payload.schedule
    }

    mutation.mutate(payload)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-8 max-w-3xl mx-auto">
      <div className="space-y-4">
        <div>
          <label className="text-sm font-medium mb-1 block">Name</label>
          <Input 
            required
            placeholder="e.g. Amazon Product Scraper"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          />
        </div>
        
        <div>
          <label className="text-sm font-medium mb-1 block">Description</label>
          <Textarea 
            placeholder="What does this scraper do?"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          />
        </div>

        <div>
          <label className="text-sm font-medium mb-1 block">Example URL</label>
          <Input 
            placeholder="https://example.com/product/123"
            value={formData.example_url}
            onChange={(e) => setFormData({ ...formData, example_url: e.target.value })}
          />
          <p className="text-xs text-zinc-500 mt-1">Used for documentation and testing</p>
        </div>
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium">Extraction Schema</label>
          <div className="flex bg-zinc-900 rounded-lg p-1">
            <button
              type="button"
              onClick={() => {
                setSchemaMode("nl")
                // Reset schema content if switching from default JSON
                if (formData.schema === defaultJsonSchema) setFormData({ ...formData, schema: "" })
              }}
              className={`px-3 py-1 text-xs font-medium rounded-md transition-colors flex items-center gap-1 ${
                schemaMode === "nl" ? "bg-zinc-800 text-white shadow-sm" : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              <Wand2 className="h-3 w-3" />
              Natural Language
            </button>
            <button
              type="button"
              onClick={() => {
                setSchemaMode("json")
                // Set default JSON if empty
                if (!formData.schema) setFormData({ ...formData, schema: defaultJsonSchema })
              }}
              className={`px-3 py-1 text-xs font-medium rounded-md transition-colors flex items-center gap-1 ${
                schemaMode === "json" ? "bg-zinc-800 text-white shadow-sm" : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              <Code className="h-3 w-3" />
              JSON Schema
            </button>
          </div>
        </div>

        {schemaMode === "nl" ? (
          <div className="relative">
            <Textarea 
              required={schemaMode === "nl"}
              className="min-h-[200px] font-mono text-sm"
              placeholder="Extract the product name, price, reviews, and specifications..."
              value={typeof formData.schema === 'string' ? formData.schema : JSON.stringify(formData.schema, null, 2)}
              onChange={(e) => setFormData({ ...formData, schema: e.target.value })}
            />
            <div className="absolute bottom-3 right-3">
              <Wand2 className="h-4 w-4 text-amber-500 opacity-50" />
            </div>
          </div>
        ) : (
          <div className="border border-zinc-800 rounded-md overflow-hidden bg-[#1e1e1e]">
            <Editor
              value={typeof formData.schema === 'string' ? formData.schema : JSON.stringify(formData.schema, null, 2)}
              onValueChange={(code) => setFormData({ ...formData, schema: code })}
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
              style={{
                fontFamily: '"Fira Code", "Fira Mono", monospace',
                fontSize: 14,
                backgroundColor: "#1e1e1e",
                minHeight: "200px"
              }}
              className="min-h-[200px]"
            />
          </div>
        )}
        <p className="text-xs text-zinc-500">
          {schemaMode === "nl" 
            ? "Describe what you want to extract in plain English. AI will handle the rest." 
            : "Define a strict JSON Schema for the extraction output."}
        </p>
      </div>

      <div className="space-y-4 pt-4 border-t border-zinc-800">
        <h3 className="text-sm font-medium text-zinc-400 uppercase tracking-wider">Advanced Options</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-sm font-medium mb-1 block">Schedule (Optional)</label>
            <Input 
              placeholder="*/30 * * * * or 60 (minutes)"
              value={formData.schedule?.toString() || ""}
              onChange={(e) => setFormData({ ...formData, schedule: e.target.value })}
            />
            <p className="text-xs text-zinc-500 mt-1">Cron expression or interval in minutes</p>
          </div>
          
          <div>
            <label className="text-sm font-medium mb-1 block">Webhook URL (Optional)</label>
            <Input 
              placeholder="https://api.myapp.com/webhook"
              value={formData.webhook_url}
              onChange={(e) => setFormData({ ...formData, webhook_url: e.target.value })}
            />
          </div>
        </div>
      </div>

      <div className="flex justify-end pt-4">
        <Button 
          type="submit" 
          size="lg" 
          disabled={mutation.isPending}
          className="w-full md:w-auto"
        >
          {mutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          Create Scraper
        </Button>
      </div>
      
      {mutation.isError && (
        <div className="p-4 bg-red-900/20 border border-red-900/50 rounded-md text-red-400 text-sm">
          Error: {(mutation.error as Error).message}
        </div>
      )}
    </form>
  )
}

