import { execFileSync } from 'node:child_process'
import vue from '@vitejs/plugin-vue'
import { defineConfig, loadEnv } from 'vite'

const backendPaths = String.raw`^/(?:[^?]+\.(?:json|xml)|[^/?]+/(?:upload\.html|subget/?|links/(?:add|delete/[^/?]+|from|to))|docs/intro|[a-zA-Z0-9_-]+(?:/(?:[0-9]+|edit(?:/[^/?]+)?))?|version\.txt)(?:\?|$)`

export default defineConfig(({ command, mode }) => {
   const config = {
      base: command === 'build' ? './' : '/',
      plugins: [vue()],
      build: { assetsInlineLimit: 512 }
   }
   if (process.env.VITE_LEXONOMY_REVISION === undefined) {
      try {
         const [revision, message] = execFileSync('git', ['log', '-1', '--format=%H%x00%B'], {
            encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore']
         }).trimEnd().split('\0')
         config.define = {
            'import.meta.env.VITE_LEXONOMY_REVISION': JSON.stringify(revision),
            'import.meta.env.VITE_LEXONOMY_COMMIT_MESSAGE': JSON.stringify(message || '')
         }
      } catch {
         // Source archives can build without Git metadata.
      }
   }
   if (command === 'build') return config

   const env = loadEnv(mode, process.cwd(), 'LEXONOMY_')
   const target = new URL(env.LEXONOMY_BACKEND_URL || 'http://127.0.0.1:8000')
   if (!['http:', 'https:'].includes(target.protocol) || target.search || target.hash || target.username || target.password) {
      throw new Error('LEXONOMY_BACKEND_URL must be an HTTP(S) URL with an optional path.')
   }
   const prefix = target.pathname.replace(/\/+$/, '')

   config.server = {
      strictPort: true,
      proxy: {
         [backendPaths]: {
            target: target.origin,
            changeOrigin: true,
            cookieDomainRewrite: '',
            cookiePathRewrite: '/',
            rewrite: path => prefix + path,
            configure(proxy) {
               proxy.on('proxyRes', (response, request) => {
                  const location = response.headers.location
                  const upstream = target.origin + request.url
                  if (!location || !URL.canParse(location, upstream)) return
                  const redirect = new URL(location, upstream)
                  if (redirect.origin !== target.origin) return
                  const path = redirect.pathname === prefix ? '/'
                     : prefix && redirect.pathname.startsWith(prefix + '/')
                        ? redirect.pathname.slice(prefix.length)
                        : redirect.pathname
                  response.headers.location = path + redirect.search + redirect.hash
               })
            }
         }
      }
   }
   return config
})
