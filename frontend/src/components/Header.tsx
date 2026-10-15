import React from 'react'
import type { DemoSummary } from '../types'

export type TabType = 'showcase' | 'library' | 'overview' | 'replay' | 'studio' | 'clips' | 'settings'

interface HeaderProps {
  activeTab: TabType
  onTabChange: (tab: TabType) => void
  selectedCount: number
  onOpenQueue: () => void
  onOpenSettings?: () => void
  currentDemo: DemoSummary | null
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  onTabChange,
  selectedCount,
  onOpenQueue,
  onOpenSettings,
  currentDemo,
}) => {
  return (
    <header className="app-header">
      <div className="brand" onClick={() => onTabChange('showcase')} style={{ cursor: 'pointer' }} title="Главная витрина проекта dem.Toshka">
        <div className="brand-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <polygon points="5 3 19 12 5 21 5 3" />
          </svg>
        </div>
        <div>
          <div className="brand-title">
            dem.Toshka <span style={{ color: '#38bdf8', fontWeight: 400 }}>|</span> pytoshka
          </div>
          <div className="brand-subtitle">CS2 Highlights Studio</div>
        </div>
      </div>

      <nav className="nav-tabs">
        {/* Showcase / Overview Tab */}
        <button
          className={`nav-tab ${activeTab === 'showcase' ? 'active' : ''}`}
          onClick={() => onTabChange('showcase')}
          style={{
            borderColor: activeTab === 'showcase' ? '#38bdf8' : undefined,
            color: activeTab === 'showcase' ? '#38bdf8' : undefined,
          }}
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
          </svg>
          ✨ Обзор проекта
        </button>

        {/* Library Tab */}
        <button
          className={`nav-tab ${activeTab === 'library' ? 'active' : ''}`}
          onClick={() => onTabChange('library')}
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
          </svg>
          Library
        </button>

        {/* Match Overview Tab */}
        <button
          className={`nav-tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => onTabChange('overview')}
          disabled={!currentDemo}
          style={{ opacity: currentDemo ? 1 : 0.4 }}
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="3" width="18" height="18" rx="2" />
            <path d="M3 9h18" />
            <path d="M9 21V9" />
          </svg>
          Match
        </button>

        {/* 2D Replay Tab */}
        <button
          className={`nav-tab ${activeTab === 'replay' ? 'active' : ''}`}
          onClick={() => onTabChange('replay')}
          disabled={!currentDemo}
          style={{ opacity: currentDemo ? 1 : 0.4 }}
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <circle cx="12" cy="12" r="4" />
            <line x1="4.93" y1="4.93" x2="9.17" y2="9.17" />
            <line x1="14.83" y1="14.83" x2="19.07" y2="19.07" />
          </svg>
          2D Replay
        </button>

        {/* Highlights Studio Tab */}
        <button
          className={`nav-tab ${activeTab === 'studio' ? 'active' : ''}`}
          onClick={() => onTabChange('studio')}
          disabled={!currentDemo}
          style={{ opacity: currentDemo ? 1 : 0.4 }}
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="m18 8 4 4-4 4" />
            <path d="M6 16l-4-4 4-4" />
            <path d="M14 4l-4 16" />
          </svg>
          Render Studio
        </button>

        {/* Clips & Montage Tab */}
        <button
          className={`nav-tab ${activeTab === 'clips' ? 'active' : ''}`}
          onClick={() => onTabChange('clips')}
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18" />
            <line x1="7" y1="2" x2="7" y2="22" />
            <line x1="17" y1="2" x2="17" y2="22" />
            <line x1="2" y1="12" x2="22" y2="12" />
          </svg>
          Clips & Montage
        </button>

        {/* Settings Tab */}
        <button
          className={`nav-tab ${activeTab === 'settings' ? 'active' : ''}`}
          onClick={() => onTabChange('settings')}
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="3" />
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
          </svg>
          Settings
        </button>
      </nav>

      <div className="header-actions">
        {/* Creator Links */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginRight: '8px' }}>
          <a
            href="https://t.me/thepytoshka"
            target="_blank"
            rel="noopener noreferrer"
            title="Telegram-канал разработчика @thepytoshka"
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '32px',
              height: '32px',
              borderRadius: '6px',
              background: 'rgba(56, 189, 248, 0.1)',
              border: '1px solid rgba(56, 189, 248, 0.25)',
              color: '#38bdf8',
              textDecoration: 'none',
              transition: 'all 0.2s',
            }}
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.2.2 0 00-.05-.18c-.06-.05-.14-.03-.21-.02-.09.02-1.49.95-4.22 2.79-.4.27-.76.41-1.08.4-.36-.01-1.04-.2-1.55-.37-.63-.2-1.12-.31-1.08-.66.02-.18.27-.36.74-.55 2.92-1.27 4.86-2.11 5.83-2.51 2.78-1.16 3.35-1.36 3.73-1.36.08 0 .27.02.39.12.1.08.13.19.14.27-.01.06.01.24 0 .38z" />
            </svg>
          </a>
          <a
            href="https://www.youtube.com/@thePytoshka"
            target="_blank"
            rel="noopener noreferrer"
            title="YouTube-канал разработчика @thePytoshka"
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '32px',
              height: '32px',
              borderRadius: '6px',
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.25)',
              color: '#ef4444',
              textDecoration: 'none',
              transition: 'all 0.2s',
            }}
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor">
              <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
            </svg>
          </a>
        </div>

        {currentDemo && (
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginRight: '8px' }}>
            <span style={{ color: '#38bdf8', fontWeight: 700 }}>
              {(currentDemo.map_name || 'Match').replace('de_', '').toUpperCase()}
            </span>
            {' • '}
            <span>{currentDemo.rounds_count}R</span>
          </div>
        )}

        {onOpenSettings && (
          <button className="btn btn-secondary" onClick={onOpenSettings} title="Параметры видеоклипа">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="3" />
            </svg>
            Параметры
          </button>
        )}

        <button className="btn btn-queue" onClick={onOpenQueue}>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
          </svg>
          Queue
          {selectedCount > 0 && <span className="queue-badge">{selectedCount}</span>}
        </button>
      </div>
    </header>
  )
}
