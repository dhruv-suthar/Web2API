export interface Scraper {
  scraper_id: string;
  name: string;
  description?: string;
  schema: string | object;
  example_url?: string;
  webhook_url?: string;
  schedule?: string | number;
  options?: {
    timeout?: number;
    use_simple_scraper?: boolean;
    wait_for?: number;
  };
  created_at?: string;
}

export interface Monitor {
  monitor_id: string;
  scraper_id: string;
  url: string;
  active: boolean;
  last_run?: string;
  next_run?: string;
  run_count?: number;
  created_at?: string;
}

export interface JobResult {
  job_id: string;
  scraper_id?: string;
  status: "queued" | "fetching" | "fetched" | "extracting" | "extracted" | "validating" | "completed" | "failed";
  percent: number;
  data?: any;
  url?: string;
  cached?: boolean;
  monitoring?: boolean;
  created_at?: string;
  updated_at?: string;
  message?: string;
  error?: string;
  stage?: string;
  metadata?: Record<string, any>;
}

export interface CreateScraperInput {
  name: string;
  description?: string;
  schema: string | object;
  example_url?: string;
  webhook_url?: string;
  schedule?: string | number;
  monitor_urls?: string[];
  options?: {
    timeout?: number;
    use_simple_scraper?: boolean;
    wait_for?: number;
  };
}

export interface RunOptions {
  use_cache?: boolean;
  wait_for?: number;
  async?: boolean;
  skip_monitoring?: boolean;
  timeout?: number;
  use_simple_scraper?: boolean;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000/api';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, options);
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.error || `Request failed with status ${res.status}`);
  }
  return res.json();
}

export const api = {
  // Scrapers
  listScrapers: () => fetchJson<{ scrapers: Scraper[]; count: number }>(`${API_BASE}/scrapers`),
  
  getScraper: (id: string) => fetchJson<Scraper>(`${API_BASE}/scrapers/${id}`),
  
  createScraper: (data: CreateScraperInput) => 
    fetchJson<Scraper>(`${API_BASE}/scrapers`, { 
      method: 'POST', 
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data) 
    }),
  
  // Extraction
  runScraper: (scraperId: string, url: string, options?: RunOptions) =>
    fetchJson<JobResult>(`${API_BASE}/scrape/${scraperId}`, { 
      method: 'POST', 
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, options }) 
    }),
    
  getStatus: (jobId: string) => fetchJson<JobResult>(`${API_BASE}/status/${jobId}`),
  
  getResults: (jobId: string) => fetchJson<JobResult>(`${API_BASE}/results/${jobId}`),
  
  // Monitors
  listMonitors: (scraperId?: string) => 
    fetchJson<{ monitors: Monitor[]; total: number; active_count: number }>(
      `${API_BASE}/monitors${scraperId ? `?scraper_id=${scraperId}` : ''}`
    ),
};

