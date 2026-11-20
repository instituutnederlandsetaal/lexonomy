import { createRouter, createWebHashHistory, type LocationQuery, type RouteRecordRaw } from 'vue-router'
import { login, session } from './auth.ts'
import { dictionaryWorkspace, type EntrySearch } from './dictionary-workspace.ts'
import { pageUrl } from './page-url.ts'
import { confirmEntryNavigation, unsavedEntry } from '../components/entry-editor/unsaved.js'

declare module 'vue-router' {
   interface RouteMeta {
      requiresSession?: boolean
      theme?: 'account' | 'public'
      wide?: boolean
   }
}

const accountPage = () => import('../components/main-page.vue')
const accounts: [path: string, page: string, requiresSession?: boolean][] = [
   ['/', 'login'],
   ['/register', 'register'],
   ['/forgot', 'forgot'],
   ['/createaccount/:token?', 'registerPassword'],
   ['/recoverpwd/:token?', 'forgotPassword'],
   ['/make', 'new', true],
   ['/userprofile', 'userprofile', true]
]
const accountRoutes: RouteRecordRaw[] = accounts.map(([path, mainSubPage, requiresSession]) => ({
   path, name: path === '/' ? 'home' : mainSubPage,
   alias: path === '/' ? '/login' : [],
   component: accountPage,
   props: route => ({ mainSubPage, token: typeof route.params.token === 'string' ? route.params.token : '' }),
   meta: { requiresSession, theme: requiresSession ? undefined : 'account' }
}))

const configPages = {
   autonumber: () => import('../components/dict-config-autonumber.vue'),
   download: () => import('../components/dict-config-download.vue'),
   editing: () => import('../components/dict-config-editing.vue'),
   flagging: () => import('../components/dict-config-flagging.vue'),
   ident: () => import('../components/dict-config-ident.vue'),
   links: () => import('../components/dict-config-links.vue'),
   publico: () => import('../components/dict-config-publico.vue'),
   searchability: () => import('../components/dict-config-searchability.vue'),
   subbing: () => import('../components/dict-config-subbing.vue'),
   titling: () => import('../components/dict-config-titling.vue'),
   url: () => import('../components/dict-config-url.vue'),
   users: () => import('../components/dict-config-users.vue'),
   xema: () => import('../components/dict-config-xema.vue'),
   xemplate: () => import('../components/dict-config-xemplate.vue'),
}

export function readEntrySearch(query: LocationQuery): EntrySearch {
   const text = (key: string) => {
      const value = query[key]
      return (Array.isArray(value) ? value[0] : value) || ''
   }
   return { searchtext: text('s'), searchflag: text('f'), modifier: text('m') || 'start' }
}

export const router = createRouter({
   history: createWebHashHistory(pageUrl.pathname),
   sensitive: true,
   routes: [
      ...accountRoutes,
      { path: '/opendictionaries', name: 'public-list', meta: { theme: 'public' }, component: () => import('../components/open-dict-list.vue') },
      { path: '/docs/intro', name: 'docs-intro', component: () => import('../components/docs-intro.vue') },
      { path: '/docs/about', name: 'docs-about', component: () => import('../components/docs-about.vue') },
      { path: '/:dictId', name: 'dictionary', component: () => import('../components/dict-public.vue'), meta: { wide: true, theme: 'public' } },
      { path: '/:dictId/:entryId(\\d+)', name: 'entry', component: () => import('../components/dict-public-entry.vue'), meta: { wide: true, theme: 'public' } },
      { path: '/:dictId/edit/:doctype?/:entryId(\\d+)?/:mode(edit|view)?', name: 'edit',
         component: () => import('../components/dict-edit.vue'), meta: { requiresSession: true, wide: true } },
      { path: '/:dictId/links', name: 'links', component: () => import('../components/dict-links.vue'), meta: { requiresSession: true } },
      { path: '/:dictId/download', name: 'download', component: () => import('../components/dict-download.vue'), meta: { requiresSession: true } },
      { path: '/:dictId/upload', name: 'upload', component: () => import('../components/dict-upload.vue'), meta: { requiresSession: true } },
      { path: '/:dictId/config', name: 'config', component: () => import('../components/dict-config.vue'), props: true,
         alias: ['ske', 'kontext', 'gapi'].map(page => '/:dictId/config/' + page), meta: { requiresSession: true } },
      ...Object.entries(configPages).map(([page, component]) => ({
         path: '/:dictId/config/' + page, name: 'config-' + page, component, props: true,
         alias: page === 'xemplate' ? '/:dictId/config/xemplate-override' : [],
         meta: { requiresSession: true }
      })),
      { path: '/e404', name: 'not-found', component: () => import('../components/e404.vue') },
      { path: '/:pathMatch(.*)*', redirect: { name: 'not-found' } },
   ]
})

let restoringSession: Promise<boolean> | undefined
router.beforeEach(async (to, from) => {
   await (restoringSession ??= login().catch(() => false))
   if (to.meta.requiresSession && !session.value) {
      return { name: 'home', query: { redirect: to.fullPath } }
   }
   if (to.path !== from.path && !confirmEntryNavigation()) return false
})

router.afterEach((to, from, failure) => {
   if (failure) return
   if (to.path !== from.path) unsavedEntry.value = false

   const { dictId, doctype, entryId, mode } = to.params
   void dictionaryWorkspace.open({
      dictId: typeof dictId === 'string' ? dictId : null,
      doctype: typeof doctype === 'string' ? doctype : null,
      entryId: Number(entryId) || null,
      mode: mode === 'edit' ? 'edit' : 'view',
      filters: readEntrySearch(to.query),
      entryLimit: to.name === 'dictionary' ? 20 : undefined
   }).then(result => {
      if (result === false && router.currentRoute.value === to) void router.replace({ name: 'home' })
   })
})
