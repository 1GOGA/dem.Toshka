import React, { useState, useEffect } from 'react'
import { api } from '../api'
import type { HighlightItem } from '../types'
import { useTranslation } from '../i18n'

interface SocialDraftModalProps {
  highlight: HighlightItem | null
  mapName?: string | null
  onClose: () => void
}

export const SocialDraftModal: React.FC<SocialDraftModalProps> = ({
  highlight,
  mapName,
  onClose,
}) => {
  const safeMapName = mapName || 'de_mirage'
  const { lang } = useTranslation()
  const [platform, setPlatform] = useState<'telegram' | 'youtube_shorts' | 'tiktok'>('telegram')
  const [draftText, setDraftText] = useState<string>('')
  const [loading, setLoading] = useState<boolean>(false)
  const [copied, setCopied] = useState<boolean>(false)

  useEffect(() => {
    if (!highlight) return

    setLoading(true)
    const durationSec = Math.max(
      1.0,
      ((highlight.kill_end_tick || highlight.clip_end_tick) - (highlight.kill_start_tick || highlight.clip_start_tick)) / 128
    )

    api
      .createSocialDraft({
        player_name: highlight.pov_name || 'Player',
        map_name: safeMapName,
        highlight_type: highlight.highlight_type,
        primary_weapon: highlight.tags?.[0] || 'm4a1',
        round_num: highlight.round_num,
        kill_count: highlight.kill_count,
        score: highlight.kill_count * 20.0,
        duration_sec: durationSec,
        platform,
      })
      .then((res) => {
        setDraftText(res.text)
      })
      .catch((err) => {
        console.error('Error fetching social draft:', err)
        setDraftText(`${highlight.pov_name || 'Player'} — ${highlight.highlight_type.toUpperCase()} #${safeMapName}`)
      })
      .finally(() => {
        setLoading(false)
      })
  }, [highlight, safeMapName, platform])

  if (!highlight) return null

  const handleCopy = () => {
    if (!draftText) return
    navigator.clipboard.writeText(draftText)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(5, 7, 12, 0.75)',
        backdropFilter: 'blur(6px)',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px',
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '560px',
          backgroundColor: '#0f131d',
          border: '1px solid #283046',
          borderRadius: '14px',
          boxShadow: '0 20px 50px rgba(0,0,0,0.6), 0 0 30px rgba(56, 189, 248, 0.15)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            padding: '16px 20px',
            borderBottom: '1px solid #232a3d',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            backgroundColor: '#141a27',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '20px' }}>📱</span>
            <div>
              <div style={{ fontSize: '15px', fontWeight: 800, color: '#f8fafc' }}>
                {lang === 'ru' ? 'Генератор описания для соцсетей' : 'Social Media Content Producer'}
              </div>
              <div style={{ fontSize: '12px', color: '#94a3b8' }}>
                {highlight.pov_name} • {highlight.highlight_type.toUpperCase()} (Р{highlight.round_num})
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#94a3b8',
              fontSize: '20px',
              cursor: 'pointer',
              padding: '4px',
            }}
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Platform Switcher */}
          <div
            style={{
              display: 'flex',
              gap: '6px',
              backgroundColor: '#090d16',
              padding: '4px',
              borderRadius: '8px',
              border: '1px solid #1e2536',
            }}
          >
            <button
              type="button"
              onClick={() => setPlatform('telegram')}
              style={{
                flex: 1,
                padding: '8px 12px',
                fontSize: '12px',
                fontWeight: 700,
                borderRadius: '6px',
                border: 'none',
                cursor: 'pointer',
                backgroundColor: platform === 'telegram' ? '#0ea5e9' : 'transparent',
                color: platform === 'telegram' ? '#fff' : '#94a3b8',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px',
                transition: 'all 0.15s ease',
              }}
            >
              <span>✈️ Telegram</span>
            </button>
            <button
              type="button"
              onClick={() => setPlatform('youtube_shorts')}
              style={{
                flex: 1,
                padding: '8px 12px',
                fontSize: '12px',
                fontWeight: 700,
                borderRadius: '6px',
                border: 'none',
                cursor: 'pointer',
                backgroundColor: platform === 'youtube_shorts' ? '#ef4444' : 'transparent',
                color: platform === 'youtube_shorts' ? '#fff' : '#94a3b8',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px',
                transition: 'all 0.15s ease',
              }}
            >
              <span>🔴 YouTube Shorts</span>
            </button>
            <button
              type="button"
              onClick={() => setPlatform('tiktok')}
              style={{
                flex: 1,
                padding: '8px 12px',
                fontSize: '12px',
                fontWeight: 700,
                borderRadius: '6px',
                border: 'none',
                cursor: 'pointer',
                backgroundColor: platform === 'tiktok' ? '#a855f7' : 'transparent',
                color: platform === 'tiktok' ? '#fff' : '#94a3b8',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px',
                transition: 'all 0.15s ease',
              }}
            >
              <span>🎵 TikTok / Reels</span>
            </button>
          </div>

          {/* Draft Preview / Textarea */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <label style={{ fontSize: '12px', fontWeight: 700, color: '#cbd5e1' }}>
                {lang === 'ru' ? 'Сгенерированный текст и теги:' : 'Generated Post Copy & Tags:'}
              </label>
              <span style={{ fontSize: '11px', color: '#64748b' }}>
                {draftText.length} {lang === 'ru' ? 'символов' : 'characters'}
              </span>
            </div>
            <textarea
              value={loading ? (lang === 'ru' ? 'Генерация описания...' : 'Generating copy...') : draftText}
              onChange={(e) => setDraftText(e.target.value)}
              disabled={loading}
              rows={6}
              style={{
                width: '100%',
                backgroundColor: '#090d16',
                border: '1px solid #232b3f',
                borderRadius: '8px',
                padding: '12px',
                color: '#e2e8f0',
                fontSize: '13px',
                lineHeight: 1.5,
                resize: 'vertical',
                outline: 'none',
                fontFamily: 'inherit',
              }}
            />
          </div>

          {/* Action Buttons */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '4px' }}>
            <button
              type="button"
              onClick={onClose}
              style={{
                padding: '8px 16px',
                fontSize: '13px',
                fontWeight: 600,
                backgroundColor: '#1e2536',
                color: '#cbd5e1',
                border: '1px solid #2d3748',
                borderRadius: '8px',
                cursor: 'pointer',
              }}
            >
              {lang === 'ru' ? 'Закрыть' : 'Close'}
            </button>
            <button
              type="button"
              onClick={handleCopy}
              disabled={loading || !draftText}
              style={{
                padding: '8px 20px',
                fontSize: '13px',
                fontWeight: 800,
                backgroundColor: copied ? '#10b981' : '#38bdf8',
                color: '#090d16',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                transition: 'all 0.15s ease',
                boxShadow: copied ? '0 0 16px rgba(16, 185, 129, 0.4)' : '0 0 16px rgba(56, 189, 248, 0.3)',
              }}
            >
              <span>{copied ? '✓' : '📋'}</span>
              <span>
                {copied
                  ? lang === 'ru'
                    ? 'Скопировано!'
                    : 'Copied!'
                  : lang === 'ru'
                  ? 'Скопировать текст'
                  : 'Copy Post Text'}
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
