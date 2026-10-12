import { request } from './http.js'

export function getHostDiscussionLog() {
  const id = localStorage.getItem('research_id')
  return request('GET', '/host/discussion' + (id ? `?research_id=${id}` : ''))
}
