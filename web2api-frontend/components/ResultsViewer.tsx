'use client'

import { useState } from "react"
import Editor from "react-simple-code-editor"
import Prism from "prismjs"
import "prismjs/components/prism-clike"
import "prismjs/components/prism-javascript"
import "prismjs/components/prism-json"
import { Button } from "./ui/Button"
import { Copy, Check } from "lucide-react"

interface ResultsViewerProps {
  data: any
}

export function ResultsViewer({ data }: ResultsViewerProps) {
  const [copied, setCopied] = useState(false)
  const jsonString = JSON.stringify(data, null, 2)

  const handleCopy = () => {
    navigator.clipboard.writeText(jsonString)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="relative border border-zinc-800 rounded-lg overflow-hidden bg-[#1e1e1e]">
      <div className="absolute top-2 right-2 z-10">
        <Button 
          size="sm" 
          variant="secondary" 
          className="h-8 px-2 bg-zinc-800/80 hover:bg-zinc-700 backdrop-blur-sm"
          onClick={handleCopy}
        >
          {copied ? (
            <>
              <Check className="h-3 w-3 mr-1" />
              Copied
            </>
          ) : (
            <>
              <Copy className="h-3 w-3 mr-1" />
              Copy JSON
            </>
          )}
        </Button>
      </div>
      <Editor
        value={jsonString}
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
          fontFamily: '"Fira Code", "Fira Mono", monospace',
          fontSize: 14,
          backgroundColor: "#1e1e1e",
          minHeight: "300px"
        }}
      />
    </div>
  )
}

