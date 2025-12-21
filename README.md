# Web2API ✦

> A data gathering platform that turns any website into a **type-safe API** — with schema validation, AI-powered extraction, and scheduled monitoring built-in.

![Web2API - AI-Powered Scraping](./web2api-backend/public/hero.png)

## ✨ Features

- 🤖 **AI-Powered Extraction** - Define your data in JSON schema, GPT-4o-mini extracts it
- 🚀 **Zero Selectors** - No CSS, XPath, or regex - AI understands the page semantically
- ⚡ **Two-Level Caching** - Extraction cache + content cache = instant repeat requests
- 📊 **Real-time Progress** - WebSocket streaming shows extraction status live
- 🔄 **Scheduled Monitoring** - Cron jobs for automatic re-scraping
- 🛠️ **Visual Workbench** - See your workflow in Motia's flow visualization

![Extraction Flow](./web2api-backend/public/flow.png)

## 🗺️ Roadmap

### Core Features

| Feature | Status | Description |
|---------|--------|-------------|
| JSON Schema Extraction | ✅ Done | Define output structure, AI extracts matching data |
| Firecrawl Integration | ✅ Done | Handles JS rendering, anti-bot protection |
| GPT-4o-mini Extraction | ✅ Done | Smart extraction without brittle selectors |
| Extraction Caching | ✅ Done | Cache by URL + schema hash |
| Content Caching | ✅ Done | Cache raw content by URL only |
| Real-time Progress | ✅ Done | WebSocket updates via Motia Streams |
| Webhook Notifications | 🔜 Planned | Notify on data changes |

### API

| Feature | Status | Description |
|---------|--------|-------------|
| Create Scraper | ✅ Done | Define name, schema, options |
| Run Scraper | ✅ Done | Execute against any URL |
| Get Status | ✅ Done | Poll job progress |
| Get Results | ✅ Done | Fetch extracted data |
| List Scrapers | ✅ Done | View all scrapers |
| Delete Monitor | ✅ Done | Remove scheduled jobs |

### Scheduled Monitoring

| Feature | Status | Description |
|---------|--------|-------------|
| Cron Scheduler | ✅ Done | Check monitors every 5 minutes |
| Auto-Monitoring | ✅ Done | URLs auto-added to monitoring |
| Fresh Scrapes | ✅ Done | Bypass cache for scheduled runs |
| Webhook Notifications | 🔜 Planned | Notify on data changes |

### Frontend

| Feature | Status | Description |
|---------|--------|-------------|
| Scraper Dashboard | ✅ Done | List and manage scrapers |
| Create Scraper Form | ✅ Done | Visual schema builder |
| Run Scraper UI | ✅ Done | Execute with options |
| Job Progress | ✅ Done | Real-time status updates |
| Results Viewer | ✅ Done | Pretty JSON display with syntax highlighting |
| API Usage Modal | ✅ Done | Show how to use scrapers programmatically |

**Want to contribute?** PRs welcome!

## 🚀 Quick Start

### Prerequisites

- Node.js 18+
- Python 3.9+
- API Keys: Firecrawl, OpenAI

### Installation

```bash
git clone https://github.com/MotiaDev/web2api.git
cd web2api

# Backend
cd web2api-backend
npm install

# Frontend
cd ../web2api-frontend
npm install
```

### Configure API Keys

Create `.env` in `web2api-backend/`:

```bash
FIRECRAWL_API_KEY=fc-xxxxxxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxxxxxx
```

Create `.env.local` in `web2api-frontend/`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:3001/api
```

### Start Development

```bash
# Terminal 1: Start Motia backend
cd web2api-backend
npm run dev

# Terminal 2: Start Next.js frontend
cd web2api-frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) and create your first scraper!

## 📊 How It Works

```
┌──────────────────────────────────────────────────────────────────┐
│                         WEB2API FLOW                             │
│                                                                  │
│  1. Define scraper with JSON schema                              │
│     {"news_titles": ["string"]}                                  │
│                                                                  │
│  2. POST /scrape/:id with target URL                             │
│     └─▶ API Step emits to queue                                  │
│                                                                  │
│  3. FetchWebpage (Event Step)                                    │
│     ├─▶ Check extraction cache → HIT → Return instantly          │
│     ├─▶ Check content cache → HIT → Skip Firecrawl               │
│     └─▶ MISS → Scrape with Firecrawl                             │
│                                                                  │
│  4. ExtractWithLLM (Event Step)                                  │
│     └─▶ GPT-4o-mini extracts structured data                     │
│                                                                  │
│  5. StoreResults (Event Step)                                    │
│     ├─▶ Validate against schema                                  │
│     ├─▶ Cache for future requests                                │
│     └─▶ Update job status                                        │
│                                                                  │
│  6. Receive clean JSON matching your schema                      │
└──────────────────────────────────────────────────────────────────┘
```

