# Web2API Demo Script (2:50)

> **Hackathon Demo for Motia Challenge**

---

## Pre-Demo Checklist

```bash
# Terminal 1: Backend
cd web2api-backend && npm run dev  # Running on :3001

# Terminal 2: Frontend  
cd web2api-frontend && npm run dev  # Running on :3000
```

**Browser tabs ready:**
1. Frontend: `http://localhost:3000`
2. Hacker News: `https://news.ycombinator.com/`
3. Workbench: `http://localhost:3001` (optional)

---

## THE SCRIPT

### [0:00 - 0:15] HOOK (15 sec)

> "Developers waste hours writing scrapers. CSS selectors break. Sites change. Maintenance is endless."
>
> "What if you could turn ANY website into a structured API in 30 seconds? Just describe what you want."
>
> "That's **Web2API** - built on Motia."

*[Show frontend homepage with scraper list]*

---

### [0:15 - 0:45] CREATE SCRAPER (30 sec)

> "I want news titles from Hacker News. Watch."

**Actions:**
1. Click **"New Scraper"**
2. Fill form:
   - Name: `Hacker News Scraper`
   - URL: `https://news.ycombinator.com/`
   - Schema:
   ```json
   {
     "news_titles": ["string"]
   }
   ```
3. Click **Create**

> "No CSS selectors. No XPath. No regex. Just JSON schema - describe what you want, AI figures out the rest."

---

### [0:45 - 1:30] FIRST SCRAPE (45 sec)

> "Now let's run it."

**Actions:**
1. Click **"Run Scraper"**
2. Point to progress indicator

> "Behind the scenes:"
> - Motia **API Step** receives the request
> - Emits event to **FIFO queue** for reliability  
> - **Event Step** fetches page via Firecrawl
> - Another **Event Step** extracts with GPT-4o-mini
> - Final **Event Step** validates and stores
> - Real-time progress via **Motia Streams**

*[Results appear]*

> "30 news titles. Perfectly structured JSON. Zero code."

*[Scroll through results briefly]*

---

### [1:30 - 1:55] CACHE DEMO (25 sec)

> "Here's the killer feature. Run it again - same URL."

**Actions:**
1. Click **"Run"** again (same URL)
2. *[Results appear INSTANTLY]*

> "Instant. Zero API calls."
>
> "We cache extraction results in **Motia State**. Same URL + same schema = cached response."
>
> "In production, this saves thousands in API costs."

---

### [1:55 - 2:25] ARCHITECTURE (30 sec)

> "Let me show you why Motia was perfect for this."

*[Optional: Quick flash of Workbench OR just describe]*

> "Traditional approach: One big endpoint doing everything. Fails halfway? Start over. Timeout? Lost work."
>
> "With Motia:"
> - **API Steps** handle HTTP - thin controllers
> - **Event Steps** do the heavy lifting - retriable, durable
> - **State** passes large payloads between steps
> - **Streams** push real-time updates to the frontend
> - **Cron Steps** handle scheduled monitoring

*[Point to flow if Workbench is visible]*

> "Every step is independently deployable. Queue fails? Automatic retry. LLM timeout? Retry. The workflow is **durable**."

---

### [2:25 - 2:50] CLOSE (25 sec)

> "What we built:"
> - **14 Motia Steps** - 9 API, 4 Event, 1 Cron
> - **100% Python** - Motia's multi-language support
> - **Two-level caching** - extraction cache + content cache  
> - **Real-time progress** - WebSocket streams
> - **Production-ready** - deployed on Railway

> "Use cases:"
> - Price monitoring across e-commerce
> - News aggregation from any source
> - Lead generation from directories
> - Research data collection

> "Traditional scrapers break when sites change. Ours **adapts** because AI understands the page semantically."

> "**Web2API** - turn any website into a structured API. Built on **Motia**."

---

## Backup Phrases

**If something breaks:**
> "Live demos - the architecture handles this gracefully with retry logic. Let me show the cached result..."

**If asked about scaling:**
> "Each step is a separate Lambda-style function. FIFO queues handle backpressure. Motia State is Redis-backed."

**If asked about accuracy:**
> "GPT-4o-mini with JSON schema validation. Schema acts as a contract - if extraction doesn't match, it fails fast."

---

## Quick Recovery URLs

If Hacker News fails:
- `https://www.producthunt.com/`
- `https://github.com/trending`

---

## Key Stats to Mention

| Metric | Value |
|--------|-------|
| Steps | 14 (9 API, 4 Event, 1 Cron) |
| Language | 100% Python |
| Cache Layers | 2 (extraction + content) |
| External APIs | Firecrawl + OpenAI |
| State Groups | 9 |
| First scrape | ~10-15 seconds |
| Cached scrape | <100ms |

---

## Judging Criteria Soundbites

| Criteria | One-liner |
|----------|-----------|
| **Real-World Impact** | "Scrapers break constantly. This adapts with AI." |
| **Creativity** | "Steps as primitives - API for entry, Events for work, State as glue." |
| **Technical Excellence** | "FIFO queues, retry logic, 4KB payload optimization, structured logging." |
| **Developer Experience** | "Describe what you want in JSON. That's it." |
| **Learning Journey** | "First time using Motia - the unified runtime model clicked immediately." |

