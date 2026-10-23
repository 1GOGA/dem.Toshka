import React from 'react'
import type { DemoSummary } from '../types'
import { useTranslation } from '../i18n'
import {
  SparkleIcon,
  FolderIcon,
  ChartIcon,
  RadarIcon,
  ClapperboardIcon,
  FilmIcon,
  SettingsIcon,
} from './Icons'

export type TabType = 'showcase' | 'studio' | 'library' | 'overview' | 'replay' | 'clips' | 'settings'

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
  const { t } = useTranslation()

  return (
    <header className="app-header">
      <div
        className="brand"
        onClick={() => onTabChange('showcase')}
        style={{ cursor: 'pointer' }}
        title={t('brand.showcaseTooltip')}
      >
        <div className="brand-icon">
          <img
            src="/avatar.png"
            alt="dem.Toshka"
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              borderRadius: '7px',
            }}
          />
        </div>
        <div>
          <div className="brand-title">
            dem.Toshka <span style={{ color: '#38bdf8', fontWeight: 400 }}>|</span> pytoshka
          </div>
          <div className="brand-subtitle">{t('brand.subtitle')}</div>
        </div>
      </div>

      <nav className="nav-tabs" aria-label="Main Navigation">
        {/* 1. Showcase / Home */}
        <button
          className={`nav-tab ${activeTab === 'showcase' ? 'active' : ''}`}
          onClick={() => onTabChange('showcase')}
          title={t('brand.showcaseTooltip')}
        >
          <SparkleIcon size={15} color={activeTab === 'showcase' ? '#38bdf8' : 'currentColor'} />
          <span>{t('nav.showcase')}</span>
        </button>

        {/* 2. Highlights Studio (Primary App Workspace) */}
        <button
          className={`nav-tab nav-tab-studio ${activeTab === 'studio' ? 'active' : ''}`}
          onClick={() => onTabChange('studio')}
          title="Студия хайлайтов CS2 — выбор раундов, фильтры игроков, HLAE/OBS настройки и рендер"
        >
          <ClapperboardIcon size={15} color={activeTab === 'studio' ? '#38bdf8' : '#38bdf8'} />
          <span>{t('nav.studio')}</span>
        </button>

        {/* 3. Library (Demos Archive & Ingestion) */}
        <button
          className={`nav-tab ${activeTab === 'library' ? 'active' : ''}`}
          onClick={() => onTabChange('library')}
          title="Библиотека CS2 демок — импорт .dem, парсинг и переключение матчей"
        >
          <FolderIcon size={15} color={activeTab === 'library' ? '#38bdf8' : 'currentColor'} />
          <span>{t('nav.library')}</span>
        </button>

        {/* 4. Match Overview & Analytics */}
        <button
          className={`nav-tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => onTabChange('overview')}
          title="Аналитика матча — таблица счёта, ADR, HS%, раунды и фраги"
        >
          <ChartIcon size={15} color={activeTab === 'overview' ? '#38bdf8' : 'currentColor'} />
          <span>{t('nav.match')}</span>
        </button>

        {/* 5. 2D Tactical Replay */}
        <button
          className={`nav-tab ${activeTab === 'replay' ? 'active' : ''}`}
          onClick={() => onTabChange('replay')}
          title="Тактический 2D Реплей — радар, траектории игроков и таймеры гранат"
        >
          <RadarIcon size={15} color={activeTab === 'replay' ? '#38bdf8' : 'currentColor'} />
          <span>{t('nav.replay')}</span>
        </button>

        {/* 6. Clips & Montage */}
        <button
          className={`nav-tab ${activeTab === 'clips' ? 'active' : ''}`}
          onClick={() => onTabChange('clips')}
          title="Готовые клипы и монтаж — видеотека MP4 и объединение в ролики"
        >
          <FilmIcon size={15} color={activeTab === 'clips' ? '#38bdf8' : 'currentColor'} />
          <span>{t('nav.clips')}</span>
        </button>

        {/* 7. Settings */}
        <button
          className={`nav-tab ${activeTab === 'settings' ? 'active' : ''}`}
          onClick={() => onTabChange('settings')}
          title="Настройки — CS2 Config Shield, HLAE, каталоги сохранения и очистка"
        >
          <SettingsIcon size={15} color={activeTab === 'settings' ? '#38bdf8' : 'currentColor'} />
          <span>{t('nav.settings')}</span>
        </button>
      </nav>

      <div className="header-actions">
        {/* Creator Socials */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <a
            href="https://t.me/thepytoshka"
            target="_blank"
            rel="noopener noreferrer"
            title={t('header.telegramTooltip')}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '32px',
              height: '32px',
              borderRadius: '7px',
              background: 'rgba(56, 189, 248, 0.08)',
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
            title={t('header.youtubeTooltip')}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '32px',
              height: '32px',
              borderRadius: '7px',
              background: 'rgba(239, 68, 68, 0.08)',
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

        {/* Active Demo Badge / Quick Ingestion Switcher */}
        {currentDemo ? (
          <div
            className="header-demo-pill"
            onClick={() => onTabChange('library')}
            title="Активная демка. Нажмите для выбора другой в Библиотеке"
          >
            <span className="header-demo-map">
              {(currentDemo.map_name || 'Match').replace('de_', '').toUpperCase()}
            </span>
            <span className="header-demo-dot">•</span>
            <span className="header-demo-rounds">{currentDemo.rounds_count}R</span>
          </div>
        ) : (
          <button
            type="button"
            className="header-no-demo-pill"
            onClick={() => onTabChange('library')}
            title="Нажмите, чтобы выбрать или загрузить демку в Библиотеке"
          >
            <FolderIcon size={12} color="#38bdf8" />
            <span>Выбрать демку</span>
          </button>
        )}

        {/* Parameters Modal Trigger */}
        {onOpenSettings && (
          <button className="btn btn-secondary" onClick={onOpenSettings} title={t('header.parametersTooltip')}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="3" />
            </svg>
            {t('header.parameters')}
          </button>
        )}

        {/* Render Queue Modal Trigger */}
        <button className="btn btn-queue" onClick={onOpenQueue} title="Очередь рендера и мониторинг задач">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
          </svg>
          {t('header.queue')}
          {selectedCount > 0 && <span className="queue-badge">{selectedCount}</span>}
        </button>
      </div>
    </header>
  )
}
