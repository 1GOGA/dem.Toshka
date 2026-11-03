import React, { useState } from 'react'
import { useTranslation } from '../i18n'

interface TwitchLiveWidgetProps {
  channelName?: string
}

export const TwitchLiveWidget: React.FC<TwitchLiveWidgetProps> = ({ channelName = 'pytoshka_' }) => {
  const { lang } = useTranslation()
  const [isOpen, setIsOpen] = useState(false)
  const [isDismissed, setIsDismissed] = useState(false)

  // Current domain hostname for Twitch parent parameter
  const parentDomain = typeof window !== 'undefined' ? window.location.hostname || 'localhost' : 'localhost'

  if (isDismissed) return null

  return (
    <div
      style={{
        position: 'fixed',
        bottom: '24px',
        left: '24px',
        zIndex: 9990,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-start',
        gap: '8px',
        pointerEvents: 'auto',
      }}
    >
      {/* Expanded Twitch Stream Embed */}
      {isOpen && (
        <div
          style={{
            width: '360px',
            height: '240px',
            backgroundColor: '#0c0f17',
            border: '1px solid #9333ea',
            borderRadius: '12px',
            overflow: 'hidden',
            boxShadow: '0 12px 36px rgba(0, 0, 0, 0.8), 0 0 24px rgba(147, 51, 234, 0.35)',
            display: 'flex',
            flexDirection: 'column',
            animation: 'fadeIn 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
          }}
        >
          {/* Stream header */}
          <div
            style={{
              padding: '6px 12px',
              backgroundColor: '#120f1e',
              borderBottom: '1px solid rgba(147, 51, 234, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span
                style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  backgroundColor: '#ef4444',
                  boxShadow: '0 0 8px #ef4444',
                  display: 'inline-block',
                }}
              />
              <span style={{ fontSize: '11px', fontWeight: 800, color: '#f1f5f9' }}>
                Twitch: {channelName}
              </span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <a
                href={`https://www.twitch.tv/${channelName}`}
                target="_blank"
                rel="noopener noreferrer"
                title={lang === 'ru' ? 'Открыть на Twitch в браузере' : 'Open in browser on Twitch'}
                style={{
                  color: '#a855f7',
                  fontSize: '11px',
                  fontWeight: 700,
                  textDecoration: 'none',
                  padding: '2px 6px',
                  borderRadius: '4px',
                  backgroundColor: 'rgba(168, 85, 247, 0.15)',
                }}
              >
                ↗ Twitch
              </a>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                title={lang === 'ru' ? 'Свернуть' : 'Minimize'}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#94a3b8',
                  fontSize: '14px',
                  cursor: 'pointer',
                  padding: '0 4px',
                }}
              >
                ✕
              </button>
            </div>
          </div>

          {/* Twitch Player Iframe */}
          <div style={{ flex: 1, width: '100%', height: '100%', backgroundColor: '#000000' }}>
            <iframe
              src={`https://player.twitch.tv/?channel=${channelName}&parent=${parentDomain}&parent=127.0.0.1&parent=localhost&muted=true`}
              height="100%"
              width="100%"
              allowFullScreen
              style={{ border: 'none' }}
              title="Twitch Stream Player"
            />
          </div>
        </div>
      )}

      {/* Collapsed Pill Button */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
        <button
          type="button"
          className="btn card-interactive"
          onClick={() => setIsOpen((prev) => !prev)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '7px 12px',
            borderRadius: '10px',
            backgroundColor: isOpen ? '#9333ea' : '#141120',
            border: '1px solid rgba(168, 85, 247, 0.5)',
            boxShadow: '0 4px 16px rgba(0, 0, 0, 0.5), 0 0 12px rgba(168, 85, 247, 0.25)',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
          }}
          title={lang === 'ru' ? 'Стрим создателя pytoshka_ на Twitch' : 'Creator stream on Twitch'}
        >
          {/* Twitch Logo SVG */}
          <svg width="15" height="15" viewBox="0 0 24 24" fill={isOpen ? '#ffffff' : '#a855f7'}>
            <path d="M11.571 4.714h1.715v5.143H11.57zm4.715 0H18v5.143h-1.714zM6 0L1.714 4.286v15.428h5.143V24l4.286-4.286h3.428L22.286 12V0zm14.571 11.143l-3.428 3.428h-3.429l-3 3v-3H6.857V1.714h13.714Z" />
          </svg>

          <span style={{ fontSize: '11px', fontWeight: 800, color: '#ffffff' }}>
            {isOpen ? (lang === 'ru' ? 'Скрыть Twitch' : 'Hide Twitch') : 'Twitch Live'}
          </span>

          <span
            style={{
              width: '7px',
              height: '7px',
              borderRadius: '50%',
              backgroundColor: '#a855f7',
              boxShadow: '0 0 8px #a855f7',
            }}
          />
        </button>

        <button
          type="button"
          onClick={() => setIsDismissed(true)}
          title={lang === 'ru' ? 'Закрыть виджет до следующего запуска' : 'Dismiss widget'}
          style={{
            background: 'rgba(15, 23, 42, 0.7)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '6px',
            color: '#64748b',
            fontSize: '11px',
            width: '20px',
            height: '20px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 0,
          }}
        >
          ✕
        </button>
      </div>
    </div>
  )
}

