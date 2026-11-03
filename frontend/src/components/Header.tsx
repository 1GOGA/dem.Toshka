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
  onOpenDonate?: () => void
  currentDemo: DemoSummary | null
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  onTabChange,
  selectedCount,
  onOpenQueue,
  onOpenSettings,
  onOpenDonate,
  currentDemo,
}) => {
  const { t, lang } = useTranslation()

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
          title={lang === 'ru' ? 'Студия хайлайтов CS2 — выбор раундов, фильтры игроков, HLAE/OBS настройки и рендер' : 'CS2 Highlights Studio — round selection, player filters, HLAE/OBS settings and render'}
        >
          <ClapperboardIcon size={15} color={activeTab === 'studio' ? '#38bdf8' : '#38bdf8'} />
          <span>{t('nav.studio')}</span>
        </button>

        {/* 3. 2D Tactical Replay (3-й слева: радар и таймеры раунда) */}
        <button
          className={`nav-tab ${activeTab === 'replay' ? 'active' : ''}`}
          onClick={() => onTabChange('replay')}
          title={lang === 'ru' ? 'Тактический 2D Реплей — радар, траектории игроков и таймеры гранат' : 'Tactical 2D Replay — radar, player paths and grenade timers'}
        >
          <RadarIcon size={15} color={activeTab === 'replay' ? '#38bdf8' : 'currentColor'} />
          <span>{t('nav.replay')}</span>
        </button>

        {/* 4. Match Overview & Analytics (4-й слева: статистика матча) */}
        <button
          className={`nav-tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => onTabChange('overview')}
          title={lang === 'ru' ? 'Аналитика матча — таблица счёта, ADR, HS%, раунды и фраги' : 'Match Analytics — scoreboard, ADR, HS%, rounds and kills'}
        >
          <ChartIcon size={15} color={activeTab === 'overview' ? '#38bdf8' : 'currentColor'} />
          <span>{t('nav.match')}</span>
        </button>

        {/* 5. Clips & Montage */}
        <button
          className={`nav-tab ${activeTab === 'clips' ? 'active' : ''}`}
          onClick={() => onTabChange('clips')}
          title={lang === 'ru' ? 'Готовые клипы и монтаж — видеотека MP4 и объединение в ролики' : 'Clips & Montage — MP4 gallery and highlight compilation'}
        >
          <FilmIcon size={15} color={activeTab === 'clips' ? '#38bdf8' : 'currentColor'} />
          <span>{t('nav.clips')}</span>
        </button>

        {/* 6. Library (Ближе к Настройкам) */}
        <button
          className={`nav-tab ${activeTab === 'library' ? 'active' : ''}`}
          onClick={() => onTabChange('library')}
          title={lang === 'ru' ? 'Библиотека CS2 демок — импорт .dem, парсинг и переключение матчей' : 'CS2 Demo Library — import .dem, parse and switch matches'}
        >
          <FolderIcon size={15} color={activeTab === 'library' ? '#38bdf8' : 'currentColor'} />
          <span>{t('nav.library')}</span>
        </button>

        {/* 7. Settings */}
        <button
          className={`nav-tab ${activeTab === 'settings' ? 'active' : ''}`}
          onClick={() => onTabChange('settings')}
          title={lang === 'ru' ? 'Настройки — CS2 Config Shield, HLAE, каталоги сохранения и очистка' : 'Settings — CS2 Config Shield, HLAE, save directories and cleanup'}
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
          <a
            href="https://www.twitch.tv/pytoshka_"
            target="_blank"
            rel="noopener noreferrer"
            title="Twitch: pytoshka_"
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '32px',
              height: '32px',
              borderRadius: '7px',
              background: 'rgba(168, 85, 247, 0.08)',
              border: '1px solid rgba(168, 85, 247, 0.25)',
              color: '#a855f7',
              textDecoration: 'none',
              transition: 'all 0.2s',
            }}
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor">
              <path d="M11.571 4.714h1.715v5.143H11.57zm4.715 0H18v5.143h-1.714zM6 0L1.714 4.286v15.428h5.143V24l4.286-4.286h3.428L22.286 12V0zm14.571 11.143l-3.428 3.428h-3.429l-3 3v-3H6.857V1.714h13.714Z" />
            </svg>
          </a>
          <a
            href="https://github.com/1GOGA/dem.Toshka"
            target="_blank"
            rel="noopener noreferrer"
            title="GitHub: 1GOGA/dem.Toshka"
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '32px',
              height: '32px',
              borderRadius: '7px',
              background: 'rgba(255, 255, 255, 0.06)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              color: '#e2e8f0',
              textDecoration: 'none',
              transition: 'all 0.2s',
            }}
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor">
              <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
            </svg>
          </a>
        </div>

        {/* Active Demo Badge / Quick Ingestion Switcher */}
        {currentDemo ? (
          <div
            className="header-demo-pill"
            onClick={() => onTabChange('library')}
            title={lang === 'ru' ? 'Активная демка. Нажмите для выбора другой в Библиотеке' : 'Active demo. Click to select another in Library'}
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
            title={lang === 'ru' ? 'Нажмите, чтобы выбрать или загрузить демку в Библиотеке' : 'Click to select or upload a demo in Library'}
          >
            <FolderIcon size={12} color="#38bdf8" />
            <span>{lang === 'ru' ? 'Выбрать демку' : 'Select Demo'}</span>
          </button>
        )}

        {/* Support & Donate Button */}
        {onOpenDonate && (
          <button
            type="button"
            className="btn card-interactive"
            onClick={onOpenDonate}
            title={lang === 'ru' ? 'Поддержать создателя (DonationAlerts, Steam скинчики, Twitch)' : 'Support creator (DonationAlerts, Steam skins, Twitch)'}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              backgroundColor: 'rgba(236, 72, 153, 0.12)',
              color: '#f472b6',
              border: '1px solid rgba(236, 72, 153, 0.35)',
              fontWeight: 700,
              padding: '6px 12px',
              borderRadius: '8px',
              fontSize: '12px',
              cursor: 'pointer',
              boxShadow: '0 0 12px rgba(236, 72, 153, 0.2)',
            }}
          >
            <span style={{ fontSize: '13px' }}>💖</span>
            <span>{lang === 'ru' ? 'Донат' : 'Donate'}</span>
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
        <button
          className="btn btn-queue"
          onClick={onOpenQueue}
          title={lang === 'ru' ? 'Очередь рендера и мониторинг задач' : 'Render queue and job monitoring'}
        >
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
