import { shallowRef } from 'vue'
import { api } from './api.ts'

type Session = { email: string; consent: boolean }
type Credentials = { email: string; password: string }
type LoginResponse = { success: false } | ({ success: true } & Session)
export type AuthResult = { success: boolean }

export const session = shallowRef<Session | null>(null)

export async function login(credentials?: Credentials) {
   const response = await api.post<LoginResponse>('login.json', credentials)
   if (response.success) session.value = { email: response.email, consent: response.consent }
   return response.success
}

export async function logout() {
   // The logout endpoint returns success: false after clearing the session.
   await api.post('logout.json')
   session.value = null
}

export async function acceptConsent() {
   const user = session.value
   if (!user) return false
   const { success } = await api.post<AuthResult>('consent.json', { consent: 1 })
   if (success && session.value === user) session.value = { ...user, consent: true }
   return success
}
