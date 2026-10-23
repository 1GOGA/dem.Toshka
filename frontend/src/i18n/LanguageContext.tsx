import React, { useEffect, useState, useMemo, useCallback } from 'react'
import type { Language, TranslationKey } from './types'
import { ru } from './locales/ru'
import { en } from './locales/en'
import { STORAGE_KEY, getInitialLanguage } from './detector'
import { LanguageContext } from './context'

const dictionaries = { ru, en }

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [langState, setLangState] = useState(() => getInitialLanguage())

  const setLang = useCallback((newLang: Language) => {
    setLangState({ lang: newLang, isAuto: false })
    try {
      localStorage.setItem(STORAGE_KEY, newLang)
    } catch {
      // ignore storage error
    }
    if (typeof document !== 'undefined') {
      document.documentElement.lang = newLang
    }
  }, [])

  const toggleLang = useCallback(() => {
    setLang(langState.lang === 'ru' ? 'en' : 'ru')
  }, [langState.lang, setLang])

  useEffect(() => {
    if (typeof document !== 'undefined') {
      document.documentElement.lang = langState.lang
    }
  }, [langState.lang])

  const t = useCallback(
    (key: TranslationKey, params?: Record<string, string | number>): string => {
      const dict = dictionaries[langState.lang] || dictionaries.en
      let text = dict[key] || dictionaries.en[key] || (key as string)
      if (params) {
        Object.entries(params).forEach(([paramKey, val]) => {
          text = text.replace(new RegExp(`\\{${paramKey}\\}`, 'g'), String(val))
        })
      }
      return text
    },
    [langState.lang]
  )

  const value = useMemo(
    () => ({
      lang: langState.lang,
      setLang,
      toggleLang,
      t,
      isAutoDetected: langState.isAuto,
    }),
    [langState.lang, langState.isAuto, setLang, toggleLang, t]
  )

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>
}

