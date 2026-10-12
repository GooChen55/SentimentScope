import { ref } from 'vue'
import type { ConfigOptions, CrawlConfig, TaskType } from '@/types'

const BASE = '/api'

async function get<T>(url: string): Promise<T> {
  const res = await fetch(`${BASE}${url}`)
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error((body as any).detail || `HTTP ${res.status}`)
  }
  return res.json()
}

async function post<T>(url: string, data?: any): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: data ? JSON.stringify(data) : undefined,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error((body as any).detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export function useApi() {
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchPlatforms() {
    return get<any[]>('/platforms')
  }

  async function fetchConfigOptions() {
    return get<ConfigOptions>('/config/options')
  }

  async function fetchTopics(days = 7) {
    return get<any[]>('/topics?days=' + days)
  }

  async function fetchTopicKeywords(date: string) {
    return get<{ date: string; keywords: string[]; count: number }>(`/topics/${date}/keywords`)
  }

  async function fetchNews(date?: string, source?: string) {
    const params = new URLSearchParams()
    if (date) params.set('target_date', date)
    if (source) params.set('source', source)
    return get<any>(`/news?${params.toString()}`)
  }

  async function fetchNewsSources() {
    return get<any[]>('/news/sources')
  }

  async function fetchTasks(limit = 20) {
    return get<any>(`/crawl/tasks?limit=${limit}`)
  }

  async function fetchTask(taskId: string) {
    return get<any>(`/crawl/tasks/${taskId}`)
  }

  async function stopTask(taskId: string) {
    return post<any>(`/crawl/tasks/${taskId}/stop`)
  }

  async function startCrawl(type: TaskType, config: Partial<CrawlConfig>) {
    return post<{ task_id: string; status: string; type: string; created_at: string }>(
      `/crawl/${type}`, config
    )
  }

  async function initDb(req: {
    host: string; port: number; user: string; password: string
    db_name: string; charset: string
  }) {
    return post<any>('/init-db', req)
  }

  async function healthCheck() {
    return get<{ status: string; db_connected: boolean }>('/health')
  }

  return {
    loading, error,
    fetchPlatforms, fetchConfigOptions, fetchTopics, fetchTopicKeywords,
    fetchNews, fetchNewsSources, fetchTasks, fetchTask, stopTask,
    startCrawl, initDb, healthCheck,
    fetchEngine: () => get<any>('/crawl/engine'),
    fetchDocuments: () => get<any[]>('/crawl/documents'),
    retryTask: (taskId: string) => post<any>(`/crawl/tasks/${taskId}/retry`),
  }
}
