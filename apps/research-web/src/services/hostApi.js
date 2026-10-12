import { request } from './http.js'

export function startHost() {
  return request('GET', '/host/start')
}

export function stopHost() {
  return request('GET', '/host/stop')
}
