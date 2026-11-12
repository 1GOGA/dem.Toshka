import React, { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import { useTranslation } from '../i18n'
import type { DemoSummary } from '../types'
import {
  ClapperboardIcon,
  SparkleIcon,
  FilmIcon,
  CheckIcon,
  FolderIcon,
} from './Icons'
import './CinematicStudioView.css'

interface CinematicStudioViewProps {
  currentDemo: DemoSummary | null
  demos: DemoSummary[]
  onSelectDemo: (demo: DemoSummary) => void
  onNavigateTab: (tab: any) => void
}

interface RankedHighlight {
  id: string
  demo_id: number
  highlight_type: string
  round_num: number
  start_tick: number
  end_tick: number
  pov_steam_id?: string
  pov_name?: string
  score: number
  kills_count: number
  kills: any[]
  has_headshot: boolean
  has_wallbang: boolean
  is_ace: boolean
  is_clutch: boolean
}

interface PlannedShot {
  shot_id: string
  highlight_id: string
  round_number: number
  camera_type: string
  purpose: string
  start_tick: number
  end_tick: number
  start_time: number
  end_time: number
  duration_seconds: number
  fov: number
  pov_steam_id?: string
  pov_name?: string
  focus_target_name?: string
  has_campath: boolean
  output_filename: string
  enabled: boolean
  fps: number
  resolution: string
  hud_mode: string
  xray: boolean
  watermark: boolean
  validation_status: string
}

export const CinematicStudioView: React.FC<CinematicStudioViewProps> = ({
  currentDemo,
  demos,
  onSelectDemo,
  onNavigateTab,
}) => {
  const { lang } = useTranslation()

  // Primary View Mode: 'fragmovie' (Master Studio & Live Showcase) vs 'planner' (3D Camera Choreography Wizard)
  const [viewMode, setViewMode] = useState<'fragmovie' | 'planner'>('fragmovie')

  // Fragmovie Master Studio States
  const [productionData, setProductionData] = useState<any | null>(null)
  const [selectedReleaseId, setSelectedReleaseId] = useState<string>('master_16x9')
  const [inspectorTab, setInspectorTab] = useState<'timing' | 'hud' | 'dynamics' | 'fairlight'>('timing')
  const [isPlaying, setIsPlaying] = useState<boolean>(false)
  const [currentTime, setCurrentTime] = useState<number>(0.0)
  const [isMuted, setIsMuted] = useState<boolean>(false)
  const [showQAModal, setShowQAModal] = useState<boolean>(false)
  const videoRef = useRef<HTMLVideoElement | null>(null)

  // 3D Planner States (Steps 1-5)
  const [currentStep, setCurrentStep] = useState<number>(2) // 1=Demo, 2=Highlights, 3=ShotPlan, 4=Capture, 5=Resolve
  const [highlights, setHighlights] = useState<RankedHighlight[]>([])
  const [selectedHighlightIds, setSelectedHighlightIds] = useState<Set<string>>(new Set())
  const [plannedShots, setPlannedShots] = useState<PlannedShot[]>([])
  const [packageSummary, setPackageSummary] = useState<any | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  // Load production overview on mount
  useEffect(() => {
    loadProductionOverview()
  }, [])

  // Load highlights when current demo changes
  useEffect(() => {
    if (currentDemo) {
      loadHighlights(currentDemo.id)
    } else if (demos.length > 0) {
      onSelectDemo(demos[0])
    }
  }, [currentDemo?.id])

  const loadProductionOverview = async () => {
    try {
      const data = await api.getCinematicProductionOverview()
      setProductionData(data)
    } catch (e) {
      console.warn('Could not fetch cinematic production overview:', e)
    }
  }

  const loadHighlights = async (demoId: number) => {
    setIsLoading(true)
    setErrorMsg(null)
    try {
      const data = await api.getCinematicHighlights(demoId)
      setHighlights(data)
      if (data.length > 0) {
        const topIds = new Set(data.slice(0, Math.min(2, data.length)).map((h: any) => h.id))
        setSelectedHighlightIds(topIds)
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to load cinematic highlights')
    } finally {
      setIsLoading(false)
    }
  }

  const toggleHighlight = (id: string) => {
    setSelectedHighlightIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  const selectAllHighlights = () => {
    setSelectedHighlightIds(new Set(highlights.map((h) => h.id)))
  }

  const clearSelection = () => {
    setSelectedHighlightIds(new Set())
  }

  // Generate AI Shot Plan
  const handleGenerateShotPlan = async () => {
    if (!currentDemo || selectedHighlightIds.size === 0) return
    setIsLoading(true)
    setErrorMsg(null)
    try {
      const res = await api.planCinematicShots(currentDemo.id, Array.from(selectedHighlightIds), 60)
      setPlannedShots(res.shots || [])
      setCurrentStep(3)
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to generate shot plan')
    } finally {
      setIsLoading(false)
    }
  }

  const toggleShotEnabled = (shotId: string) => {
    setPlannedShots((prev) =>
      prev.map((s) => (s.shot_id === shotId ? { ...s, enabled: !s.enabled } : s))
    )
  }

  // Build and Export DaVinci Resolve Package
  const handleGeneratePackage = async () => {
    if (!currentDemo || plannedShots.length === 0) return
    setIsLoading(true)
    setErrorMsg(null)
    try {
      const enabledShots = plannedShots.filter((s) => s.enabled)
      const res = await api.createProductionPackage(
        currentDemo.id,
        enabledShots,
        `CS2_${currentDemo.map_name || 'Match'}_Cinematic_Master`
      )
      setPackageSummary(res)
      setCurrentStep(5)
      setSuccessMsg(lang === 'ru' ? 'Пакет для DaVinci Resolve успешно сгенерирован!' : 'DaVinci Resolve package generated successfully!')
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to generate production package')
    } finally {
      setIsLoading(false)
    }
  }

  // Video player controls
  const handleSeek = (timeSeconds: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = timeSeconds
      setCurrentTime(timeSeconds)
    }
  }

  const togglePlay = () => {
    if (videoRef.current) {
      if (videoRef.current.paused) {
        videoRef.current.play()
        setIsPlaying(true)
      } else {
        videoRef.current.pause()
        setIsPlaying(false)
      }
    }
  }

  const getActiveVideoUrl = () => {
    if (!productionData || !productionData.releases) {
      return '/renders/ACE_FINAL_V3_AUDIO_KILLFEED/ACE_FINAL_V3_MASTER.mp4'
    }
    const rel = productionData.releases.find((r: any) => r.id === selectedReleaseId)
    return rel ? rel.url : '/renders/ACE_FINAL_V3_AUDIO_KILLFEED/ACE_FINAL_V3_MASTER.mp4'
  }

  const getCameraBadgeColor = (type: string) => {
    switch (type) {
      case 'FIRST_PERSON':
        return '#38bdf8' // Cyan
      case 'VICTIM_POV':
        return '#ef4444' // Red
      case 'SHOULDER_CAM':
        return '#10b981' // Emerald
      case 'ORBIT_CAMERA':
        return '#f59e0b' // Amber/Gold
      case 'FREECAM_FLYBY':
        return '#a855f7' // Purple
      case 'ESTABLISHING_SHOT':
        return '#06b6d4' // Teal
      case 'TOP_DOWN':
        return '#eab308' // Yellow
      default:
        return '#64748b'
    }
  }

  // Exact timeline event pins
  const eventPins = [
    { time: 7.711, label: '808 Drop', color: '#ec4899', icon: '🎵' },
    { time: 7.830, label: 'Kill 1 (1K)', color: '#ff8c00', icon: '💀' },
    { time: 10.455, label: 'Kill 2 (2K)', color: '#ff5a00', icon: '💀' },
    { time: 12.198, label: 'Kill 3 (HS)', color: '#ef4444', icon: '🎯' },
    { time: 12.998, label: 'Kill 4 (4K)', color: '#dc2626', icon: '💀' },
    { time: 15.538, label: 'Kill 5 (ACE)', color: '#ffd700', icon: '🏆' },
    { time: 15.800, label: '5K Domination', color: '#38bdf8', icon: '👑' },
  ]

  return (
    <div className="cinematic-studio-container">
      {/* Top Banner Navigation & View Mode Switcher */}
      <header className="cinematic-top-nav">
        <div className="cinematic-brand-group">
          <ClapperboardIcon size={24} color="#f59e0b" />
          <div className="cinematic-titles">
            <h2>{lang === 'ru' ? 'CINEMATIC STUDIO — MOVIE DIRECTOR' : 'CINEMATIC STUDIO — MOVIE DIRECTOR'}</h2>
            <span>{lang === 'ru' ? 'AI Кино-режиссер CS2 • Точный бит-дроп • Стековый турнирный киллфид • Чистый CS2 No-HUD' : 'CS2 AI Fragmovie Director • Frame-Accurate Beat Drop • Stacked Killfeed • Clean No-HUD'}</span>
          </div>
        </div>

        {/* View Mode Toggle: Fragmovie Studio vs 3D Planner */}
        <div className="cinematic-mode-switcher">
          <button
            className={`mode-btn ${viewMode === 'fragmovie' ? 'active' : ''}`}
            onClick={() => setViewMode('fragmovie')}
          >
            <SparkleIcon size={14} color={viewMode === 'fragmovie' ? '#000' : '#f59e0b'} />
            <span>{lang === 'ru' ? '🎬 Муви-Студия & Релиз' : '🎬 Fragmovie Studio & Release'}</span>
          </button>
          <button
            className={`mode-btn ${viewMode === 'planner' ? 'active' : ''}`}
            onClick={() => setViewMode('planner')}
          >
            <FilmIcon size={14} color={viewMode === 'planner' ? '#000' : '#38bdf8'} />
            <span>{lang === 'ru' ? '📐 3D Конструктор Камер' : '📐 3D Camera Planner'}</span>
          </button>
        </div>

        {/* Quick Action Buttons */}
        <div className="cinematic-top-actions">
          <a
            href="/renders/ACE_FINAL_V3_AUDIO_KILLFEED/ACE_FINAL_V3.fcpxml"
            download="ACE_FINAL_V3.fcpxml"
            className="btn-quick-fcpxml"
            title={lang === 'ru' ? 'Скачать XML для DaVinci Resolve' : 'Download DaVinci Resolve FCPXML'}
          >
            📥 FCPXML
          </a>
          <button
            className="btn-quick-folder"
            onClick={() => api.openOutputFolder()}
            title={lang === 'ru' ? 'Открыть папку готовых рендеров' : 'Open Render Directory'}
          >
            <FolderIcon size={14} color="#e2e8f0" />
          </button>
        </div>
      </header>

      {/* Messages */}
      {errorMsg && <div className="cinematic-alert error">{errorMsg}</div>}
      {successMsg && <div className="cinematic-alert success">{successMsg}</div>}

      {/* VIEW MODE 1: FRAGMOVIE MASTER STUDIO */}
      {viewMode === 'fragmovie' && (
        <div className="fragmovie-studio-layout">
          {/* LEFT COLUMN: LIVE MASTER VIDEO PLAYER & TIMELINE SCRUBBER */}
          <div className="fragmovie-player-column">
            <div className="player-card">
              {/* Player Header with Format Selector */}
              <div className="player-card-header">
                <div className="format-toggle-group">
                  <button
                    className={`format-btn ${selectedReleaseId === 'master_16x9' ? 'active' : ''}`}
                    onClick={() => setSelectedReleaseId('master_16x9')}
                  >
                    16:9 Widescreen (1080p60)
                  </button>
                  <button
                    className={`format-btn ${selectedReleaseId === 'tiktok_9x16' ? 'active' : ''}`}
                    onClick={() => setSelectedReleaseId('tiktok_9x16')}
                  >
                    9:16 TikTok Vertical
                  </button>
                  <button
                    className={`format-btn ${selectedReleaseId === 'preview_16x9' ? 'active' : ''}`}
                    onClick={() => setSelectedReleaseId('preview_16x9')}
                  >
                    Preview (8 Mbps)
                  </button>
                </div>

                <div className="clean-master-badge">
                  <span className="dot-green"></span>
                  <span>🛡️ CLEAN MASTER (0% WATERMARK)</span>
                </div>
              </div>

              {/* Video Display Container */}
              <div className={`video-stage ${selectedReleaseId === 'tiktok_9x16' ? 'vertical-stage' : 'widescreen-stage'}`}>
                <video
                  ref={videoRef}
                  src={getActiveVideoUrl()}
                  className="cinematic-video-element"
                  playsInline
                  onTimeUpdate={(e) => setCurrentTime((e.target as HTMLVideoElement).currentTime)}
                  onPlay={() => setIsPlaying(true)}
                  onPause={() => setIsPlaying(false)}
                  onClick={togglePlay}
                />
                {!isPlaying && (
                  <div className="video-play-overlay" onClick={togglePlay}>
                    <div className="play-circle">▶</div>
                  </div>
                )}
              </div>

              {/* Timeline Scrubber Bar with Exact Event Pins */}
              <div className="timeline-scrubber-box">
                <div className="scrubber-pins-container">
                  {eventPins.map((pin, i) => {
                    const pct = (pin.time / 18.5) * 100
                    return (
                      <div
                        key={i}
                        className="timeline-pin"
                        style={{ left: `${pct}%`, borderColor: pin.color }}
                        onClick={() => handleSeek(pin.time)}
                        title={`${pin.label} (${pin.time.toFixed(2)}s)`}
                      >
                        <span className="pin-icon">{pin.icon}</span>
                        <div className="pin-tooltip">
                          <strong>{pin.label}</strong>
                          <span>{pin.time.toFixed(2)}s</span>
                        </div>
                      </div>
                    )
                  })}
                </div>

                <input
                  type="range"
                  min="0"
                  max="18.5"
                  step="0.01"
                  value={currentTime}
                  onChange={(e) => handleSeek(parseFloat(e.target.value))}
                  className="timeline-slider"
                  aria-label="Timeline scrubber"
                />

                <div className="timeline-meta-bar">
                  <div className="time-display">
                    <span className="cur-time">{currentTime.toFixed(2)}s</span>
                    <span className="divider">/</span>
                    <span className="total-time">18.50s (1110 Frames @ 60 FPS)</span>
                  </div>

                  <div className="transport-controls">
                    <button className="btn-transport" onClick={togglePlay}>
                      {isPlaying ? '⏸ PAUSE' : '▶ PLAY'}
                    </button>
                    <button
                      className="btn-transport"
                      onClick={() => {
                        if (videoRef.current) {
                          videoRef.current.muted = !videoRef.current.muted
                          setIsMuted(videoRef.current.muted)
                        }
                      }}
                    >
                      {isMuted ? '🔇 MUTED' : '🔊 AUDIO'}
                    </button>
                  </div>
                </div>
              </div>

              {/* Quick Jump Buttons */}
              <div className="quick-jump-strip">
                <span className="jump-title">{lang === 'ru' ? 'Быстрый переход к событию:' : 'Quick Jump to Event:'}</span>
                <div className="jump-buttons">
                  <button className="jump-chip drop" onClick={() => handleSeek(7.71)}>
                    🎵 7.71s Beat Drop
                  </button>
                  <button className="jump-chip kill" onClick={() => handleSeek(7.83)}>
                    💀 7.83s Frag #1
                  </button>
                  <button className="jump-chip kill" onClick={() => handleSeek(10.45)}>
                    💀 10.45s Frag #2
                  </button>
                  <button className="jump-chip headshot" onClick={() => handleSeek(12.20)}>
                    🎯 12.20s Headshot
                  </button>
                  <button className="jump-chip kill" onClick={() => handleSeek(13.00)}>
                    💀 13.00s Frag #4
                  </button>
                  <button className="jump-chip ace" onClick={() => handleSeek(15.54)}>
                    🏆 15.54s 5K ACE
                  </button>
                  <button className="jump-chip banner" onClick={() => handleSeek(15.80)}>
                    👑 15.80s Domination
                  </button>
                </div>
              </div>

              {/* Footer Utilities */}
              <div className="player-foot-actions">
                <button className="btn-secondary-action" onClick={() => setShowQAModal(true)}>
                  🖼️ {lang === 'ru' ? 'Покадровый контактный лист (QA Sheet)' : 'Frame-by-Frame QA Sheet'}
                </button>
                <a
                  href={getActiveVideoUrl()}
                  download={selectedReleaseId === 'tiktok_9x16' ? 'ACE_FINAL_V3_TIKTOK.mp4' : 'ACE_FINAL_V3_MASTER.mp4'}
                  className="btn-primary-action"
                >
                  📥 {lang === 'ru' ? 'Скачать готовый MP4' : 'Download Master MP4'}
                </a>
              </div>
            </div>
          </div>

          {/* RIGHT COLUMN: SCENE INTELLIGENCE, TIMING MATRIX & HUD CONTROLS */}
          <div className="fragmovie-inspector-column">
            {/* Inspector Navigation Tabs */}
            <div className="inspector-tabs">
              <button
                className={`insp-tab ${inspectorTab === 'timing' ? 'active' : ''}`}
                onClick={() => setInspectorTab('timing')}
              >
                🎯 {lang === 'ru' ? 'Тайминги & Бит' : 'Timings & Beat'}
              </button>
              <button
                className={`insp-tab ${inspectorTab === 'hud' ? 'active' : ''}`}
                onClick={() => setInspectorTab('hud')}
              >
                🛡️ {lang === 'ru' ? 'CS2 No-HUD' : 'CS2 No-HUD'}
              </button>
              <button
                className={`insp-tab ${inspectorTab === 'dynamics' ? 'active' : ''}`}
                onClick={() => setInspectorTab('dynamics')}
              >
                ⚡ {lang === 'ru' ? 'Динамика & FX' : 'Dynamics & FX'}
              </button>
              <button
                className={`insp-tab ${inspectorTab === 'fairlight' ? 'active' : ''}`}
                onClick={() => setInspectorTab('fairlight')}
              >
                🎚️ {lang === 'ru' ? 'Fairlight Звук' : 'Fairlight Audio'}
              </button>
            </div>

            {/* TAB 1: EXACT EVENT TIMINGS & BEAT DROP MATRIX */}
            {inspectorTab === 'timing' && (
              <div className="inspector-card">
                <div className="card-head">
                  <h4>{lang === 'ru' ? 'Матрица покадровой синхронизации фрагов' : 'Frame-Accurate Kill & Beat Matrix'}</h4>
                  <span className="badge-calibrated">⚡ 0 ms LAG CALIBRATED</span>
                </div>
                <p className="card-desc">
                  {lang === 'ru'
                    ? 'Сначала регистрируется точный выстрел (Engagement) и подтверждение смерти (Fatal Hit). Бит-дроп падает на первый выстрел, а плашка киллфида появляется в кадр подтверждения фрага.'
                    : 'First weapon engagement and fatal hit ticks are registered. Beat drop locks to the initial muzzle flash, while the killfeed badge appears immediately upon lethal confirmation.'}
                </p>

                <div className="kills-table-container">
                  <table className="kills-sync-table">
                    <thead>
                      <tr>
                        <th>#</th>
                        <th>{lang === 'ru' ? 'Жертва' : 'Victim'}</th>
                        <th>{lang === 'ru' ? 'Первый выстрел' : 'First Shot'}</th>
                        <th>{lang === 'ru' ? 'Смерть (Тик)' : 'Fatal Tick'}</th>
                        <th>{lang === 'ru' ? 'Бит-дроп' : 'Beat Drop'}</th>
                        <th>{lang === 'ru' ? 'Киллфид' : 'Killfeed'}</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td><span className="kill-pill k1">1K</span></td>
                        <td><strong>Tiger07</strong></td>
                        <td><span className="shot-time">7.71s</span></td>
                        <td><span className="tick-code">120927 (7.83s)</span></td>
                        <td><span className="beat-hit">🎵 808 DROP @ 7.71s</span></td>
                        <td><span className="frame-badge">F: 470</span></td>
                      </tr>
                      <tr>
                        <td><span className="kill-pill k2">2K</span></td>
                        <td><strong>zuuuuuhhhhn</strong></td>
                        <td><span className="shot-time">10.24s</span></td>
                        <td><span className="tick-code">121263 (10.45s)</span></td>
                        <td><span className="beat-mid">142 BPM Snare</span></td>
                        <td><span className="frame-badge">F: 627</span></td>
                      </tr>
                      <tr>
                        <td><span className="kill-pill k3">3K</span></td>
                        <td><strong>ProfyfGames</strong> <span className="hs-skull">🎯</span></td>
                        <td><span className="shot-time">12.07s</span></td>
                        <td><span className="tick-code">121491 (12.20s)</span></td>
                        <td><span className="beat-hs">Sub Downer + Snap</span></td>
                        <td><span className="frame-badge">F: 732</span></td>
                      </tr>
                      <tr>
                        <td><span className="kill-pill k4">4K</span></td>
                        <td><strong>freekjkeee</strong></td>
                        <td><span className="shot-time">12.80s</span></td>
                        <td><span className="tick-code">121595 (13.00s)</span></td>
                        <td><span className="beat-mid">142 BPM Kick</span></td>
                        <td><span className="frame-badge">F: 780</span></td>
                      </tr>
                      <tr>
                        <td><span className="kill-pill k5">5K</span></td>
                        <td><strong>axuenchik002</strong> <span className="ace-trophy">🏆</span></td>
                        <td><span className="shot-time">15.30s</span></td>
                        <td><span className="tick-code">121920 (15.54s)</span></td>
                        <td><span className="beat-ace">Climax Downer 45Hz</span></td>
                        <td><span className="frame-badge">F: 932</span></td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                <div className="music-sync-box">
                  <div className="music-info-row">
                    <span className="track-title">🎵 LOVELYDILLER — МАЛЫШКА РЕВНУЕТ</span>
                    <span className="track-bpm">142.0 BPM (4/4 Trap)</span>
                  </div>
                  <div className="music-bar-visual">
                    <div className="music-segment approach" style={{ width: '41.6%' }}>
                      <span>Approach & Tension Riser (0.00s – 7.71s)</span>
                    </div>
                    <div className="music-segment drop" style={{ width: '58.4%' }}>
                      <span>💥 808 BEAT DROP & ACE MULTIKILL (7.71s – 18.50s)</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 2: IN-GAME CS2 NO-HUD & DEATHNOTICES SUPPRESSION POLICY */}
            {inspectorTab === 'hud' && (
              <div className="inspector-card">
                <div className="card-head">
                  <h4>{lang === 'ru' ? 'Политика чистого CS2 No-HUD & Киллфида' : 'Clean CS2 No-HUD & Killfeed Policy'}</h4>
                  <span className="badge-verified">PRO FRAGMOVIE STANDARD</span>
                </div>
                <p className="card-desc">
                  {lang === 'ru'
                    ? 'При рендере кастомного киллфида дефолтный CS2 интерфейс и стандартные оповещения об убийствах полностью отключаются в игре, чтобы исключить дублирование и мыльные полосы.'
                    : 'When custom tournament overlays are used, default CS2 HUD and in-game deathnotices are completely suppressed to guarantee a clean, professional aesthetic.'}
                </p>

                <div className="policy-toggle-list">
                  <div className="policy-item active">
                    <div className="policy-checkbox checked">✓</div>
                    <div className="policy-text">
                      <strong>cl_drawhud 0 (Полное скрытие CS2 HUD)</strong>
                      <span>Отключает радар, полоски здоровья, броню, патроны и чат во время кинематографичного захвата.</span>
                    </div>
                  </div>

                  <div className="policy-item active">
                    <div className="policy-checkbox checked">✓</div>
                    <div className="policy-text">
                      <strong>cl_draw_only_deathnotices 0 (Скрытие дефолтного киллфида)</strong>
                      <span>Стандартный внутриигровой киллфид выключен, чтобы не перекрывать высокочеткий турнирный оверлей.</span>
                    </div>
                  </div>

                  <div className="policy-item active">
                    <div className="policy-checkbox checked">✓</div>
                    <div className="policy-text">
                      <strong>crosshair 0 (Чистая кинематографическая камера)</strong>
                      <span>Прицел отключается на свободных пролетах (Flyby), облётах (Orbit) и плечевой камере (Shoulder Cam).</span>
                    </div>
                  </div>

                  <div className="policy-item active">
                    <div className="policy-checkbox checked">✓</div>
                    <div className="policy-text">
                      <strong>Стековый турнирный киллфид dem.Toshka (4K Overlay)</strong>
                      <span>Плашки фрагов стекуются сверху вниз (Row 0..4) в правом верхнем углу с индикацией оружия, хэдшотов и ников.</span>
                    </div>
                  </div>

                  <div className="policy-item active">
                    <div className="policy-checkbox checked">✓</div>
                    <div className="policy-text">
                      <strong>Трофейная карточка 5K ACE — ROUND DOMINATION</strong>
                      <span>Появляется строго на 15.80 с (кадр 948) после подтверждения 5-го фрага с янтарным свечением.</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 3: SCENE DYNAMICS & CINEMATIC TRANSITIONS */}
            {inspectorTab === 'dynamics' && (
              <div className="inspector-card">
                <div className="card-head">
                  <h4>{lang === 'ru' ? 'Динамика сцены, переходы & VFX' : 'Scene Dynamics, Transitions & VFX'}</h4>
                  <span className="badge-verified">COMBAT TEMPO: RAPID FIRE</span>
                </div>
                <p className="card-desc">
                  {lang === 'ru'
                    ? 'Кинематографичный темпоритм: скоростные смены ракурсов, оптические вспышки на хэдшотах и звуковые акценты.'
                    : 'Cinematic pacing with directional whip pans, radial zoom blurs, headshot flashes and heavy climax downers.'}
                </p>

                <div className="transitions-stack">
                  <div className="trans-row">
                    <div className="trans-time">2.15s</div>
                    <div className="trans-badge whip">WHIP PAN</div>
                    <div className="trans-details">
                      <strong>Shoulder Cam ➔ Hero POV</strong>
                      <span>Хлесткий горизонтальный сдвиг с Motion Blur (затвор 240°) под струйный свист воздуха.</span>
                    </div>
                  </div>

                  <div className="trans-row">
                    <div className="trans-time">11.30s</div>
                    <div className="trans-badge zoom">RADIAL ZOOM</div>
                    <div className="trans-details">
                      <strong>Hero POV ➔ Victim Reaction (ProfyfGames)</strong>
                      <span>Центрированный зум-блюр 1.42x в точку зрения противника перед смертельным выстрелом.</span>
                    </div>
                  </div>

                  <div className="trans-row">
                    <div className="trans-time">12.18s</div>
                    <div className="trans-badge flash">HEADSHOT FLASH</div>
                    <div className="trans-details">
                      <strong>Optical Exposure Flash & Chromatic Split</strong>
                      <span>Импульс яркости (+30%) и призматическое расщепление на хэдшоте + звук щелчка карабина.</span>
                    </div>
                  </div>

                  <div className="trans-row">
                    <div className="trans-time">12.60s</div>
                    <div className="trans-badge snap">ICE SNAP</div>
                    <div className="trans-details">
                      <strong>Victim Reaction ➔ Hero POV Climax</strong>
                      <span>Мгновенный возврат в прицел героя под щелчок раскалывания льда для добивания серии.</span>
                    </div>
                  </div>

                  <div className="trans-row">
                    <div className="trans-time">15.54s</div>
                    <div className="trans-badge ace-fx">5K CLIMAX</div>
                    <div className="trans-details">
                      <strong>Ace Downer 45Hz & Orbit Glide</strong>
                      <span>Глубокий суб-басовый даунер с затуханием 2.5 с при переходе в победный 70° облёт фонтана.</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 4: FAIRLIGHT 6-TRACK STEMS & SOUND DESIGN */}
            {inspectorTab === 'fairlight' && (
              <div className="inspector-card">
                <div className="card-head">
                  <h4>{lang === 'ru' ? '6-дорожечный микс DaVinci Fairlight' : 'DaVinci Fairlight 6-Track Stems'}</h4>
                  <span className="badge-calibrated">EBU R128 / -1.0 dBTP</span>
                </div>
                <p className="card-desc">
                  {lang === 'ru'
                    ? '100% профессиональные звуки из официальной библиотеки Sonniss GDC 2026. Полный отказ от синтетических генераторов.'
                    : '100% professionally recorded 24-bit/96kHz assets from official Sonniss GDC 2026 Bundle. Zero synthetic generators.'}
                </p>

                <div className="stems-list">
                  <div className="stem-item">
                    <div className="stem-id">A1</div>
                    <div className="stem-info">
                      <strong>CS2 In-Engine Gameplay Audio</strong>
                      <span>Сегментированная нарезка по дублям. HPF 80Hz, +2.6 dB для хлесткости выстрелов.</span>
                    </div>
                    <div className="stem-meter">+2.6 dB</div>
                  </div>

                  <div className="stem-item">
                    <div className="stem-id">A2</div>
                    <div className="stem-info">
                      <strong>LOVELYDILLER — МАЛЫШКА РЕВНУЕТ (142 BPM)</strong>
                      <span>Бит-дроп заблокирован ровно на 7.71 с первого выстрела. Fade-in 0.4s, fade-out 1.5s.</span>
                    </div>
                    <div className="stem-meter">-4.5 dB</div>
                  </div>

                  <div className="stem-item">
                    <div className="stem-id">A3</div>
                    <div className="stem-info">
                      <strong>Sonniss GDC 2026 Cinematic Impacts</strong>
                      <span>Металлический слайс на Kill 1, Fast16 саб-даунер на хэдшоте, Med04 на эйсе.</span>
                    </div>
                    <div className="stem-meter">-4.0 dB</div>
                  </div>

                  <div className="stem-item">
                    <div className="stem-id">A4</div>
                    <div className="stem-info">
                      <strong>Sonniss GDC 2026 Transition Whooshes</strong>
                      <span>Стереофонические воздушные пролёты на склейках камер (2.15s, 11.30s, 12.60s, 15.70s).</span>
                    </div>
                    <div className="stem-meter">-8.0 dB</div>
                  </div>

                  <div className="stem-item">
                    <div className="stem-id">A5</div>
                    <div className="stem-info">
                      <strong>Federico Soler Tension Risers & Accents</strong>
                      <span>Экспоненциальное нарастание (5.00s – 7.71s) перед дропом + механический карабин на хэдшоте.</span>
                    </div>
                    <div className="stem-meter">-7.5 dB</div>
                  </div>

                  <div className="stem-item">
                    <div className="stem-id">A6</div>
                    <div className="stem-info">
                      <strong>Sonniss Dark Spell Drone (Атмосфера)</strong>
                      <span>Темная кинематографичная текстура под открывающим планом плечевой камеры.</span>
                    </div>
                    <div className="stem-meter">-14.0 dB</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* VIEW MODE 2: 3D CAMERA PLANNER (STEPS 1-5) */}
      {viewMode === 'planner' && (
        <div className="cinematic-planner-layout">
          {/* Steps Strip */}
          <div className="cinematic-steps-strip">
            <button
              className={`cinematic-step-pill ${currentStep === 1 ? 'active' : ''}`}
              onClick={() => setCurrentStep(1)}
            >
              <span>1</span> {lang === 'ru' ? 'Выбор демки' : 'Select Demo'}
            </button>
            <button
              className={`cinematic-step-pill ${currentStep === 2 ? 'active' : ''}`}
              onClick={() => setCurrentStep(2)}
            >
              <span>2</span> {lang === 'ru' ? 'Хайлайты' : 'Highlights'} ({selectedHighlightIds.size})
            </button>
            <button
              className={`cinematic-step-pill ${currentStep === 3 ? 'active' : ''}`}
              onClick={() => setCurrentStep(3)}
              disabled={plannedShots.length === 0}
            >
              <span>3</span> {lang === 'ru' ? 'План камер' : 'Shot Plan'} ({plannedShots.filter(s => s.enabled).length})
            </button>
            <button
              className={`cinematic-step-pill ${currentStep === 4 ? 'active' : ''}`}
              onClick={() => setCurrentStep(4)}
            >
              <span>4</span> {lang === 'ru' ? 'Захват HLAE' : 'Capture'}
            </button>
            <button
              className={`cinematic-step-pill ${currentStep === 5 ? 'active' : ''}`}
              onClick={() => setCurrentStep(5)}
              disabled={!packageSummary}
            >
              <span>5</span> {lang === 'ru' ? 'DaVinci Resolve' : 'Resolve Handoff'}
            </button>
          </div>

          <div className="cinematic-content">
            {/* STEP 1: Select Demo */}
            {currentStep === 1 && (
              <section className="cinematic-section step-demos">
                <div className="section-toolbar">
                  <div className="toolbar-info">
                    <h3>{lang === 'ru' ? 'Выберите CS2 демку для создания мувика' : 'Select a CS2 Demo for Cinematic Production'}</h3>
                    <p>{lang === 'ru' ? 'Или загрузите новую демку в Библиотеке' : 'Or import a new demo in the Library'}</p>
                  </div>
                  <button className="btn-secondary" onClick={() => onNavigateTab('library')}>
                    📁 {lang === 'ru' ? 'Библиотека демок' : 'Demo Library'}
                  </button>
                </div>
                <div className="demos-grid">
                  {demos.map((d) => (
                    <div
                      key={d.id}
                      className={`demo-card ${currentDemo?.id === d.id ? 'active' : ''}`}
                      onClick={() => {
                        onSelectDemo(d)
                        setCurrentStep(2)
                      }}
                    >
                      <div className="demo-card-head">
                        <span className="map-badge">{(d.map_name || 'UNKNOWN').toUpperCase()}</span>
                        <span className="rounds-badge">{d.rounds_count} Rounds</span>
                      </div>
                      <div className="demo-card-file">{d.file_path.split(/[\\/]/).pop()}</div>
                      <div className="demo-card-foot">
                        <span>{new Date(d.created_at).toLocaleDateString()}</span>
                        <button className="btn-select">➔</button>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* STEP 2: Highlights Selection */}
            {currentStep === 2 && (
              <section className="cinematic-section step-highlights">
                <div className="section-toolbar">
                  <div className="toolbar-info">
                    <h3>{lang === 'ru' ? 'AI Ранжирование лучших моментов' : 'AI Ranked Match Highlights'}</h3>
                    <p>{lang === 'ru' ? 'Выберите фраги и серии для многокамерной кинематографичной съёмки' : 'Select moments for multi-camera cinematic choreography'}</p>
                  </div>
                  <div className="toolbar-actions">
                    <button className="btn-secondary" onClick={selectAllHighlights}>
                      {lang === 'ru' ? 'Выбрать все' : 'Select All'}
                    </button>
                    <button className="btn-secondary" onClick={clearSelection}>
                      {lang === 'ru' ? 'Снять выбор' : 'Clear'}
                    </button>
                    <button
                      className="btn-accent-gold"
                      disabled={selectedHighlightIds.size === 0 || isLoading}
                      onClick={handleGenerateShotPlan}
                    >
                      <SparkleIcon size={16} color="#000" />
                      {lang === 'ru'
                        ? `Построить план камер (${selectedHighlightIds.size}) ➔`
                        : `Generate Shot Plan (${selectedHighlightIds.size}) ➔`}
                    </button>
                  </div>
                </div>

                {isLoading ? (
                  <div className="cinematic-loading-box">
                    <div className="spinner"></div>
                    <span>{lang === 'ru' ? 'Анализ траекторий и расчет зрелищности моментов...' : 'Analyzing player trajectories and scoring highlight intensity...'}</span>
                  </div>
                ) : highlights.length === 0 ? (
                  <div className="cinematic-empty-box">
                    <p>{lang === 'ru' ? 'В этом матче нет подтвержденных хайлайтов.' : 'No confirmed highlights found in this demo.'}</p>
                  </div>
                ) : (
                  <div className="highlights-grid">
                    {highlights.map((hl) => {
                      const isSelected = selectedHighlightIds.has(hl.id)
                      return (
                        <div
                          key={hl.id}
                          className={`highlight-card ${isSelected ? 'selected' : ''}`}
                          onClick={() => toggleHighlight(hl.id)}
                        >
                          <div className="hl-header">
                            <span className="hl-score-pill">★ {hl.score} PTS</span>
                            <span className="hl-round-pill">R{hl.round_num}</span>
                            <div className={`hl-checkbox ${isSelected ? 'checked' : ''}`}>
                              {isSelected && <CheckIcon size={14} color="#000" />}
                            </div>
                          </div>

                          <div className="hl-hero-info">
                            <span className="hero-name">{hl.pov_name || 'Hero'}</span>
                            <span className="hero-type">{hl.highlight_type.replace('_', ' ').toUpperCase()}</span>
                          </div>

                          <div className="hl-tags-row">
                            {hl.is_ace && <span className="tag-gold">ACE 5K</span>}
                            {hl.is_clutch && <span className="tag-cyan">CLUTCH</span>}
                            {hl.has_headshot && <span className="tag-red">🎯 HEADSHOT</span>}
                            {hl.has_wallbang && <span className="tag-amber">🧱 WALLBANG</span>}
                            <span className="tag-kills">{hl.kills_count} KILLS</span>
                          </div>

                          <div className="hl-timing-row">
                            <span>Tick: {hl.start_tick} - {hl.end_tick}</span>
                            <span>{((hl.end_tick - hl.start_tick) / 64.0).toFixed(1)}s</span>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )}
              </section>
            )}

            {/* STEP 3: Cinematic Shot Plan */}
            {currentStep === 3 && (
              <section className="cinematic-section step-shot-plan">
                <div className="section-toolbar">
                  <div className="toolbar-info">
                    <h3>{lang === 'ru' ? 'Режиссерский план ракурсов и траекторий камер' : 'Cinematic Camera Shot Plan'}</h3>
                    <p>{lang === 'ru' ? 'Включайте и отключайте ракурсы. Каждый дубль будет снят из реальной CS2 демки без водяных знаков.' : 'Toggle camera angles. Each take originates from authentic CS2 demo playback with clean masters.'}</p>
                  </div>
                  <div className="toolbar-actions">
                    <button className="btn-secondary" onClick={() => setCurrentStep(2)}>
                      ← {lang === 'ru' ? 'Назад к хайлайтам' : 'Back to Highlights'}
                    </button>
                    <button
                      className="btn-accent-gold"
                      disabled={plannedShots.filter(s => s.enabled).length === 0 || isLoading}
                      onClick={handleGeneratePackage}
                    >
                      <FilmIcon size={16} color="#000" />
                      {lang === 'ru'
                        ? `Собрать пакет для DaVinci (${plannedShots.filter(s => s.enabled).length}) ➔`
                        : `Create Resolve Package (${plannedShots.filter(s => s.enabled).length}) ➔`}
                    </button>
                  </div>
                </div>

                <div className="shots-list">
                  {plannedShots.map((shot, idx) => {
                    const color = getCameraBadgeColor(shot.camera_type)
                    return (
                      <div key={shot.shot_id} className={`shot-row ${shot.enabled ? 'active' : 'disabled'}`}>
                        <div className="shot-toggle" onClick={() => toggleShotEnabled(shot.shot_id)}>
                          <input
                            type="checkbox"
                            checked={shot.enabled}
                            onChange={() => {}}
                            aria-label="Toggle shot"
                          />
                        </div>

                        <div className="shot-index">#{idx + 1}</div>

                        <div className="shot-camera-badge" style={{ backgroundColor: `${color}20`, borderColor: color, color }}>
                          {shot.camera_type.replace(/_/g, ' ')}
                        </div>

                        <div className="shot-details">
                          <div className="shot-title">
                            <span className="shot-purpose">[{shot.purpose}]</span>
                            <span className="shot-filename">{shot.output_filename}</span>
                            {shot.has_campath && <span className="campath-indicator">★ 3D Spline Campath</span>}
                          </div>
                          <div className="shot-subtext">
                            <span>Round {shot.round_number}</span>
                            <span>•</span>
                            <span>Focus: {shot.focus_target_name || shot.pov_name || 'Combat Zone'}</span>
                            <span>•</span>
                            <span>FOV: {shot.fov}°</span>
                            <span>•</span>
                            <span>Ticks: {shot.start_tick} - {shot.end_tick}</span>
                          </div>
                        </div>

                        <div className="shot-timing">
                          <span className="shot-duration">{shot.duration_seconds.toFixed(2)}s</span>
                          <span className="shot-fps">{shot.fps} FPS</span>
                        </div>

                        <div className="shot-status-badge">
                          {shot.watermark ? 'WATERMARKED' : '🛡️ CLEAN MASTER'}
                        </div>
                      </div>
                    )
                  })}
                </div>
              </section>
            )}

            {/* STEP 4: Capture Engine Status */}
            {currentStep === 4 && (
              <section className="cinematic-section step-capture">
                <div className="capture-dashboard">
                  <div className="dashboard-card">
                    <h4>{lang === 'ru' ? 'HLAE Source 2 Драйвер захвата' : 'HLAE Source 2 Capture Engine'}</h4>
                    <div className="driver-status">
                      <span className="status-dot online"></span>
                      <span>AfxHookSource2.dll: v0.41.7 Ready</span>
                    </div>
                    <p>{lang === 'ru' ? 'Захват выполняется последовательно на аппаратном уровне Direct3D 11 без просадок кадров через mirv_streams.' : 'Hardware Direct3D 11 sequential capture via mirv_streams at strict host_framerate.'}</p>
                  </div>

                  <div className="dashboard-card">
                    <h4>{lang === 'ru' ? 'Гарантия чистых мастеров' : 'Clean Master Guarantee'}</h4>
                    <div className="brand-policy">
                      <span className="policy-badge">brand_overlay.enabled = false</span>
                    </div>
                    <p>{lang === 'ru' ? 'Водяной знак dem.Toshka отключен по умолчанию для всех кинематографичных экспортов.' : 'Watermark is strictly excluded from cinematic master video renders.'}</p>
                  </div>
                </div>

                <div className="capture-action-banner">
                  <p>{lang === 'ru' ? 'Готовы к записи всех запланированных ракурсов за один непрерывный сеанс CS2.' : 'Ready to capture all planned camera takes in sequential order.'}</p>
                  <button className="btn-accent-gold" onClick={() => setCurrentStep(5)}>
                    {lang === 'ru' ? 'Перейти к пакету DaVinci Resolve ➔' : 'Proceed to DaVinci Resolve Package ➔'}
                  </button>
                </div>
              </section>
            )}

            {/* STEP 5: DaVinci Resolve Handoff */}
            {currentStep === 5 && packageSummary && (
              <section className="cinematic-section step-resolve">
                <div className="resolve-hero-card">
                  <div className="resolve-badge-row">
                    <span className="badge-resolve">DAVINCI RESOLVE PRODUCTION PACKAGE</span>
                    <span className="badge-package-id">{packageSummary.package_id}</span>
                  </div>

                  <h2>{packageSummary.project_name}</h2>
                  <p className="package-path">{packageSummary.output_directory}</p>

                  <div className="resolve-quick-actions">
                    <a
                      href={api.getPackageFcpxmlUrl(packageSummary.package_id)}
                      download="DaVinci_Resolve_Project.fcpxml"
                      className="btn-download-fcpxml"
                    >
                      📥 {lang === 'ru' ? 'Скачать DaVinci Resolve FCPXML (1-Click Import)' : 'Download DaVinci Resolve FCPXML'}
                    </a>
                    <button
                      className="btn-secondary"
                      onClick={() => alert(`Manifests saved at: ${packageSummary.output_directory}`)}
                    >
                      📁 {lang === 'ru' ? 'Открыть папку проекта' : 'Open Project Folder'}
                    </button>
                  </div>
                </div>
              </section>
            )}
          </div>
        </div>
      )}

      {/* QA Sheet Modal Preview */}
      {showQAModal && (
        <div className="qa-modal-overlay" onClick={() => setShowQAModal(false)}>
          <div className="qa-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="qa-modal-header">
              <h3>{lang === 'ru' ? 'Покадровый сравнительный лист синхронизации (QA Contact Sheet)' : 'Frame-by-Frame Synchronization QA Sheet'}</h3>
              <button className="btn-close-modal" onClick={() => setShowQAModal(false)}>✕</button>
            </div>
            <div className="qa-modal-body">
              <img
                src="/renders/ACE_FINAL_V3_AUDIO_KILLFEED/qa/qa_kill_sync_contact_sheet.png"
                alt="Kill Synchronization QA Sheet"
                className="qa-sheet-img"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
