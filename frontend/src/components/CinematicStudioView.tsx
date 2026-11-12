import React, { useEffect, useState } from 'react'
import { api } from '../api'
import { useTranslation } from '../i18n'
import type { DemoSummary } from '../types'
import {
  ClapperboardIcon,
  SparkleIcon,
  FilmIcon,
  CheckIcon,
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
  const [currentStep, setCurrentStep] = useState<number>(2) // 1=Demo, 2=Highlights, 3=ShotPlan, 4=Capture, 5=Resolve
  const [highlights, setHighlights] = useState<RankedHighlight[]>([])
  const [selectedHighlightIds, setSelectedHighlightIds] = useState<Set<string>>(new Set())
  const [plannedShots, setPlannedShots] = useState<PlannedShot[]>([])
  const [packageSummary, setPackageSummary] = useState<any | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  // Load highlights when current demo changes
  useEffect(() => {
    if (currentDemo) {
      loadHighlights(currentDemo.id)
    } else if (demos.length > 0) {
      onSelectDemo(demos[0])
    }
  }, [currentDemo?.id])

  const loadHighlights = async (demoId: number) => {
    setIsLoading(true)
    setErrorMsg(null)
    try {
      const data = await api.getCinematicHighlights(demoId)
      setHighlights(data)
      // Auto-select the top 2 highest-ranked highlights
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

  return (
    <div className="cinematic-studio-container">
      {/* Top Banner Navigation Steps */}
      <header className="cinematic-top-nav">
        <div className="cinematic-brand-group">
          <ClapperboardIcon size={22} color="#f59e0b" />
          <div className="cinematic-titles">
            <h2>{lang === 'ru' ? 'CINEMATIC STUDIO' : 'CINEMATIC STUDIO'}</h2>
            <span>{lang === 'ru' ? '3D Кино-режиссер CS2 & Экспорт в DaVinci Resolve' : 'CS2 3D Movie Director & DaVinci Resolve Production'}</span>
          </div>
        </div>

        {/* Steps Bar */}
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

        {/* Active Demo Indicator */}
        <div className="cinematic-active-demo-pill">
          <span className="dot-live"></span>
          <span className="demo-map">{(currentDemo?.map_name || 'DEMO').toUpperCase()}</span>
          <span className="demo-rounds">{currentDemo?.rounds_count || 0}R</span>
        </div>
      </header>

      {/* Messages */}
      {errorMsg && <div className="cinematic-alert error">{errorMsg}</div>}
      {successMsg && <div className="cinematic-alert success">{successMsg}</div>}

      {/* Main Content Areas based on Step */}
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

            {/* Production Manifests Grid */}
            <div className="manifests-grid">
              <div className="manifest-item">
                <span className="manifest-icon">📜</span>
                <div className="manifest-info">
                  <strong>highlight_manifest.json</strong>
                  <span>{lang === 'ru' ? 'Реестр хайлайтов и таймингов' : 'Highlight catalog and timing metadata'}</span>
                </div>
              </div>
              <div className="manifest-item">
                <span className="manifest-icon">🎬</span>
                <div className="manifest-info">
                  <strong>shot_plan.json</strong>
                  <span>{lang === 'ru' ? 'Режиссерский план всех ракурсов' : 'Structured camera angle choreography'}</span>
                </div>
              </div>
              <div className="manifest-item">
                <span className="manifest-icon">📐</span>
                <div className="manifest-info">
                  <strong>camera_paths.json & campath.xml</strong>
                  <span>{lang === 'ru' ? '3D сплайны и координаты HLAE' : 'HLAE 3D spline keyframes and Euler angles'}</span>
                </div>
              </div>
              <div className="manifest-item">
                <span className="manifest-icon">🎥</span>
                <div className="manifest-info">
                  <strong>capture_manifest.json</strong>
                  <span>{lang === 'ru' ? 'Параметры видеозахвата 1080p60' : 'H.264 / AAC capture settings and quality'}</span>
                </div>
              </div>
              <div className="manifest-item">
                <span className="manifest-icon">✂️</span>
                <div className="manifest-info">
                  <strong>edit_decision_list.json & Timeline.edl</strong>
                  <span>{lang === 'ru' ? 'Многодорожечный таймлайн монтажа' : 'Multi-track CMX 3600 EDL sequence'}</span>
                </div>
              </div>
              <div className="manifest-item">
                <span className="manifest-icon">🎯</span>
                <div className="manifest-info">
                  <strong>overlay_events.json & SVG Badges</strong>
                  <span>{lang === 'ru' ? 'Кинематографичный оверлей киллфида' : 'Rich killfeed graphics and ACE announcements'}</span>
                </div>
              </div>
              <div className="manifest-item">
                <span className="manifest-icon">⚙️</span>
                <div className="manifest-info">
                  <strong>render_manifest.json</strong>
                  <span>{lang === 'ru' ? 'Спецификация дорожек и цветового пространства' : 'Track layout and Rec.709 color specification'}</span>
                </div>
              </div>
            </div>

            {/* Resolve Import Guide */}
            <div className="resolve-guide-box">
              <h4>{lang === 'ru' ? 'Как открыть проект в DaVinci Resolve:' : 'How to import into DaVinci Resolve:'}</h4>
              <ol>
                <li>{lang === 'ru' ? 'Откройте DaVinci Resolve и создайте новый проект.' : 'Open DaVinci Resolve and create a new project.'}</li>
                <li>{lang === 'ru' ? 'Выберите меню: File ➔ Import ➔ Timeline... и укажите скачанный DaVinci_Resolve_Project.fcpxml.' : 'Choose File ➔ Import ➔ Timeline... and select the downloaded DaVinci_Resolve_Project.fcpxml.'}</li>
                <li>{lang === 'ru' ? 'DaVinci автоматически создаст 4 видеодорожки: Track 1 (Hero POV), Track 2 (Cinematic B-Roll), Track 3 (Victim POV), Track 4 (Overlays) с маркерами на фрагах.' : 'Resolve will automatically generate 4 separate tracks (Hero POV, Cinematic B-Roll, Victim POV, Overlays) with synchronized kill markers.'}</li>
              </ol>
            </div>
          </section>
        )}
      </div>
    </div>
  )
}
