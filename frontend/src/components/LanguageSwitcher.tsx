import React, { useState } from 'react'
import { useTranslation } from '../i18n'

export const LanguageSwitcher: React.FC = () => {
  const { lang, toggleLang, isAutoDetected } = useTranslation()
  const [isHovered, setIsHovered] = useState(false)

  return (
    <div
      className="lang-switcher-container"
      style={{
        position: 'fixed',
        bottom: '20px',
        right: '20px',
        zIndex: 100,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-end',
        gap: '6px',
        pointerEvents: 'auto',
      }}
    >
      {/* Tooltip on hover */}
      {isHovered && (
        <div
          style={{
            background: 'rgba(8, 11, 17, 0.95)',
            border: '1px solid rgba(56, 189, 248, 0.25)',
            boxShadow: '0 4px 16px rgba(0, 0, 0, 0.6)',
            borderRadius: '6px',
            padding: '4px 10px',
            fontSize: '11px',
            color: '#94a3b8',
            whiteSpace: 'nowrap',
            animation: 'fadeIn 0.15s ease',
            pointerEvents: 'none',
          }}
        >
          <span>{lang === 'ru' ? 'Сменить язык на English' : 'Switch language to Русский'}</span>
          {isAutoDetected && (
            <span style={{ color: '#38bdf8', marginLeft: '6px' }}>
              • {lang === 'ru' ? 'Авто: устройство' : 'Auto: device'}
            </span>
          )}
        </div>
      )}

      {/* Switch Button */}
      <button
        type="button"
        className="lang-switcher-btn card-interactive"
        onClick={toggleLang}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        title={lang === 'ru' ? 'Сменить язык / Switch language' : 'Switch language / Сменить язык'}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '7px 14px',
          background: 'rgba(10, 13, 20, 0.88)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(56, 189, 248, 0.35)',
          borderRadius: '24px',
          color: '#f8fafc',
          cursor: 'pointer',
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.6), 0 0 12px rgba(56, 189, 248, 0.2)',
          userSelect: 'none',
          transition: 'all 0.18s cubic-bezier(0.16, 1, 0.3, 1)',
        }}
      >
        {/* Globe SVG */}
        <svg
          width="15"
          height="15"
          viewBox="0 0 24 24"
          fill="none"
          stroke="#38bdf8"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          style={{ flexShrink: 0 }}
        >
          <circle cx="12" cy="12" r="10" />
          <line x1="2" y1="12" x2="22" y2="12" />
          <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
        </svg>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            fontSize: '12px',
            fontWeight: 800,
            fontFamily: 'Space Grotesk, sans-serif',
          }}
        >
          <span
            style={{
              color: lang === 'ru' ? '#38bdf8' : '#64748b',
              transition: 'color 0.15s ease',
            }}
          >
            RU
          </span>
          <span style={{ color: '#334155' }}>/</span>
          <span
            style={{
              color: lang === 'en' ? '#38bdf8' : '#64748b',
              transition: 'color 0.15s ease',
            }}
          >
            EN
          </span>
        </div>
      </button>
    </div>
  )
}
