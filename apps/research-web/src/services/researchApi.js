import { request } from './http.js'

export function startResearch(query, mode = 'live') {
  return request('POST', '/research', { query, mode })
}

export function getLatestResults(id = localStorage.getItem('research_id')) {
  return request('GET', '/research/latest' + (id ? `?research_id=${encodeURIComponent(id)}` : ''))
}

export const listResearchTasks = () => request('GET', '/research/tasks')
export const getResearchTask = id => request('GET', `/research/tasks/${id}`)
export const cancelResearch = id => request('POST', `/research/tasks/${id}/cancel`)
export const retryResearch = id => request('POST', `/research/tasks/${id}/retry`)
export const getEvidence = id => request('GET', `/research/tasks/${id}/evidence`)
export const getEvaluation = id => request('GET', `/research/tasks/${id}/evaluation`)
