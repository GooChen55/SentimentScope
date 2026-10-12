/* SSE event stream composable for real-time role updates. */

import { ref, onUnmounted } from 'vue'
import { getLatestResults } from './api.js'

export function useSSE() {
  const connected = ref(false)
  const roleProgress = ref({})
  const roleResults = ref({})
  let eventSource = null
  let reconnectTimer = null

  /* 通知-拉取:role_result 仅为完成信号,数据从 REST 拉取 */
  async function fetchRoleResult(role) {
    try {
      const data = await getLatestResults()
      const result = data?.results?.[role]
      if (result) {
        roleResults.value = {
          ...roleResults.value,
          [role]: result
        }
      }
    } catch {}
  }

  function connect() {
    if (eventSource) eventSource.close()

    eventSource = new EventSource('/api/events/stream')

    eventSource.addEventListener('connected', () => {
      connected.value = true
    })

    eventSource.onmessage = (event) => {
      try {
        const { event: evtType, data } = JSON.parse(event.data)
        if (data?.research_id !== localStorage.getItem('research_id')) return
        if (evtType === 'role_progress' && data?.role) {
          const previous = roleProgress.value[data.role]
          const progress = data.status === 'starting'
            ? data.progress_pct
            : Math.max(previous?.progress_pct || 0, data.progress_pct || 0)
          roleProgress.value = {
            ...roleProgress.value,
            [data.role]: {
              ...data,
              progress_pct: progress
            }
          }
        } else if (evtType === 'role_result' && data?.role) {
          fetchRoleResult(data.role)
        } else if (evtType === 'role_error' && data?.role) {
          roleProgress.value = { ...roleProgress.value, [data.role]: { ...data, message: data.error, status: 'error' } }
        }
      } catch {}
    }

    eventSource.onerror = () => {
      connected.value = false
      eventSource?.close()
      reconnectTimer = setTimeout(connect, 3000)
    }
  }

  function disconnect() {
    clearTimeout(reconnectTimer)
    eventSource?.close()
    connected.value = false
  }

  function clearResearchState() {
    roleProgress.value = {}
    roleResults.value = {}
  }

  onUnmounted(disconnect)

  return { connected, roleProgress, roleResults, connect, disconnect, clearResearchState }
}
