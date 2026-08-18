// Where the api box lives. Overridable at build time with VITE_API_BASE.

const fallback = 'http://localhost:8100'

export const API_BASE: string = (import.meta.env.VITE_API_BASE as string | undefined)?.replace(/\/$/, '') || fallback

export function wsUrl(path = '/ws'): string {
  const base = new URL(API_BASE, window.location.href)
  base.protocol = base.protocol === 'https:' ? 'wss:' : 'ws:'
  base.pathname = path
  base.search = ''
  return base.toString()
}
