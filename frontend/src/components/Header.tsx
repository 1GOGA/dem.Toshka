import React from 'react'
import type { DemoSummary } from '../types'

export type TabType = 'library' | 'overview' | 'replay' | 'studio' | 'clips' | 'settings'

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
      <div className="brand" onClick={() => onTabChange('library')} style={{ cursor: 'pointer' }}>
        <div className="brand-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <polygon points="5 3 19 12 5 21 5 3" />
          </svg>
        </div>
        <div>
          <div className="brand-title">dem.Toshka</div>
          <div className="brand-subtitle">CS2 Highlights & Tactical Studio</div>
        </div>
      </div>

      <nav className="nav-tabs">
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
