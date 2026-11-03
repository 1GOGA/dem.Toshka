import React, { useState } from 'react'
import { useTranslation } from '../i18n'

interface SupportDonateModalProps {
  isOpen: boolean
  onClose: () => void
}

export const SupportDonateModal: React.FC<SupportDonateModalProps> = ({ isOpen, onClose }) => {
  const { lang } = useTranslation()
  const [copiedKey, setCopiedKey] = useState<string | null>(null)

  if (!isOpen) return null

  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text)
    setCopiedKey(key)
    setTimeout(() => setCopiedKey(null), 2500)
  }

  const tradeUrl = 'https://steamcommunity.com/tradeoffer/new/?partner=1076140204&token=-A3e3Vab'
  const donationAlertsUrl = 'https://www.donationalerts.com/r/pytoshka_'
  const twitchUrl = 'https://www.twitch.tv/pytoshka_'

  return (
    <div
      className="modal-overlay"
      onClick={onClose}
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(5, 7, 12, 0.85)',
        backdropFilter: 'blur(8px)',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '16px',
        animation: 'fadeIn 0.15s ease',
      }}
    >
      <div
        className="modal-content card-interactive"
        onClick={(e) => e.stopPropagation()}
        style={{
          width: '100%',
          maxWidth: '520px',
          backgroundColor: '#0f131c',
          border: '1px solid rgba(56, 189, 248, 0.35)',
          borderRadius: '16px',
          boxShadow: '0 20px 50px rgba(0, 0, 0, 0.7), 0 0 30px rgba(56, 189, 248, 0.15)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: '18px 22px',
            borderBottom: '1px solid #1e2638',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            background: 'linear-gradient(90deg, rgba(236, 72, 153, 0.1) 0%, rgba(56, 189, 248, 0.1) 100%)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '34px',
                height: '34px',
                borderRadius: '8px',
                background: 'linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 4px 12px rgba(236, 72, 153, 0.4)',
              }}
            >
              <span style={{ fontSize: '18px' }}>💖</span>
            </div>
            <div>
              <div style={{ fontSize: '15px', fontWeight: 800, color: '#f8fafc', letterSpacing: '-0.01em' }}>
                {lang === 'ru' ? 'Поддержать автора и проект' : 'Support Creator & Project'}
              </div>
              <div style={{ fontSize: '11px', color: '#94a3b8' }}>
                dem.Toshka • by pytoshka
              </div>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#94a3b8',
              fontSize: '20px',
              cursor: 'pointer',
              lineHeight: 1,
              padding: '4px 8px',
              borderRadius: '6px',
            }}
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div style={{ padding: '22px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <p style={{ margin: 0, fontSize: '13px', color: '#cbd5e1', lineHeight: 1.5 }}>
            {lang === 'ru'
              ? 'dem.Toshka развивается полностью бесплатно для CS2 комьюнити. Если программа экономит твоё время и помогает делать крутые хайлайты — любая поддержка греет душу и ускоряет обновления!'
              : 'dem.Toshka is completely free for the CS2 community. If the tool saves your time and helps create sick clips — any support is genuinely appreciated and fuels new updates!'}
          </p>

          {/* Option 1: DonationAlerts */}
          <div
            style={{
              padding: '14px',
              borderRadius: '10px',
              backgroundColor: '#141824',
              border: '1px solid #232d42',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '12px',
              transition: 'all 0.2s ease',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div
                style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '10px',
                  backgroundColor: 'rgba(249, 115, 22, 0.15)',
                  border: '1px solid rgba(249, 115, 22, 0.3)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '20px',
                }}
              >
                ⚡
              </div>
              <div>
                <div style={{ fontSize: '13px', fontWeight: 700, color: '#f1f5f9' }}>
                  DonationAlerts
                </div>
                <div style={{ fontSize: '11px', color: '#94a3b8' }}>
                  {lang === 'ru' ? 'Карты РФ, СБП, QIWI, зарубежные карты' : 'Bank cards, SBP, QIWI, international'}
                </div>
              </div>
            </div>

            <a
              href={donationAlertsUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="btn card-interactive"
              style={{
                backgroundColor: '#f97316',
                color: '#ffffff',
                border: 'none',
                padding: '8px 14px',
                borderRadius: '8px',
                fontSize: '12px',
                fontWeight: 700,
                textDecoration: 'none',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                whiteSpace: 'nowrap',
              }}
            >
              <span>{lang === 'ru' ? 'Задонатить' : 'Donate'}</span>
              <span>➔</span>
            </a>
          </div>

          {/* Option 2: Steam Trade URL (Skins) */}
          <div
            style={{
              padding: '14px',
              borderRadius: '10px',
              backgroundColor: '#141824',
              border: '1px solid #232d42',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '12px',
              transition: 'all 0.2s ease',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div
                style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '10px',
                  backgroundColor: 'rgba(56, 189, 248, 0.15)',
                  border: '1px solid rgba(56, 189, 248, 0.3)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#38bdf8',
                }}
              >
                <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M11.979 0C5.678 0 .511 4.86.022 11.037l6.432 2.658c.545-.371 1.203-.59 1.912-.59.063 0 .125.004.188.006l2.861-4.142V8.91c0-2.495 2.028-4.524 4.524-4.524 2.494 0 4.524 2.031 4.524 4.527s-2.03 4.525-4.524 4.525h-.105l-4.076 2.911c0 .052.005.105.005.159 0 1.875-1.515 3.396-3.39 3.396-1.635 0-3.016-1.173-3.331-2.727L.436 14.85C1.848 20.086 6.613 24 12.233 24c6.627 0 12-5.373 12-12S18.605 0 11.979 0z" />
                </svg>
              </div>
              <div>
                <div style={{ fontSize: '13px', fontWeight: 700, color: '#f1f5f9' }}>
                  Steam Trade Offer
                </div>
                <div style={{ fontSize: '11px', color: '#94a3b8' }}>
                  {lang === 'ru' ? 'Скины, кейсы или граффити CS2' : 'CS2 skins, cases or graffiti'}
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '6px' }}>
              <button
                type="button"
                className="btn card-interactive"
                onClick={() => handleCopy(tradeUrl, 'trade')}
                style={{
                  backgroundColor: '#1e2638',
                  color: copiedKey === 'trade' ? '#34d399' : '#94a3b8',
                  border: '1px solid #2d3748',
                  padding: '7px 10px',
                  borderRadius: '8px',
                  fontSize: '11px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  whiteSpace: 'nowrap',
                }}
              >
                {copiedKey === 'trade' ? '✓ ' + (lang === 'ru' ? 'Скопировано' : 'Copied') : (lang === 'ru' ? 'Копия' : 'Copy')}
              </button>
              <a
                href={tradeUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="btn card-interactive"
                style={{
                  backgroundColor: '#0284c7',
                  color: '#ffffff',
                  border: 'none',
                  padding: '8px 14px',
                  borderRadius: '8px',
                  fontSize: '12px',
                  fontWeight: 700,
                  textDecoration: 'none',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  whiteSpace: 'nowrap',
                }}
              >
                <span>{lang === 'ru' ? 'Трейд' : 'Trade'}</span>
                <span>➔</span>
              </a>
            </div>
          </div>

          {/* Option 3: Twitch Follow / Sub */}
          <div
            style={{
              padding: '14px',
              borderRadius: '10px',
              backgroundColor: '#141824',
              border: '1px solid #232d42',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '12px',
              transition: 'all 0.2s ease',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div
                style={{
                  width: '40px',
                  height: '40px',
                  borderRadius: '10px',
                  backgroundColor: 'rgba(168, 85, 247, 0.15)',
                  border: '1px solid rgba(168, 85, 247, 0.3)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#a855f7',
                }}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M11.571 4.714h1.715v5.143H11.57zm4.715 0H18v5.143h-1.714zM6 0L1.714 4.286v15.428h5.143V24l4.286-4.286h3.428L22.286 12V0zm14.571 11.143l-3.428 3.428h-3.429l-3 3v-3H6.857V1.714h13.714Z" />
                </svg>
              </div>
              <div>
                <div style={{ fontSize: '13px', fontWeight: 700, color: '#f1f5f9' }}>
                  Twitch (pytoshka_)
                </div>
                <div style={{ fontSize: '11px', color: '#94a3b8' }}>
                  {lang === 'ru' ? 'Фоллоу, сабка или баллы канала' : 'Follow, sub or channel points'}
                </div>
              </div>
            </div>

            <a
              href={twitchUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="btn card-interactive"
              style={{
                backgroundColor: '#9333ea',
                color: '#ffffff',
                border: 'none',
                padding: '8px 14px',
                borderRadius: '8px',
                fontSize: '12px',
                fontWeight: 700,
                textDecoration: 'none',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                whiteSpace: 'nowrap',
              }}
            >
              <span>{lang === 'ru' ? 'Смотреть' : 'Watch'}</span>
              <span>➔</span>
            </a>
          </div>
        </div>

        {/* Footer info */}
        <div
          style={{
            padding: '12px 22px',
            backgroundColor: '#0a0d14',
            borderTop: '1px solid #1a202c',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontSize: '11px',
            color: '#64748b',
          }}
        >
          <span>{lang === 'ru' ? 'Спасибо за любую поддержку! ❤️' : 'Thanks for every bit of support! ❤️'}</span>
          <button
            type="button"
            onClick={onClose}
            className="btn btn-secondary"
            style={{ fontSize: '11px', padding: '4px 10px' }}
          >
            {lang === 'ru' ? 'Закрыть' : 'Close'}
          </button>
        </div>
      </div>
    </div>
  )
}

