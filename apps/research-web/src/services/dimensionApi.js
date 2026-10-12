import { request } from './http.js'

export function getResearchDimensions() {
  return request('GET', '/host/dimensions')
}
