import { CreateScraperForm } from "@/components/CreateScraperForm"
import { ArrowLeft } from "lucide-react"
import Link from "next/link"

export default function NewScraperPage() {
  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div>
        <Link 
          href="/" 
          className="inline-flex items-center text-sm text-zinc-500 hover:text-zinc-300 mb-4 transition-colors"
        >
          <ArrowLeft className="mr-1 h-4 w-4" />
          Back to Dashboard
        </Link>
        <h1 className="text-3xl font-bold tracking-tight">Create New Scraper</h1>
        <p className="text-zinc-400 mt-2">
          Configure a new AI-powered scraper. Define what you want to extract using natural language or a JSON schema.
        </p>
      </div>
      
      <div className="bg-zinc-900/30 border border-zinc-800 rounded-xl p-6 md:p-8">
        <CreateScraperForm />
      </div>
    </div>
  )
}

