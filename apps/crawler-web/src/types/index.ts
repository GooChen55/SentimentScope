export interface Platform {
  value: string
  label: string
  description: string
}

export interface ConfigOptions {
  login_types: { value: string; label: string }[]
  default_max_keywords: number
  default_max_notes: number
  default_login_type: string
  supported_platforms: Platform[]
}

export interface CrawlConfig {
  target_date: string
  platforms: string[]
  sources: string[]
  max_keywords: number
  max_notes: number
  login_type: string
  keywords: string[]
  urls: string[]
  topic: string
}

export type TaskType = 'broad_topic' | 'deep_sentiment' | 'pipeline' | 'web_page'
export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed' | 'stopping' | 'stopped'

export interface TaskInfo {
  task_id: string
  type: TaskType
  status: TaskStatus
  created_at: string
  started_at?: string
  ended_at?: string
  config: Record<string, any>
  progress: TaskProgress
  result?: Record<string, any>
  error?: string
}

export interface TaskProgress {
  stage?: string
  current_platform?: string
  platforms_completed: string[]
  keywords_total: number
  keywords_processed: number
  notes_collected: number
  comments_collected: number
  elapsed_seconds: number
}

export interface TaskSummary {
  task_id: string
  type: TaskType
  status: TaskStatus
  created_at: string
  ended_at?: string
  error?: string
}

export interface WsEvent {
  type: 'stage' | 'progress' | 'log' | 'status_change' | 'result' | 'pong'
  stage?: string
  message?: string
  platform?: string
  keywords_done?: number
  keywords_total?: number
  notes?: number
  comments?: number
  level?: string
  success?: boolean
  data?: any
  error?: string
  elapsed_seconds: number
  timestamp: string
  from?: string
  to?: string
}

export interface DbInitResult {
  success: boolean
  message: string
  tables_created: string[]
  elapsed_seconds: number
  error?: string
}

export interface TopicItem {
  extract_date: string
  keywords_count: number
  summary?: string
  keywords: string[]
}
