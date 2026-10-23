import { createContext } from 'react'
import type { Language, TranslationKey } from './types'

export interface LanguageContextType {
  lang: Language
  setLang: (lang: Language) => void
  toggleLang: () => void
  t: (key: TranslationKey, params?: Record<string, string | number>) => string
  isAutoDetected: boolean
}

export const LanguageContext = createContext<LanguageContextType | undefined>(undefined)

