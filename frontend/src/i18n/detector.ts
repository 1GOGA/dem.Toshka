import type { Language } from './types'

export const STORAGE_KEY = 'demtoshka_lang'

export function detectDeviceLanguage(): Language {
  const nav = typeof window !== 'undefined' ? window.navigator : null
  const preferred = (nav?.languages && nav.languages.length > 0 ? nav.languages[0] : nav?.language) || ''
  const code = preferred.toLowerCase()

  // Slavic / Russian-speaking locale codes
  if (
    code.startsWith('ru') ||
    code.startsWith('uk') ||
    code.startsWith('be') ||
    code.startsWith('kk')
  ) {
    return 'ru'
  }
  return 'en'
}

export function getInitialLanguage(): { lang: Language; isAuto: boolean } {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved === 'ru' || saved === 'en') {
      return { lang: saved, isAuto: false }
    }
  } catch {
    // ignore storage access error
  }
  return { lang: detectDeviceLanguage(), isAuto: true }
}

