import { request } from './http.js'

export function getConfig() {
  return request('GET', '/config')
}

export function updateConfig(values) {
  return request('POST', '/config', values)
}