### Motia Workbench

Visualize and test your API flows in the Motia Workbench:

![Motia Workbench](./web2api-backend/public/workbench.png)

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/scrapers` | POST | Create scraper with JSON schema |
| `/api/scrapers` | GET | List all scrapers |
| `/api/scrapers/:id` | GET | Get scraper details |
| `/api/scrape/:scraperId` | POST | Execute scraper on URL |
| `/api/status/:jobId` | GET | Poll job status |
| `/api/results/:jobId` | GET | Get extraction results |
| `/api/monitors` | GET | List scheduled monitors |
| `/api/monitors/:id` | DELETE | Remove monitor |

### Example Usage

```bash
# Create a scraper
curl -X POST http://localhost:3001/api/scrapers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Hacker News Scraper",
    "schema": {"news_titles": ["string"]},
    "example_url": "https://news.ycombinator.com/"
  }'

# Run the scraper
curl -X POST http://localhost:3001/api/scrape/:scraperId \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://news.ycombinator.com/",
    "options": {"use_cache": true}
  }'
```

## 🚢 Deployment

### Backend → Railway

```bash
cd web2api-backend
railway up
railway domain  # Get your URL
```

### Frontend → Vercel

```bash
cd web2api-frontend
vercel --prod
```

Set environment variables in Vercel:
- `NEXT_PUBLIC_API_URL` - Your Railway backend URL (e.g., `https://web2api.up.railway.app/api`)

## 📁 Project Structure

```
web2api/
├── web2api-backend/
│   ├── steps/
│   │   ├── api/              # 9 API Steps (Python)
│   │   │   ├── create_scraper_step.py
│   │   │   ├── run_scraper_step.py
│   │   │   └── ...
│   │   ├── events/           # 4 Event Steps (Python)
│   │   │   ├── fetch_webpage_step.py
│   │   │   ├── extract_with_llm_step.py
│   │   │   └── ...
│   │   ├── cron/             # 1 Cron Step (Python)
│   │   │   └── run_scheduled_monitors_step.py
│   │   └── streams/          # 1 Stream (Python)
│   │       └── job_progress_stream.py
│   ├── src/services/         # DDD Service Layer
│   └── motia.config.ts
│
├── web2api-frontend/
│   ├── app/                  # Next.js App Router
│   ├── components/           # React Components
│   └── lib/api.ts            # API Client
```

## 🛠️ Tech Stack

- **Backend**: [Motia](https://motia.dev) - Event-driven API framework
- **Backend Language**: Python 3.9
- **Frontend**: Next.js 16 + React 19
- **Styling**: Tailwind CSS 4
- **Scraping**: Firecrawl
- **AI Extraction**: OpenAI GPT-4o-mini

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| `Property 'X' does not exist on type 'Handlers'` | Run `npx motia generate-types` |
| Firecrawl rate limit | Add delay between requests |
| OpenAI timeout | Increase handler timeout in infrastructure config |
| CORS errors | Ensure `NEXT_PUBLIC_API_URL` is correct |

## 🏆 Backend Reloaded Hackathon

Built for the [Backend Reloaded Hackathon](https://www.wemakedevs.org/hackathons/motiahack25) by [WeMakeDevs](https://www.wemakedevs.org/).

### How Web2API Uses Motia

| Motia Feature | Implementation |
|---------------|----------------|
| **API Steps** | 9 REST endpoints for scraper CRUD and job management |
| **Event Steps** | Async pipeline: Fetch → Extract → Store |
| **Cron Steps** | Scheduled monitoring every 5 minutes |
| **State Management** | Redis-backed caching with two cache layers |
| **Streams** | Real-time WebSocket progress updates |
| **Workbench** | Visual flow debugging and step visualization |

### Judging Criteria

| Criteria | Our Implementation |
|----------|-------------------|
| **Real-World Impact** | Solves web scraping pain - no more brittle CSS selectors |
| **Creativity & Innovation** | AI extraction + two-level caching = instant structured APIs |
| **Technical Excellence** | DDD architecture, event-driven design, FIFO queues with retry |
| **Developer Experience** | Define schema → Get JSON. No code, no selectors |

## 📚 Learn More

- [Motia Documentation](https://www.motia.dev/docs)
- [Motia GitHub](https://github.com/MotiaDev/motia)
- [Firecrawl Docs](https://firecrawl.dev)
- [OpenAI API](https://platform.openai.com/docs)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

MIT

---

<div align="center">

Built with ⚡ [Motia](https://motia.dev) for [Backend Reloaded Hackathon](https://www.wemakedevs.org/hackathons/motiahack25)

**Turn any website into an API. No code. No selectors. Just AI.**

</div>
