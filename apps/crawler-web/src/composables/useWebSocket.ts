import { ref } from 'vue'
import type { WsEvent } from '@/types'

export function useWebSocket(taskId: string, onEvent: (e: WsEvent) => void) {
  const connected = ref(false)
  const reconnecting = ref(false)
  const reconnectAttempt = ref(0)
  let ws: WebSocket | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let destroyed = false

  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${location.host}/ws/crawl/${taskId}`

  function connect() {
    if (destroyed) return
    ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      connected.value = true
      reconnecting.value = false
      reconnectAttempt.value = 0
    }

    ws.onmessage = (msg) => {
      try {
        const event: WsEvent = JSON.parse(msg.data)
        onEvent(event)
      } catch { /* ignore malformed */ }
    }

    ws.onclose = () => {
      connected.value = false
      if (!destroyed) {
        scheduleReconnect()
      }
    }

    ws.onerror = () => {
      ws?.close()
    }
  }

  function scheduleReconnect() {
    const base = 1000
    const cap = 15000
    const delay = Math.min(base * Math.pow(2, reconnectAttempt.value), cap)
    reconnectAttempt.value++
    reconnecting.value = true
    reconnectTimer = setTimeout(connect, delay)
  }

  function sendStop() {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: 'stop' }))
    }
  }

  function sendPing() {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: 'ping' }))
    }
  }

  function disconnect() {
    destroyed = true
    if (reconnectTimer) clearTimeout(reconnectTimer)
    if (ws) {
      ws.onclose = null
      ws.close()
      ws = null
    }
    connected.value = false
    reconnecting.value = false
  }

  connect()

  return { connected, reconnecting, reconnectAttempt, sendStop, sendPing, disconnect }
}
