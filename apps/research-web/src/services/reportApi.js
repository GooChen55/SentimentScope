import { request } from './http.js'

export function getReportStatus(researchId) {
  return request('GET', '/report/status' + (researchId ? `?research_id=${researchId}` : ''))
}

export function generateReport(query, research_id) {
  return request('POST', '/report/generate', { query, research_id })
}

export const getReportTask = id => request('GET', `/report/task/${id}`)

export function getReportResult(taskId) {
  return request('GET', `/report/result/${taskId}`)
}

export function getReportDownloadUrl(taskId, fileType = 'html') {
  return `/api/report/download/${taskId}/${fileType}`
}

export function getMarkdownUrl(taskId) {
  return getReportDownloadUrl(taskId, 'md')
}
