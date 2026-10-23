import React, { useState, useMemo, useRef, useEffect, useCallback } from 'react'
import type { ClipSettings, DemoSummary, HighlightItem, KillDTO, MontageDTO, PlayerDTO, RoundDTO, RoundReplayData } from '../types'
import { Map2DRadar } from './Map2DRadar'
import { TacticalReplayRadar } from './TacticalReplayRadar'
import { api } from '../api'
import { VideoPlayerModal } from './VideoPlayerModal'
import { TournamentHudModal } from './TournamentHudModal'
import { PlayerAnalyticsModal } from './PlayerAnalyticsModal'
import { InteractiveCrosshairPreview } from './InteractiveCrosshairPreview'
import {
  FolderIcon,
  VolumeIcon,
  VolumeMuteIcon,
  FilmIcon,
  CrosshairIcon,
  ActivityIcon,
  PlayIcon,
  PauseIcon,
  LoaderIcon,
  WarningIcon,
  ZapIcon,
  CheckIcon,
  TrophyIcon,
  SkullIcon,
  SparkleIcon,
  SlidersIcon,
  RadarIcon,
  CameraIcon,
  EyeIcon,
} from './Icons'
import { useTranslation } from '../i18n'



interface HighlightsStudioViewProps {
  highlights: HighlightItem[]
  players: PlayerDTO[]
  selectedIds: Set<string>
  onToggleHighlight: (id: string) => void
  onSelectAllFiltered: (ids: string[]) => void
  onClearFiltered: (ids: string[]) => void
  activePlayerFilter: string | null
  onSetPlayerFilter: (steamId: string | null) => void
  activeTypeFilter: string | null
  onSetTypeFilter: (type: string | null) => void
  activeRoundFilter: number | null
  onSetRoundFilter: (round: number | null) => void
  tickrate: number
  onRenderSingle?: (id: string) => void
  onOpenQueue?: () => void

  // Scope.gg 4-step wizard integration
  demos?: DemoSummary[]
  activeDemo?: DemoSummary | null
  onSelectDemo?: (demo: DemoSummary) => void
  clipSettings?: ClipSettings
  onUpdateSettings?: (settings: ClipSettings) => void
  onSubmitRender?: (highlightIds: string[]) => Promise<any>
  kills?: KillDTO[]
  demoRounds?: RoundDTO[]
  onUploadDemo?: (file: File) => Promise<void>
  onParsePath?: (path: string) => Promise<void>
}

export const HighlightsStudioView: React.FC<HighlightsStudioViewProps> = ({
  highlights,
  players,
  selectedIds,
  onToggleHighlight,
  onSelectAllFiltered,
  onClearFiltered,
  activePlayerFilter,
  onSetPlayerFilter,
  activeTypeFilter,
  onSetTypeFilter,
  activeRoundFilter,
  onSetRoundFilter,
  tickrate,
  onRenderSingle: _onRenderSingle,
  onOpenQueue,
  demos = [],
  activeDemo = null,
  onSelectDemo,
  clipSettings,
  onUpdateSettings,
  onSubmitRender,
  kills = [],
  demoRounds = [],
  onUploadDemo,
  onParsePath: _onParsePath,
}) => {
  const { t } = useTranslation()
  // 4-step wizard: 1 = Choose match, 2 = Choose player, 3 = Choose moments (2D Map), 4 = Compile montage
  const [currentStep, setCurrentStep] = useState<1 | 2 | 3 | 4>(activeDemo ? 2 : 1)
  const [hoveredHighlightId, setHoveredHighlightId] = useState<string | null>(null)
  const [weaponFilter, setWeaponFilter] = useState<string | null>(null)
  const [aspectRatio, setAspectRatio] = useState<'16:9' | '4:3'>('16:9')

  // Drag & drop demo state
  const [isDraggingFile, setIsDraggingFile] = useState(false)
  const [isIngestingDemo, setIsIngestingDemo] = useState(false)
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  // Step 3: 2D Tactical Replay Player State
  const [radarTab, setRadarTab] = useState<'markers' | 'replay'>('markers')
  const [replayRoundNum, setReplayRoundNum] = useState<number>(demoRounds[0]?.round_num || 1)
  const [replayData, setReplayData] = useState<RoundReplayData | null>(null)
  const [isReplayLoading, setIsReplayLoading] = useState<boolean>(false)
  const [replayError, setReplayError] = useState<string | null>(null)
  const [replayFrameIndex, setReplayFrameIndex] = useState<number>(0)
  const [isReplayPlaying, setIsReplayPlaying] = useState<boolean>(false)
  const [replaySpeed, setReplaySpeed] = useState<number>(1)
  const [replayShowTrails, setReplayShowTrails] = useState<boolean>(true)
  const [replayShowShots, setReplayShowShots] = useState<boolean>(true)
  const [replayShowGrenades, setReplayShowGrenades] = useState<boolean>(true)
  const [replayLevel, setReplayLevel] = useState<'upper' | 'lower'>('upper')
  const replayTimerRef = useRef<number | null>(null)

  // Synchronize replay round if rounds list changes
  useEffect(() => {
    if (demoRounds.length > 0 && !demoRounds.some((r) => r.round_num === replayRoundNum)) {
      setReplayRoundNum(demoRounds[0].round_num)
    }
  }, [demoRounds, replayRoundNum])

  // Fetch round replay data when round or demo changes in replay mode
  useEffect(() => {
    if (!activeDemo || radarTab !== 'replay') return
    setIsReplayLoading(true)
    setReplayError(null)
    setIsReplayPlaying(false)
    setReplayFrameIndex(0)

    api
      .getRoundReplay(activeDemo.id, replayRoundNum, 32)
      .then((data) => {
        setReplayData(data)
        setIsReplayLoading(false)
      })
      .catch((err) => {
        console.error('Failed to load round replay:', err)
        setReplayError(err?.message || 'Не удалось загрузить данные тактического повтора раунда')
        setIsReplayLoading(false)
      })
  }, [activeDemo, replayRoundNum, radarTab])

  // Playback loop for 2D round replay
  useEffect(() => {
    if (!isReplayPlaying || !replayData || replayData.frames.length === 0) {
      if (replayTimerRef.current) clearInterval(replayTimerRef.current)
      return
    }

    const intervalMs = Math.max(30, Math.floor(125 / replaySpeed))
    replayTimerRef.current = window.setInterval(() => {
      setReplayFrameIndex((prev) => {
        if (prev >= replayData.frames.length - 1) {
          setIsReplayPlaying(false)
          return prev
        }
        return prev + 1
      })
    }, intervalMs)

    return () => {
      if (replayTimerRef.current) clearInterval(replayTimerRef.current)
    }
  }, [isReplayPlaying, replayData, replaySpeed])

  const currentReplayFrame = useMemo(() => {
    if (!replayData || replayData.frames.length === 0) return null
    return replayData.frames[Math.min(replayFrameIndex, replayData.frames.length - 1)]
  }, [replayData, replayFrameIndex])


  const playerReplayTrails = useMemo(() => {
    if (!replayData || !replayData.frames || replayData.frames.length === 0) return {}
    const trails: Record<string, Array<{ x: number; y: number; is_alive: boolean }>> = {}
    const maxIdx = Math.min(replayFrameIndex, replayData.frames.length - 1)
    for (let i = 0; i <= maxIdx; i++) {
      const f = replayData.frames[i]
      for (const p of f.players) {
        if (!trails[p.steam_id]) trails[p.steam_id] = []
        trails[p.steam_id].push({ x: p.x, y: p.y, is_alive: p.is_alive })
      }
    }
    return trails
  }, [replayData, replayFrameIndex])

  const replayRadarImageUrl = useMemo(() => {
    if (!replayData) return ''
    if (replayLevel === 'lower' && replayData.radar_file_lower) {
      return `/maps/${replayData.radar_file_lower}`
    }
    return `/maps/${replayData.radar_file || (activeDemo?.map_name ? `${activeDemo.map_name}.png` : 'de_nuke.png')}`
  }, [replayData, replayLevel, activeDemo])

  const formatReplayTime = (tick: number, startTick: number, rTickrate: number) => {
    const elapsedSec = Math.max(0, Math.floor((tick - startTick) / (rTickrate || 128)))
    const mins = Math.floor(elapsedSec / 60)
    const secs = elapsedSec % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const handleJumpToReplayTick = (targetTick: number) => {
    if (!replayData || replayData.frames.length === 0) return
    let bestIdx = 0
    let bestDist = Infinity
    replayData.frames.forEach((f, i) => {
      const dist = Math.abs(f.tick - targetTick)
      if (dist < bestDist) {
        bestDist = dist
        bestIdx = i
      }
    })
    setReplayFrameIndex(bestIdx)
    setIsReplayPlaying(false)
  }

  const handlePrevRound = () => {
    if (demoRounds.length === 0) return
    const curIdx = demoRounds.findIndex((r) => r.round_num === replayRoundNum)
    if (curIdx > 0) {
      setReplayRoundNum(demoRounds[curIdx - 1].round_num)
    }
  }

  const handleNextRound = () => {
    if (demoRounds.length === 0) return
    const curIdx = demoRounds.findIndex((r) => r.round_num === replayRoundNum)
    if (curIdx >= 0 && curIdx < demoRounds.length - 1) {
      setReplayRoundNum(demoRounds[curIdx + 1].round_num)
    }
  }

  // Step 3 Montage creation state
  const defaultMontageTitle = activeDemo
    ? `${(activeDemo.map_name || 'Match').replace('de_', '').toUpperCase()} ${new Date(activeDemo.created_at).toLocaleDateString()} Highlights`
    : 'CS2 Highlight Montage'
  const [montageTitle, setMontageTitle] = useState(defaultMontageTitle)
  const [isCompiling, setIsCompiling] = useState(false)
  const [compilationStatus, setCompilationStatus] = useState<string | null>(null)
  const [compilationProgress, setCompilationProgress] = useState<number>(0)
  const [compilationError, setCompilationError] = useState<string | null>(null)
  const [compiledMontage, setCompiledMontage] = useState<MontageDTO | null>(null)
  const [activeModalVideo, setActiveModalVideo] = useState<{
    url: string
    title: string
    subtitle?: string
  } | null>(null)
  const [isTournamentHudModalOpen, setIsTournamentHudModalOpen] = useState(false)
  const [selectedPlayerForAnalytics, setSelectedPlayerForAnalytics] = useState<{
    steamIdOrName: string
    name: string
    team?: string | null
  } | null>(null)

  const [mySteamId, setMySteamId] = useState<string | null>(() => {
    return localStorage.getItem('my_steam_id')
  })

  useEffect(() => {
    const handleStorageChange = () => {
      setMySteamId(localStorage.getItem('my_steam_id'))
    }
    window.addEventListener('my_steam_id_changed', handleStorageChange)
    window.addEventListener('storage', handleStorageChange)
    return () => {
      window.removeEventListener('my_steam_id_changed', handleStorageChange)
      window.removeEventListener('storage', handleStorageChange)
    }
  }, [])

  const [inspectedPlayerSteamId, setInspectedPlayerSteamId] = useState<string | null>(null)

  const inspectedPlayer = useMemo(() => {
    if (inspectedPlayerSteamId) {
      return players.find((p) => p.steam_id === inspectedPlayerSteamId) || null
    }
    if (activePlayerFilter) {
      return players.find((p) => p.steam_id === activePlayerFilter) || null
    }
    return players[0] || null
  }, [inspectedPlayerSteamId, activePlayerFilter, players])

  // Map round numbers for filter
  const roundNumbers = useMemo(() => {
    const set = new Set<number>()
    highlights.forEach((h) => set.add(h.round_num))
    return Array.from(set).sort((a, b) => a - b)
  }, [highlights])


  // Correlate kills for each highlight
  const getHighlightKillDetails = useCallback((h: HighlightItem) => {
    if (!kills || kills.length === 0) return null
    const matched = kills.filter(
      (k) => k.round_num === h.round_num && k.tick >= h.kill_start_tick && k.tick <= h.kill_end_tick + 128
    )
    return matched.length > 0 ? matched[0] : null
  }, [kills])

  // Filtered highlights
  const filteredHighlights = useMemo(() => {
    return highlights.filter((h) => {
      if (activePlayerFilter && h.pov_steam_id !== activePlayerFilter) return false
      if (activeTypeFilter && h.highlight_type !== activeTypeFilter) return false
      if (activeRoundFilter !== null && h.round_num !== activeRoundFilter) return false
      if (weaponFilter) {
        const kill = getHighlightKillDetails(h)
        if (!kill || !kill.weapon || !kill.weapon.toLowerCase().includes(weaponFilter.toLowerCase())) {
          return false
        }
      }
      return true
    })
  }, [highlights, activePlayerFilter, activeTypeFilter, activeRoundFilter, weaponFilter, getHighlightKillDetails])

  const filteredIds = useMemo(() => filteredHighlights.map((h) => h.id), [filteredHighlights])
  const allFilteredSelected = filteredIds.length > 0 && filteredIds.every((id) => selectedIds.has(id))
  const selectedHighlights = highlights.filter((h) => selectedIds.has(h.id))

  const formatRoundTime = (killTick: number) => {
    // Standard round is ~115s (1:55) after freeze time
    const tr = tickrate || 128
    const approxSec = Math.max(0, Math.floor((killTick % (tr * 115)) / tr))
    const mins = Math.floor(approxSec / 60)
    const secs = approxSec % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const cleanWeaponName = (w?: string | null) => {
    if (!w) return 'rifle'
    return w.replace('weapon_', '').replace('_silencer', '-S').toUpperCase()
  }

  const handleStartMontageCreation = async () => {
    if (!activeDemo || selectedIds.size === 0 || !onSubmitRender) return
    setIsCompiling(true)
    setCompilationError(null)
    setCompilationStatus('Добавление клипов в очередь...')
    setCompilationProgress(5)

    try {
      const highlightIds = Array.from(selectedIds)
      const submitted = await onSubmitRender(highlightIds)
      const targetJobIds = submitted && Array.isArray(submitted) ? submitted.map((j: any) => j.id) : []

      setCompilationStatus(`Рендеринг клипов через CS2/HLAE (0/${highlightIds.length})...`)

      const pollStart = Date.now()
      const maxWaitMs = 15 * 60 * 1000 // 15 mins

      while (Date.now() - pollStart < maxWaitMs) {
        await new Promise((r) => setTimeout(r, 2500))
        const currentJobs = await api.listRenderJobs(activeDemo.id)

        const relevantJobs = currentJobs.filter(
          (j) =>
            (targetJobIds.length > 0 && targetJobIds.includes(j.id)) ||
            (j.highlight_id && highlightIds.includes(j.highlight_id))
        )

        const completedJobs = relevantJobs.filter((j) => j.status === 'completed')
        const failedJobs = relevantJobs.filter((j) => j.status === 'failed')
        const total = relevantJobs.length || highlightIds.length

        const pct = Math.min(90, Math.round((completedJobs.length / total) * 80) + 10)
        setCompilationProgress(pct)
        setCompilationStatus(`Рендеринг: готово ${completedJobs.length} из ${total} клипов...`)

        if (completedJobs.length === total && total > 0) {
          setCompilationStatus('Склейка клипов в единый ролик MP4...')
          setCompilationProgress(95)
          const validJobIds = completedJobs.map((j) => j.id)
          const montage = await api.createMontage({
            demo_id: activeDemo.id,
            job_ids: validJobIds,
            output_filename: montageTitle.trim().replace(/\s+/g, '_') + '.mp4',
          })
          setCompiledMontage(montage)
          setCompilationProgress(100)
          setCompilationStatus(null)
          break
        }

        if (failedJobs.length > 0 && completedJobs.length + failedJobs.length === total) {
          if (completedJobs.length > 0) {
            setCompilationStatus('Склейка готовых клипов...')
            const validJobIds = completedJobs.map((j) => j.id)
            const montage = await api.createMontage({
              demo_id: activeDemo.id,
              job_ids: validJobIds,
              output_filename: montageTitle.trim().replace(/\s+/g, '_') + '.mp4',
            })
            setCompiledMontage(montage)
            setCompilationError(
              `Часть клипов (${failedJobs.length}) завершилась с ошибкой, но видео создано из ${completedJobs.length} готовых клипов.`
            )
          } else {
            throw new Error(failedJobs[0].error_summary || 'Рендер клипов в очереди завершился ошибкой в HLAE')
          }
          break
        }
      }
    } catch (err: any) {
      console.warn('Montage direct compilation wait note:', err)
      setCompilationError(
        err?.message || 'Рендер запущен в очереди. Вы можете отслеживать прогресс во вкладке Очередь / Монтаж.'
      )
    } finally {
      setIsCompiling(false)
    }
  }

  return (
    <div style={{ maxWidth: '1440px', margin: '0 auto', padding: '12px 18px' }}>
      {/* Compact Studio Header Control Bar */}
      <div className="studio-top-bar">
        {/* Left: Compact Horizontal Stepper */}
        <div className="studio-compact-stepper">
          <div
            className={`compact-step-pill ${currentStep === 1 ? 'active' : currentStep > 1 ? 'done' : ''}`}
            onClick={() => setCurrentStep(1)}
            title="Шаг 1: Выбор демки CS2"
          >
            <span className="step-num">1</span>
            <span>{t('studio.step1').replace(/^\d+\.\s*/, '')}</span>
          </div>
          <span className="step-sep">➔</span>
          <div
            className={`compact-step-pill ${currentStep === 2 ? 'active' : currentStep > 2 ? 'done' : ''}`}
            onClick={() => activeDemo && setCurrentStep(2)}
            style={{ opacity: activeDemo ? 1 : 0.4, cursor: activeDemo ? 'pointer' : 'default' }}
            title="Шаг 2: Выбор игрока"
          >
            <span className="step-num">2</span>
            <span>{t('studio.step2').replace(/^\d+\.\s*/, '')}</span>
          </div>
          <span className="step-sep">➔</span>
          <div
            className={`compact-step-pill ${currentStep === 3 ? 'active' : currentStep > 3 ? 'done' : ''}`}
            onClick={() => activeDemo && setCurrentStep(3)}
            style={{ opacity: activeDemo ? 1 : 0.4, cursor: activeDemo ? 'pointer' : 'default' }}
            title="Шаг 3: Моменты и 2D Радар"
          >
            <span className="step-num">3</span>
            <span>{t('studio.step3').replace(/^\d+\.\s*/, '')}</span>
            {selectedIds.size > 0 && <span className="step-count-badge">{selectedIds.size}</span>}
          </div>
          <span className="step-sep">➔</span>
          <div
            className={`compact-step-pill ${currentStep === 4 ? 'active' : ''}`}
            onClick={() => activeDemo && selectedIds.size > 0 && setCurrentStep(4)}
            style={{ opacity: activeDemo && selectedIds.size > 0 ? 1 : 0.4, cursor: activeDemo && selectedIds.size > 0 ? 'pointer' : 'default' }}
            title="Шаг 4: Сборка и Настройки"
          >
            <span className="step-num">4</span>
            <span>{t('studio.step4').replace(/^\d+\.\s*/, '')}</span>
          </div>
        </div>

        {/* Right: Contextual Step Action Buttons */}
        <div className="studio-top-actions">
          {currentStep === 2 && (
            <>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setCurrentStep(1)}
                style={{ padding: '6px 12px', fontSize: '12px', fontWeight: 600 }}
              >
                ← Сменить матч
              </button>
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => {
                  onSetPlayerFilter(null)
                  setCurrentStep(3)
                }}
                style={{ padding: '6px 14px', fontSize: '12px', fontWeight: 700 }}
              >
                Все игроки матча →
              </button>
            </>
          )}

          {currentStep === 3 && (
            <>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setCurrentStep(2)}
                style={{ padding: '6px 12px', fontSize: '12px', fontWeight: 600 }}
              >
                ← К игрокам
              </button>
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => setCurrentStep(4)}
                disabled={selectedIds.size === 0}
                style={{ padding: '6px 16px', fontSize: '12px', fontWeight: 700 }}
              >
                Далее: Настройки ({selectedIds.size}) ➔
              </button>
            </>
          )}

          {currentStep === 4 && (
            <>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setCurrentStep(3)}
                style={{ padding: '6px 12px', fontSize: '12px', fontWeight: 600 }}
              >
                ← К моментам
              </button>
              <button
                type="button"
                className="btn btn-accent card-interactive"
                onClick={handleStartMontageCreation}
                disabled={isCompiling || selectedIds.size === 0}
                style={{ padding: '6px 18px', fontSize: '12px', fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: '6px' }}
              >
                {isCompiling ? (
                  <>
                    <LoaderIcon size={13} color="#090d16" />
                    <span>Сборка...</span>
                  </>
                ) : (
                  <>
                    <FilmIcon size={13} color="#090d16" />
                    <span>Создать нарезку ({selectedIds.size})</span>
                  </>
                )}
              </button>
            </>
          )}

          {onOpenQueue && (
            <button
              type="button"
              className="btn btn-secondary card-interactive"
              onClick={onOpenQueue}
              style={{ padding: '6px 12px', fontSize: '12px', display: 'inline-flex', alignItems: 'center', gap: '6px' }}
            >
              <FilmIcon size={12} color="#94a3b8" />
              <span>Очередь</span>
            </button>
          )}
        </div>
      </div>

      {/* ==================================================================== */}
      {/* STEP 1: CHOOSE MATCH                                                 */}
      {/* ==================================================================== */}
      {currentStep === 1 && (
        <div key="step-1" className="step-transition" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Compact Drag & Drop Upload Zone */}
          <div
            onDragOver={(e) => {
              e.preventDefault()
              setIsDraggingFile(true)
            }}
            onDragLeave={() => setIsDraggingFile(false)}
            onDrop={async (e) => {
              e.preventDefault()
              setIsDraggingFile(false)
              if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                const file = e.dataTransfer.files[0]
                if (file.name.toLowerCase().endsWith('.dem') && onUploadDemo) {
                  setIsIngestingDemo(true)
                  try {
                    await onUploadDemo(file)
                    setCurrentStep(2)
                  } finally {
                    setIsIngestingDemo(false)
                  }
                }
              }
            }}
            onClick={() => fileInputRef.current?.click()}
            style={{
              border: isDraggingFile ? '2px dashed #38bdf8' : '1px dashed #334155',
              backgroundColor: isDraggingFile ? 'rgba(56, 189, 248, 0.08)' : '#12151e',
              borderRadius: '10px',
              padding: '12px 18px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".dem"
              style={{ display: 'none' }}
              onChange={async (e) => {
                if (e.target.files && e.target.files.length > 0) {
                  const file = e.target.files[0]
                  if (file.name.toLowerCase().endsWith('.dem') && onUploadDemo) {
                    setIsIngestingDemo(true)
                    try {
                      await onUploadDemo(file)
                      setCurrentStep(2)
                    } finally {
                      setIsIngestingDemo(false)
                    }
                  }
                }
              }}
            />
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
              <FolderIcon size={24} color="#38bdf8" />
              <div>
                <div style={{ fontSize: '13.5px', fontWeight: 700, color: '#f1f5f9', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {isIngestingDemo ? (
                    <>
                      <LoaderIcon size={14} color="#38bdf8" />
                      <span>Загрузка и парсинг CS2 демки...</span>
                    </>
                  ) : (
                    'Перетащите .dem файл сюда или нажмите для выбора'
                  )}
                </div>
                <div style={{ fontSize: '11px', color: '#94a3b8' }}>
                  Поддерживаются официальные демки CS2 (Matchmaking, Premier, Faceit, HLTV)
                </div>
              </div>
            </div>
            <button
              type="button"
              className="btn btn-secondary"
              style={{ padding: '6px 14px', fontSize: '12px', pointerEvents: 'none' }}
            >
              Выбрать файл .dem
            </button>
          </div>

          {/* Matches Table Card */}
          <div
            style={{
              backgroundColor: '#16181f',
              border: '1px solid #232630',
              borderRadius: '12px',
              overflow: 'hidden',
            }}
          >
            <div style={{ padding: '16px 20px', borderBottom: '1px solid #232630', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ fontWeight: 700, fontSize: '14px', color: '#f1f5f9' }}>
                Доступные матчи ({demos.length})
              </div>
              <div style={{ fontSize: '12px', color: '#94a3b8' }}>
                Выберите матч для поиска лучших моментов
              </div>
            </div>

          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
            <thead>
              <tr style={{ color: '#64748b', borderBottom: '1px solid #232630', fontSize: '11px', textTransform: 'uppercase' }}>
                <th style={{ padding: '12px 20px' }}>Карта</th>
                <th style={{ padding: '12px 16px' }}>Дата</th>
                <th style={{ padding: '12px 16px' }}>Счёт</th>
                <th style={{ padding: '12px 16px' }}>Источник</th>
                <th style={{ padding: '12px 16px' }}>Хайлайты</th>
                <th style={{ padding: '12px 20px', textAlign: 'right' }}>Действие</th>
              </tr>
            </thead>
            <tbody>
              {demos.map((d) => {
                const isSelected = activeDemo?.id === d.id
                const cleanMap = (d.map_name || 'Nuke').replace('de_', '').toUpperCase()
                return (
                  <tr
                    key={d.id}
                    onClick={() => {
                      if (onSelectDemo) onSelectDemo(d)
                      setCurrentStep(2)
                    }}
                    style={{
                      borderBottom: '1px solid #1c1f27',
                      backgroundColor: isSelected ? 'rgba(99, 102, 241, 0.08)' : 'transparent',
                      cursor: 'pointer',
                      transition: 'background-color 0.15s ease',
                    }}
                  >
                    <td style={{ padding: '14px 20px', fontWeight: 600, color: '#f1f5f9' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <div
                          style={{
                            width: '32px',
                            height: '32px',
                            borderRadius: '6px',
                            backgroundColor: '#232836',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontWeight: 800,
                            color: '#fbbf24',
                          }}
                        >
                          {cleanMap[0]}
                        </div>
                        <div>
                          <div>{cleanMap}</div>
                          <div style={{ fontSize: '11px', color: '#64748b' }}>CS2 Subtick</div>
                        </div>
                      </div>
                    </td>
                    <td style={{ padding: '14px 16px', color: '#94a3b8' }}>
                      {new Date(d.created_at).toLocaleDateString()}
                    </td>
                    <td style={{ padding: '14px 16px' }}>
                      <span
                        style={{
                          backgroundColor: 'rgba(34, 197, 94, 0.12)',
                          color: '#4ade80',
                          padding: '3px 8px',
                          borderRadius: '4px',
                          fontWeight: 700,
                          fontSize: '12px',
                        }}
                      >
                        {d.rounds_count ? `${Math.min(13, d.rounds_count)}:${Math.max(0, d.rounds_count - 13)}` : '13:8'}
                      </span>
                    </td>
                    <td style={{ padding: '14px 16px', color: '#94a3b8' }}>
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                        <CrosshairIcon size={14} color="#38bdf8" /> Valve CS2
                      </span>
                    </td>
                    <td style={{ padding: '14px 16px', color: '#f1f5f9', fontWeight: 600 }}>
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                        <SparkleIcon size={13} color="#f59e0b" />
                        <span>{d.highlights_count} моментов</span>
                      </span>
                    </td>
                    <td style={{ padding: '14px 20px', textAlign: 'right' }}>
                      <button
                        type="button"
                        className="btn btn-primary card-interactive"
                        style={{ padding: '5px 14px', fontSize: '12px' }}
                        onClick={(e) => {
                          e.stopPropagation()
                          if (onSelectDemo) onSelectDemo(d)
                          setCurrentStep(2)
                        }}
                      >
                        Выбрать →
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    )}

      {/* ==================================================================== */}
      {/* STEP 2: CHOOSE PLAYER */}
      {currentStep === 2 && (
        <div key="step-2" className="step-transition" style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {/* Subheader Info Bar */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0 4px' }}>
            <div style={{ fontSize: '12.5px', color: '#94a3b8' }}>
              Матч: <strong style={{ color: '#38bdf8' }}>{(activeDemo?.map_name || 'Match').replace('de_', '').toUpperCase()}</strong> ({activeDemo?.rounds_count || 0} раундов) • Кликните на игрока для фильтрации хайлайтов и отображения на 2D радаре
            </div>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => setCurrentStep(1)}
              style={{ fontSize: '11px', padding: '4px 10px' }}
            >
              ← Сменить матч
            </button>
          </div>

          {/* Compact Inspected Player Strip with Streamlined Team Emblem */}
          {inspectedPlayer && (() => {
            const isCT = (inspectedPlayer.team || '').toLowerCase().includes('ct')
            const playerKills = highlights.filter((h) => h.pov_steam_id === inspectedPlayer.steam_id).length
            return (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '16px',
                  backgroundColor: '#0e121c',
                  border: `1px solid ${isCT ? 'rgba(56, 189, 248, 0.4)' : 'rgba(245, 158, 11, 0.4)'}`,
                  borderRadius: '10px',
                  padding: '8px 14px',
                  boxShadow: '0 6px 20px rgba(0, 0, 0, 0.45)',
                }}
              >
                {/* Left: Compact Team Logo Window (60x60) */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div
                    style={{
                      width: '60px',
                      height: '60px',
                      borderRadius: '8px',
                      backgroundColor: '#080a10',
                      border: `1px solid ${isCT ? 'rgba(56, 189, 248, 0.5)' : 'rgba(245, 158, 11, 0.5)'}`,
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      justifyContent: 'center',
                      position: 'relative',
                      boxShadow: `0 0 14px ${isCT ? 'rgba(56, 189, 248, 0.2)' : 'rgba(245, 158, 11, 0.2)'}`,
                      flexShrink: 0,
                    }}
                  >
                    <span style={{ fontSize: '20px', lineHeight: 1 }}>{isCT ? '🛡️' : '🎭'}</span>
                    <span
                      style={{
                        fontSize: '9px',
                        fontWeight: 800,
                        fontFamily: 'JetBrains Mono, monospace',
                        color: isCT ? '#38bdf8' : '#f59e0b',
                        letterSpacing: '0.04em',
                        marginTop: '2px',
                      }}
                    >
                      {isCT ? 'CT' : 'TERROR'}
                    </span>
                    <span
                      style={{
                        position: 'absolute',
                        top: '-4px',
                        right: '-4px',
                        fontSize: '7.5px',
                        fontWeight: 800,
                        background: isCT ? '#0284c7' : '#d97706',
                        color: '#ffffff',
                        padding: '1px 4px',
                        borderRadius: '3px',
                      }}
                    >
                      {isCT ? 'M4A1' : 'AK47'}
                    </span>
                  </div>

                  {/* Middle: Player Details */}
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '3px' }}>
                      <span
                        style={{
                          fontSize: '9px',
                          fontWeight: 800,
                          padding: '2px 6px',
                          borderRadius: '4px',
                          backgroundColor: isCT ? 'rgba(56, 189, 248, 0.18)' : 'rgba(245, 158, 11, 0.18)',
                          color: isCT ? '#38bdf8' : '#f59e0b',
                          border: `1px solid ${isCT ? 'rgba(56, 189, 248, 0.35)' : 'rgba(245, 158, 11, 0.35)'}`,
                          letterSpacing: '0.04em',
                        }}
                      >
                        ВЫБРАННЫЙ ИГРОК
                      </span>
                      <span style={{ fontSize: '17px', fontWeight: 800, color: '#f8fafc', letterSpacing: '-0.02em' }}>
                        {inspectedPlayer.name}
                      </span>
                      <span
                        style={{
                          fontSize: '10px',
                          fontWeight: 700,
                          padding: '1px 5px',
                          borderRadius: '3px',
                          backgroundColor: isCT ? 'rgba(56, 189, 248, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                          color: isCT ? '#38bdf8' : '#f59e0b',
                        }}
                      >
                        {(inspectedPlayer.team || '').toUpperCase()}
                      </span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '11.5px', color: '#94a3b8' }}>
                      <span>Раундов: <strong style={{ color: '#f1f5f9' }}>{activeDemo?.rounds_count || 0}</strong></span>
                      <span>•</span>
                      <span>Фрагов: <strong style={{ color: isCT ? '#38bdf8' : '#fbbf24' }}>{playerKills}</strong></span>
                      <span>•</span>
                      <span>Сторона: <strong style={{ color: isCT ? '#38bdf8' : '#f59e0b' }}>{isCT ? 'Спецназ (CT)' : 'Террористы (T)'}</strong></span>
                    </div>
                  </div>
                </div>

                {/* Right: Actions */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={() => {
                      onSetPlayerFilter(inspectedPlayer.steam_id)
                      setCurrentStep(3)
                    }}
                    style={{ padding: '6px 14px', fontSize: '12px', fontWeight: 700 }}
                  >
                    <span>Выбрать {inspectedPlayer.name} для нарезки</span>
                    <span>➔</span>
                  </button>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() =>
                      setSelectedPlayerForAnalytics({
                        steamIdOrName: inspectedPlayer.steam_id || inspectedPlayer.name,
                        name: inspectedPlayer.name,
                        team: inspectedPlayer.team,
                      })
                    }
                    style={{ padding: '6px 10px', fontSize: '11.5px' }}
                    title="Аналитика раундов и ADR игрока"
                  >
                    <ActivityIcon size={12} color="#38bdf8" />
                    <span>PR Анализ</span>
                  </button>
                </div>
              </div>
            )
          })()}

          {/* All Players Bar (Slim) */}
          <div
            className="card-interactive"
            onClick={() => {
              onSetPlayerFilter(null)
              setCurrentStep(3)
            }}
            style={{
              backgroundColor: '#16181f',
              border: activePlayerFilter === null ? '2px solid #38bdf8' : '1px solid #232630',
              borderRadius: '8px',
              padding: '8px 14px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              cursor: 'pointer',
              transition: 'all 0.15s ease',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <ZapIcon size={15} color="#f59e0b" />
              <span style={{ fontWeight: 700, fontSize: '13px', color: '#f1f5f9' }}>
                Все игроки матча
              </span>
              <span style={{ fontSize: '11.5px', color: '#94a3b8' }}>
                ({highlights.length} ключевых хайлайтов со всех 10 игроков)
              </span>
            </div>
            <span style={{ fontSize: '11.5px', color: '#38bdf8', fontWeight: 700 }}>
              Выбрать всех ➔
            </span>
          </div>

          {/* Player Cards Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(235px, 1fr))', gap: '8px' }}>
            {players.map((p) => {
              const pHighlights = highlights.filter((h) => h.pov_steam_id === p.steam_id)
              const pAces = pHighlights.filter((h) => h.highlight_type === 'ace' || h.kill_count >= 5).length
              const pMultikills = pHighlights.filter((h) => h.kill_count >= 2 && h.kill_count < 5).length
              const pClutches = pHighlights.filter((h) => h.highlight_type === 'clutch_candidate').length
              const isSelected = activePlayerFilter === p.steam_id
              const isCT = (p.team || '').toLowerCase().includes('ct')
              const isMe = mySteamId && (mySteamId === p.steam_id || mySteamId === p.name)

              return (
                <div
                  key={p.steam_id || p.name}
                  className="card-interactive"
                  onClick={() => {
                    onSetPlayerFilter(p.steam_id)
                    setCurrentStep(3)
                  }}
                  onMouseEnter={(e) => {
                    setInspectedPlayerSteamId(p.steam_id)
                    if (!isSelected) e.currentTarget.style.borderColor = '#38bdf8'
                  }}
                  style={{
                    backgroundColor: isMe ? 'rgba(245, 158, 11, 0.05)' : '#16181f',
                    border: isSelected
                      ? '2px solid #38bdf8'
                      : isMe
                      ? '1px solid rgba(245, 158, 11, 0.5)'
                      : '1px solid #232630',
                    borderRadius: '8px',
                    padding: '10px 12px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '8px',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                  onMouseLeave={(e) => {
                    if (!isSelected) e.currentTarget.style.borderColor = isMe ? 'rgba(245, 158, 11, 0.5)' : '#232630'
                  }}

                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <div
                        style={{
                          width: '36px',
                          height: '36px',
                          borderRadius: '8px',
                          backgroundColor: isCT ? 'rgba(56, 189, 248, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                          color: isCT ? '#38bdf8' : '#f59e0b',
                          border: `1px solid ${isCT ? 'rgba(56, 189, 248, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontWeight: 800,
                          fontSize: '14px',
                        }}
                      >
                        {p.name.slice(0, 2).toUpperCase()}
                      </div>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <span style={{ fontWeight: 700, fontSize: '14px', color: '#f1f5f9' }}>{p.name}</span>
                          {isMe && (
                            <span
                              style={{
                                fontSize: '10px',
                                fontWeight: 700,
                                padding: '1px 5px',
                                borderRadius: '4px',
                                backgroundColor: 'rgba(245, 158, 11, 0.2)',
                                color: '#fbbf24',
                                border: '1px solid rgba(245, 158, 11, 0.4)',
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '3px',
                              }}
                            >
                              <SparkleIcon size={9} color="#fbbf24" />
                              <span>ВЫ</span>
                            </span>
                          )}
                        </div>
                        <div style={{ fontSize: '11px', color: '#64748b' }}>
                          {isCT ? 'Counter-Terrorist' : 'Terrorist'}
                        </div>
                      </div>
                    </div>
                    <span
                      style={{
                        backgroundColor: pHighlights.length > 0 ? 'rgba(99, 102, 241, 0.15)' : 'rgba(100, 116, 139, 0.12)',
                        color: pHighlights.length > 0 ? '#818cf8' : '#94a3b8',
                        padding: '2px 8px',
                        borderRadius: '4px',
                        fontSize: '11px',
                        fontWeight: 700,
                      }}
                    >
                      {pHighlights.length} хайлайтов
                    </span>
                  </div>

                  {/* Highlights breakdown tags */}
                  <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', fontSize: '11px' }}>
                    {pAces > 0 && (
                      <span style={{ backgroundColor: 'rgba(245, 158, 11, 0.15)', color: '#fbbf24', padding: '1px 6px', borderRadius: '4px', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                        <TrophyIcon size={11} color="#fbbf24" />
                        <span>{pAces} ACE</span>
                      </span>
                    )}
                    {pMultikills > 0 && (
                      <span style={{ backgroundColor: 'rgba(139, 92, 246, 0.15)', color: '#c084fc', padding: '1px 6px', borderRadius: '4px', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                        <SkullIcon size={11} color="#c084fc" />
                        <span>{pMultikills} Мультикилл</span>
                      </span>
                    )}
                    {pClutches > 0 && (
                      <span style={{ backgroundColor: 'rgba(16, 185, 129, 0.15)', color: '#34d399', padding: '1px 6px', borderRadius: '4px', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                        <ZapIcon size={11} color="#34d399" />
                        <span>{pClutches} Клатч</span>
                      </span>
                    )}
                    {pHighlights.length === 0 && (
                      <span style={{ color: '#64748b', fontStyle: 'italic' }}>Нет ключевых эпизодов</span>
                    )}
                  </div>

                  {/* Action buttons */}
                  <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
                    <button
                      type="button"
                      className="btn btn-secondary card-interactive"
                      style={{
                        flex: 1,
                        padding: '6px 8px',
                        fontSize: '11px',
                        fontWeight: 600,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '4px',
                      }}
                      onClick={(e) => {
                        e.stopPropagation()
                        setSelectedPlayerForAnalytics({
                          steamIdOrName: p.steam_id || p.name,
                          name: p.name,
                          team: p.team,
                        })
                      }}
                      title={`Подробный разбор ошибок и PR аналитика для ${p.name}`}
                    >
                      <ActivityIcon size={12} color="#38bdf8" />
                      <span>Разбор & Ошибки</span>
                    </button>
                    <button
                      type="button"
                      className="btn btn-primary card-interactive"
                      style={{
                        flex: 1,
                        padding: '6px 8px',
                        fontSize: '11px',
                        fontWeight: 600,
                      }}
                      onClick={() => {
                        onSetPlayerFilter(p.steam_id)
                        setCurrentStep(3)
                      }}
                    >
                      Выбрать →
                    </button>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Step 2 Action Footer Bar */}
          <div
            style={{
              marginTop: '12px',
              padding: '16px 20px',
              backgroundColor: '#12151e',
              border: '1px solid #232838',
              borderRadius: '12px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.4)',
            }}
          >
            <div>
              <div style={{ fontSize: '14px', fontWeight: 700, color: '#f1f5f9' }}>
                Выбор игрока для нарезки
              </div>
              <div style={{ fontSize: '11px', color: '#94a3b8' }}>
                Выберите конкретного игрока выше или перейдите ко всем моментам матча
              </div>
            </div>

            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setCurrentStep(1)}
                style={{ padding: '8px 16px', fontSize: '12px', fontWeight: 600 }}
              >
                ← Сменить матч
              </button>
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => {
                  onSetPlayerFilter(null)
                  setCurrentStep(3)
                }}
                style={{
                  padding: '10px 24px',
                  fontSize: '13px',
                  fontWeight: 800,
                  backgroundColor: '#38bdf8',
                  color: '#090d16',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  boxShadow: '0 0 16px rgba(56, 189, 248, 0.35)',
                }}
              >
                Далее: Все моменты матча ({highlights.length}) →
              </button>
            </div>
          </div>
        </div>
      )}


      {/* ==================================================================== */}
      {/* STEP 3: CHOOSE MOMENTS (2D MAP + KILLFEED TABLE)                     */}
      {/* ==================================================================== */}
      {currentStep === 3 && (
        <div key="step-3" className="step-transition" style={{ display: 'grid', gridTemplateColumns: '480px 1fr', gap: '24px', alignItems: 'start' }}>
          {/* Left Column: 2D Radar Map & Round Replay Player */}
          <div>
            {/* Mode Switcher: Static Highlight Markers vs Full 2D Round Player */}
            <div style={{ display: 'flex', gap: '6px', marginBottom: '12px', backgroundColor: '#10131a', padding: '4px', borderRadius: '8px', border: '1px solid #232738' }}>
              <button
                type="button"
                className="card-interactive"
                onClick={() => setRadarTab('markers')}
                style={{
                  flex: 1,
                  padding: '7px 10px',
                  fontSize: '11px',
                  fontWeight: 700,
                  borderRadius: '6px',
                  border: 'none',
                  cursor: 'pointer',
                  backgroundColor: radarTab === 'markers' ? '#38bdf8' : 'transparent',
                  color: radarTab === 'markers' ? '#090d16' : '#94a3b8',
                  transition: 'all 0.15s ease',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px',
                }}
              >
                <CrosshairIcon size={13} color={radarTab === 'markers' ? '#090d16' : '#94a3b8'} />
                <span>Маркеры хайлайтов</span>
              </button>
              <button
                type="button"
                className="card-interactive"
                onClick={() => setRadarTab('replay')}
                style={{
                  flex: 1,
                  padding: '7px 10px',
                  fontSize: '11px',
                  fontWeight: 700,
                  borderRadius: '6px',
                  border: 'none',
                  cursor: 'pointer',
                  backgroundColor: radarTab === 'replay' ? '#38bdf8' : 'transparent',
                  color: radarTab === 'replay' ? '#090d16' : '#94a3b8',
                  transition: 'all 0.15s ease',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px',
                }}
              >
                <PlayIcon size={12} color={radarTab === 'replay' ? '#090d16' : '#94a3b8'} />
                <span>2D Плеер раунда</span>
              </button>
            </div>

            {/* TAB 1: Highlight Markers Radar */}
            {radarTab === 'markers' && (
              <div>
                <Map2DRadar
                  mapName={activeDemo?.map_name}
                  highlights={filteredHighlights}
                  selectedIds={selectedIds}
                  hoveredId={hoveredHighlightId}
                  onSelectHighlight={onToggleHighlight}
                  activeRound={activeRoundFilter}
                />

                {/* Quick Map Tips */}
                <div style={{ marginTop: '12px', padding: '10px 14px', backgroundColor: '#131622', border: '1px solid #23283c', borderRadius: '8px', fontSize: '11px', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <SparkleIcon size={14} color="#38bdf8" />
                  <span>Кликните на маркер фраг-эпизода для выбора, или переключитесь на <strong>«2D Плеер раунда»</strong> для покадрового просмотра.</span>
                </div>
              </div>
            )}

            {/* TAB 2: Full 2D Tactical Round Player */}
            {radarTab === 'replay' && (
              <div
                style={{
                  backgroundColor: '#10131b',
                  border: '1px solid #23283a',
                  borderRadius: '12px',
                  padding: '14px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px',
                }}
              >
                {/* Round Switcher & Layer Toggles Bar */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                  {/* Round Navigator */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <button
                      type="button"
                      onClick={handlePrevRound}
                      disabled={demoRounds.findIndex((r) => r.round_num === replayRoundNum) <= 0}
                      style={{
                        padding: '4px 8px',
                        fontSize: '11px',
                        fontWeight: 700,
                        backgroundColor: '#181c28',
                        color: '#94a3b8',
                        border: '1px solid #283044',
                        borderRadius: '4px',
                        cursor: 'pointer',
                      }}
                      title="Предыдущий раунд"
                    >
                      ⏮️
                    </button>

                    <select
                      value={replayRoundNum}
                      onChange={(e) => setReplayRoundNum(parseInt(e.target.value, 10))}
                      style={{
                        backgroundColor: '#181c28',
                        color: '#38bdf8',
                        border: '1px solid #283044',
                        borderRadius: '4px',
                        padding: '4px 8px',
                        fontSize: '11px',
                        fontWeight: 700,
                        cursor: 'pointer',
                      }}
                    >
                      {demoRounds.map((r) => (
                        <option key={r.round_num} value={r.round_num}>
                          Раунд {r.round_num} {r.winner ? `(${r.winner.toUpperCase()} Win)` : ''}
                        </option>
                      ))}
                    </select>

                    <button
                      type="button"
                      onClick={handleNextRound}
                      disabled={demoRounds.findIndex((r) => r.round_num === replayRoundNum) >= demoRounds.length - 1}
                      style={{
                        padding: '4px 8px',
                        fontSize: '11px',
                        fontWeight: 700,
                        backgroundColor: '#181c28',
                        color: '#94a3b8',
                        border: '1px solid #283044',
                        borderRadius: '4px',
                        cursor: 'pointer',
                      }}
                      title="Следующий раунд"
                    >
                      ⏭️
                    </button>
                  </div>

                  {/* Multilevel map switcher */}
                  {replayData?.levels && replayData.levels.length > 1 && (
                    <div style={{ display: 'flex', gap: '4px' }}>
                      <button
                        type="button"
                        onClick={() => setReplayLevel('upper')}
                        style={{
                          padding: '3px 8px',
                          fontSize: '10px',
                          fontWeight: 700,
                          borderRadius: '4px',
                          border: replayLevel === 'upper' ? '1px solid #38bdf8' : '1px solid #283044',
                          backgroundColor: replayLevel === 'upper' ? 'rgba(56, 189, 248, 0.2)' : 'transparent',
                          color: replayLevel === 'upper' ? '#38bdf8' : '#94a3b8',
                          cursor: 'pointer',
                        }}
                      >
                        Верх (A)
                      </button>
                      <button
                        type="button"
                        onClick={() => setReplayLevel('lower')}
                        style={{
                          padding: '3px 8px',
                          fontSize: '10px',
                          fontWeight: 700,
                          borderRadius: '4px',
                          border: replayLevel === 'lower' ? '1px solid #38bdf8' : '1px solid #283044',
                          backgroundColor: replayLevel === 'lower' ? 'rgba(56, 189, 248, 0.2)' : 'transparent',
                          color: replayLevel === 'lower' ? '#38bdf8' : '#94a3b8',
                          cursor: 'pointer',
                        }}
                      >
                        Низ (B)
                      </button>
                    </div>
                  )}

                  {/* Trails, Shots & Grenades Toggles */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '11px', color: '#94a3b8' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '4px', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={replayShowTrails}
                        onChange={(e) => setReplayShowTrails(e.target.checked)}
                        style={{ accentColor: '#38bdf8', cursor: 'pointer' }}
                      />
                      <span>Следы</span>
                    </label>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '4px', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={replayShowShots}
                        onChange={(e) => setReplayShowShots(e.target.checked)}
                        style={{ accentColor: '#fbbf24', cursor: 'pointer' }}
                      />
                      <span>Выстрелы</span>
                    </label>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '4px', cursor: 'pointer' }}>
                      <input
                        type="checkbox"
                        checked={replayShowGrenades}
                        onChange={(e) => setReplayShowGrenades(e.target.checked)}
                        style={{ accentColor: '#10b981', cursor: 'pointer' }}
                      />
                      <span>Гранаты</span>
                    </label>
                  </div>
                </div>

                {/* 2D Canvas Area (Strict 1:1 Square) */}
                <div style={{ position: 'relative', width: '100%', maxWidth: 'min(100%, 540px)', margin: '0 auto' }}>
                  {isReplayLoading && (
                    <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '10px', backgroundColor: 'rgba(10, 12, 16, 0.85)', zIndex: 50, color: '#38bdf8', fontSize: '12px', borderRadius: '10px' }}>
                      <div className="spinner" style={{ width: '24px', height: '24px' }} />
                      <span>Загрузка тактических тиков раунда...</span>
                    </div>
                  )}

                  {replayError && (
                    <div style={{ position: 'absolute', inset: 0, padding: '20px', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(239, 68, 68, 0.1)', color: '#f87171', fontSize: '12px', textAlign: 'center', zIndex: 50, borderRadius: '10px' }}>
                      {replayError}
                    </div>
                  )}

                  <TacticalReplayRadar
                    radarImageUrl={replayRadarImageUrl}
                    mapName={activeDemo?.map_name || 'CS2 Map'}
                    currentTick={currentReplayFrame?.tick || 0}
                    tickrate={replayData?.tickrate || 128}
                    startTick={replayData?.start_tick || 0}
                    players={currentReplayFrame?.players || []}
                    kills={replayData?.kills || []}
                    grenades={replayData?.grenades || []}
                    bomb={replayData?.bomb}
                    playerTrails={playerReplayTrails}
                    currentLevel={replayLevel}
                    hasMultipleLevels={Boolean(replayData?.levels && replayData.levels.length > 1)}
                    showTrails={replayShowTrails}
                    showShots={replayShowShots}
                    showGrenades={replayShowGrenades}
                    onJumpToTick={handleJumpToReplayTick}
                    maxContainerHeight="540px"
                  />
                </div>

                {/* Timeline Scrubber & Media Player Controls */}
                <div style={{ backgroundColor: '#0d0f16', border: '1px solid #1c202d', borderRadius: '8px', padding: '10px 12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {/* Scrubber slider & timestamps */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ fontSize: '11px', fontFamily: 'monospace', color: '#38bdf8', minWidth: '34px' }}>
                      {currentReplayFrame && replayData ? formatReplayTime(currentReplayFrame.tick, replayData.start_tick, replayData.tickrate) : '0:00'}
                    </span>
                    <input
                      type="range"
                      min="0"
                      max={Math.max(0, (replayData?.frames.length || 1) - 1)}
                      value={replayFrameIndex}
                      onChange={(e) => {
                        setReplayFrameIndex(parseInt(e.target.value, 10))
                        setIsReplayPlaying(false)
                      }}
                      style={{ flex: 1, accentColor: '#38bdf8', cursor: 'pointer' }}
                    />
                    <span style={{ fontSize: '11px', fontFamily: 'monospace', color: '#64748b', minWidth: '34px', textAlign: 'right' }}>
                      {replayData ? formatReplayTime(replayData.end_tick, replayData.start_tick, replayData.tickrate) : '0:00'}
                    </span>
                  </div>

                  {/* Playback Buttons & Speed Selector */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px' }}>
                    {/* Rewind / Play / Forward */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <button
                        type="button"
                        onClick={() => {
                          const framesToJump = Math.floor((replayData?.tickrate || 64) * 5 / 32)
                          setReplayFrameIndex((prev) => Math.max(0, prev - framesToJump))
                        }}
                        style={{ padding: '4px 8px', fontSize: '11px', backgroundColor: '#181b26', border: '1px solid #282f42', borderRadius: '4px', color: '#cbd5e1', cursor: 'pointer' }}
                        title="Назад на 5 секунд"
                      >
                        ↺ 5s
                      </button>

                      <button
                        type="button"
                        className="card-interactive"
                        onClick={() => setIsReplayPlaying(!isReplayPlaying)}
                        style={{
                          padding: '6px 14px',
                          fontSize: '12px',
                          fontWeight: 800,
                          backgroundColor: isReplayPlaying ? '#f59e0b' : '#38bdf8',
                          color: '#090d16',
                          border: 'none',
                          borderRadius: '6px',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                        }}
                      >
                        {isReplayPlaying ? (
                          <>
                            <PauseIcon size={12} color="#090d16" />
                            <span>Пауза</span>
                          </>
                        ) : (
                          <>
                            <PlayIcon size={12} color="#090d16" />
                            <span>Плей</span>
                          </>
                        )}
                      </button>

                      <button
                        type="button"
                        onClick={() => {
                          const framesToJump = Math.floor((replayData?.tickrate || 64) * 5 / 32)
                          const maxFrames = (replayData?.frames.length || 1) - 1
                          setReplayFrameIndex((prev) => Math.min(maxFrames, prev + framesToJump))
                        }}
                        style={{ padding: '4px 8px', fontSize: '11px', backgroundColor: '#181b26', border: '1px solid #282f42', borderRadius: '4px', color: '#cbd5e1', cursor: 'pointer' }}
                        title="Вперед на 5 секунд"
                      >
                        5s ↻
                      </button>
                    </div>

                    {/* Speed options */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
                      {[0.5, 1, 2, 4].map((spd) => (
                        <button
                          key={spd}
                          type="button"
                          onClick={() => setReplaySpeed(spd)}
                          style={{
                            padding: '3px 6px',
                            fontSize: '10px',
                            fontWeight: 700,
                            borderRadius: '4px',
                            border: replaySpeed === spd ? '1px solid #38bdf8' : '1px solid #282f42',
                            backgroundColor: replaySpeed === spd ? 'rgba(56, 189, 248, 0.2)' : 'transparent',
                            color: replaySpeed === spd ? '#38bdf8' : '#64748b',
                            cursor: 'pointer',
                          }}
                        >
                          {spd}x
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Right Column: Filters Bar & Moments Table */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {/* Filter toolbar */}
            <div
              style={{
                backgroundColor: '#16181f',
                border: '1px solid #232630',
                borderRadius: '10px',
                padding: '14px 16px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: '12px',
              }}
            >
              {/* Badges / Dropdowns for Player, Weapon, Event */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                {/* Event Type Filter */}
                <select
                  value={activeTypeFilter || 'all'}
                  onChange={(e) => onSetTypeFilter(e.target.value === 'all' ? null : e.target.value)}
                  style={{
                    backgroundColor: '#121316',
                    border: '1px solid #2b2e38',
                    borderRadius: '6px',
                    color: '#f1f5f9',
                    padding: '6px 10px',
                    fontSize: '12px',
                    fontWeight: 600,
                  }}
                >
                  <option value="all">События: Все</option>
                  <option value="ace">ACE (5K)</option>
                  <option value="multikill_4k">4K Квадро</option>
                  <option value="multikill_3k">3K Тройное</option>
                  <option value="multikill_2k">2K Дабл-килл</option>
                  <option value="clutch_candidate">Клатчи</option>
                  <option value="kill">Одиночные киллы</option>
                </select>

                {/* Player Filter */}
                <select
                  value={activePlayerFilter || 'all'}
                  onChange={(e) => onSetPlayerFilter(e.target.value === 'all' ? null : e.target.value)}
                  style={{
                    backgroundColor: '#121316',
                    border: '1px solid #2b2e38',
                    borderRadius: '6px',
                    color: '#f1f5f9',
                    padding: '6px 10px',
                    fontSize: '12px',
                    fontWeight: 600,
                  }}
                >
                  <option value="all">Игрок: Все ({players.length})</option>
                  {players.map((p) => (
                    <option key={p.steam_id || p.name} value={p.steam_id || ''}>
                      {p.name} ({p.team?.toUpperCase() || 'SPEC'})
                    </option>
                  ))}
                </select>

                {activePlayerFilter && activeDemo && (
                  <button
                    type="button"
                    className="btn btn-secondary card-interactive"
                    style={{
                      padding: '5px 10px',
                      fontSize: '12px',
                      fontWeight: 600,
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                      borderColor: '#38bdf8',
                      color: '#38bdf8',
                    }}
                    onClick={() => {
                      const p = players.find((x) => x.steam_id === activePlayerFilter)
                      if (p) {
                        setSelectedPlayerForAnalytics({
                          steamIdOrName: p.steam_id || p.name,
                          name: p.name,
                          team: p.team,
                        })
                      }
                    }}
                    title="Открыть тактический разбор и PR рейтинг выбранного игрока"
                  >
                    <ActivityIcon size={12} color="#38bdf8" />
                    <span>Разбор игрока</span>
                  </button>
                )}


                {/* Weapon Filter */}
                <select
                  value={weaponFilter || 'all'}
                  onChange={(e) => setWeaponFilter(e.target.value === 'all' ? null : e.target.value)}
                  style={{
                    backgroundColor: '#121316',
                    border: '1px solid #2b2e38',
                    borderRadius: '6px',
                    color: '#f1f5f9',
                    padding: '6px 10px',
                    fontSize: '12px',
                    fontWeight: 600,
                  }}
                >
                  <option value="all">Оружие: Все</option>
                  <option value="ak47">AK-47</option>
                  <option value="m4a1">M4A1 / M4A4</option>
                  <option value="awp">AWP</option>
                  <option value="deagle">Desert Eagle</option>
                  <option value="glock">Glock-18</option>
                  <option value="usp">USP-S</option>
                </select>

                {/* Round Filter */}
                <select
                  value={activeRoundFilter === null ? 'all' : activeRoundFilter}
                  onChange={(e) => onSetRoundFilter(e.target.value === 'all' ? null : Number(e.target.value))}
                  style={{
                    backgroundColor: '#121316',
                    border: '1px solid #2b2e38',
                    borderRadius: '6px',
                    color: '#f1f5f9',
                    padding: '6px 10px',
                    fontSize: '12px',
                    fontWeight: 600,
                  }}
                >
                  <option value="all">Все раунды ({roundNumbers.length})</option>
                  {roundNumbers.map((r) => (
                    <option key={r} value={r}>Раунд {r}</option>
                  ))}
                </select>
              </div>

              {/* Selection Counter & Batch buttons */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span
                  style={{
                    fontSize: '12px',
                    fontWeight: 700,
                    color: selectedIds.size > 0 ? '#a855f7' : '#94a3b8',
                    backgroundColor: '#121316',
                    padding: '4px 8px',
                    borderRadius: '4px',
                    border: '1px solid #2b2e38',
                  }}
                >
                  {selectedIds.size}/{filteredHighlights.length} моментов
                </span>

                <button
                  type="button"
                  className="btn btn-secondary card-interactive"
                  onClick={() => {
                    if (allFilteredSelected) onClearFiltered(filteredIds)
                    else onSelectAllFiltered(filteredIds)
                  }}
                  style={{ padding: '5px 10px', fontSize: '11px' }}
                >
                  {allFilteredSelected ? 'Снять все' : 'Выбрать все'}
                </button>
              </div>
            </div>

            {/* Player Focus Studio Card if a player is selected */}
            {activePlayerFilter && (() => {
              const selectedPlayer = players.find((p) => p.steam_id === activePlayerFilter)
              if (!selectedPlayer) return null
              const playerHighlights = highlights.filter((h) => h.pov_steam_id === activePlayerFilter)
              const playerMultikills = playerHighlights.filter((h) => h.highlight_type.startsWith('multikill')).length
              const isCT = (selectedPlayer.team || '').toLowerCase() === 'ct'
              const teamColor = isCT ? '#38bdf8' : '#eab308'

              return (
                <div
                  style={{
                    backgroundColor: '#12141c',
                    border: `1px solid ${teamColor}40`,
                    borderRadius: '8px',
                    padding: '14px 16px',
                    marginBottom: '12px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '12px',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <div
                        style={{
                          width: '32px',
                          height: '32px',
                          borderRadius: '6px',
                          backgroundColor: `${teamColor}20`,
                          border: `1px solid ${teamColor}`,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontSize: '11px',
                          fontWeight: 800,
                          color: teamColor,
                        }}
                      >
                        {selectedPlayer.team?.toUpperCase() || 'SPEC'}
                      </div>
                      <div>
                        <div style={{ fontSize: '15px', fontWeight: 700, color: '#f1f5f9' }}>
                          {selectedPlayer.name}
                        </div>
                        <div style={{ fontSize: '11px', color: '#64748b' }}>
                          SteamID: {selectedPlayer.steam_id || 'N/A'} • {playerHighlights.length} хайлайтов ({playerMultikills} мульти-киллов)
                        </div>
                      </div>
                    </div>

                    <div style={{ display: 'flex', gap: '8px' }}>
                      {playerHighlights.length > 0 && (
                        <button
                          type="button"
                          className="btn btn-primary card-interactive"
                          style={{ padding: '6px 14px', fontSize: '11px', backgroundColor: teamColor, color: '#090d16', border: 'none', fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: '5px' }}
                          onClick={() => {
                            playerHighlights.forEach((h) => {
                              if (!selectedIds.has(h.id)) onToggleHighlight(h.id)
                            })
                            onSetPlayerFilter(selectedPlayer.name)
                            setCurrentStep(3)
                          }}
                        >
                          <SparkleIcon size={12} color="#090d16" />
                          <span>Выбрать моменты {selectedPlayer.name} ({playerHighlights.length}) →</span>
                        </button>
                      )}
                      <button
                        type="button"
                        className="btn btn-secondary card-interactive"
                        style={{ padding: '6px 10px', fontSize: '11px' }}
                        onClick={() => onSetPlayerFilter(null)}
                      >
                        ✕ Сбросить
                      </button>
                    </div>
                  </div>
                </div>
              )
            })()}

            {/* Moments Killfeed List */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '520px', overflowY: 'auto' }}>
              {filteredHighlights.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '40px 0', color: '#64748b', fontSize: '13px' }}>
                  Нет моментов, подходящих под выбранные фильтры.
                </div>
              ) : (
                filteredHighlights.map((h) => {
                  const isSelected = selectedIds.has(h.id)
                  const isHovered = hoveredHighlightId === h.id
                  const kill = getHighlightKillDetails(h)
                  const killerName = kill?.attacker_name || h.pov_name || 'Player'
                  const victimName = kill?.victim_name || 'Opponent'
                  const weapon = cleanWeaponName(kill?.weapon)

                  return (
                    <div
                      key={h.id}
                      className={`moment-row ${isSelected ? 'selected' : ''}`}
                      onClick={() => {
                        onToggleHighlight(h.id)
                        if (radarTab === 'replay') {
                          if (replayRoundNum !== h.round_num) {
                            setReplayRoundNum(h.round_num)
                          }
                          handleJumpToReplayTick(h.kill_start_tick)
                        }
                      }}
                      onMouseEnter={() => setHoveredHighlightId(h.id)}
                      onMouseLeave={() => setHoveredHighlightId(null)}
                      style={{
                        borderColor: isHovered ? '#4f46e5' : isSelected ? 'rgba(168, 85, 247, 0.4)' : '#232630',
                      }}
                    >
                      {/* Checkbox */}
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => onToggleHighlight(h.id)}
                        onClick={(e) => e.stopPropagation()}
                        style={{ width: '16px', height: '16px', accentColor: '#6366f1', cursor: 'pointer' }}
                      />

                      {/* Round badge */}
                      <span
                        style={{
                          backgroundColor: '#121316',
                          border: '1px solid #2b2e38',
                          color: '#f1f5f9',
                          fontWeight: 700,
                          fontSize: '11px',
                          padding: '3px 6px',
                          borderRadius: '4px',
                          textAlign: 'center',
                        }}
                      >
                        Р {h.round_num}
                      </span>

                      {/* Elapsed timing */}
                      <span style={{ fontSize: '12px', color: '#94a3b8', fontFamily: 'monospace' }}>
                        {formatRoundTime(h.kill_start_tick)}
                      </span>

                      {/* Killfeed presentation (Killer -> Weapon -> Headshot -> Victim) */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', overflow: 'hidden' }}>
                        {/* Killer avatar */}
                        <div
                          style={{
                            width: '24px',
                            height: '24px',
                            borderRadius: '50%',
                            backgroundColor: '#2563eb',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontWeight: 800,
                            fontSize: '11px',
                            color: '#fff',
                            flexShrink: 0,
                          }}
                        >
                          {killerName[0]?.toUpperCase()}
                        </div>
                        <span style={{ fontWeight: 600, fontSize: '12px', color: '#f1f5f9', whiteSpace: 'nowrap' }}>
                          {killerName}
                        </span>

                        {/* Weapon badge */}
                        <span
                          style={{
                            fontSize: '11px',
                            fontWeight: 700,
                            color: '#fbbf24',
                            backgroundColor: 'rgba(251, 191, 36, 0.1)',
                            padding: '2px 6px',
                            borderRadius: '4px',
                            whiteSpace: 'nowrap',
                          }}
                        >
                          {weapon}
                        </span>

                        {/* Headshot badge */}
                        {kill?.headshot && (
                          <span title="Headshot" style={{ display: 'inline-flex', alignItems: 'center' }}>
                            <CrosshairIcon size={12} color="#ef4444" />
                          </span>
                        )}

                        {/* Victim avatar & name */}
                        <div
                          style={{
                            width: '24px',
                            height: '24px',
                            borderRadius: '50%',
                            backgroundColor: '#dc2626',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontWeight: 800,
                            fontSize: '11px',
                            color: '#fff',
                            flexShrink: 0,
                          }}
                        >
                          {victimName[0]?.toUpperCase()}
                        </div>
                        <span style={{ fontSize: '12px', color: '#94a3b8', whiteSpace: 'nowrap' }}>
                          {victimName}
                        </span>
                      </div>

                      {/* Highlight Type Pill & Quick Render */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span
                          style={{
                            fontSize: '10px',
                            fontWeight: 800,
                            padding: '2px 6px',
                            borderRadius: '4px',
                            backgroundColor: h.highlight_type === 'ace' ? '#f59e0b' : '#38bdf8',
                            color: '#000',
                            textTransform: 'uppercase',
                          }}
                        >
                          {h.highlight_type.replace('multikill_', '').toUpperCase()}
                        </span>
                        <button
                          type="button"
                          className="btn btn-secondary card-interactive"
                          onClick={(e) => {
                            e.stopPropagation()
                            if (!selectedIds.has(h.id)) {
                              onToggleHighlight(h.id)
                            }
                            setCurrentStep(4)
                          }}
                          title="Выбрать и перейти к настройке записи этого момента"
                          style={{ padding: '3px 8px', fontSize: '11px', borderRadius: '4px', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                        >
                          <FilmIcon size={11} color="#94a3b8" />
                          <span>Запись →</span>
                        </button>
                      </div>
                    </div>
                  )
                })
              )}
            </div>

            {/* Step 3 Action Navigation Bar */}
            <div
              style={{
                marginTop: '16px',
                padding: '16px 20px',
                backgroundColor: '#12151e',
                border: '1px solid #232838',
                borderRadius: '12px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                boxShadow: '0 8px 24px rgba(0, 0, 0, 0.4)',
              }}
            >
              <div>
                <div style={{ fontSize: '14px', fontWeight: 700, color: '#f1f5f9' }}>
                  Выбрано моментов: <strong style={{ color: '#38bdf8' }}>{selectedIds.size}</strong> из {highlights.length}
                </div>
                <div style={{ fontSize: '11px', color: '#94a3b8' }}>
                  {selectedIds.size === 0
                    ? 'Отметьте хотя бы один момент галочкой для перехода к записи'
                    : 'Моменты выбраны! Нажмите «Далее» для настройки 4:3, стилей радара и записи'}
                </div>
              </div>

              <div style={{ display: 'flex', gap: '10px' }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setCurrentStep(2)}
                  style={{ padding: '8px 16px', fontSize: '12px', fontWeight: 600 }}
                >
                  ← Назад к игрокам
                </button>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => setCurrentStep(4)}
                  disabled={selectedIds.size === 0}
                  style={{
                    padding: '10px 24px',
                    fontSize: '13px',
                    fontWeight: 800,
                    backgroundColor: selectedIds.size > 0 ? '#6366f1' : '#334155',
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: '8px',
                    cursor: selectedIds.size > 0 ? 'pointer' : 'not-allowed',
                    boxShadow: selectedIds.size > 0 ? '0 0 20px rgba(99, 102, 241, 0.5)' : 'none',
                    transition: 'all 0.2s ease',
                  }}
                >
                  Далее: Настройки и запись ({selectedIds.size}) →
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* STEP 4: COMPILE MONTAGE (SETTINGS CARDS & EXPORT)                    */}
      {/* ==================================================================== */}
      {currentStep === 4 && (
        <div key="step-4" className="step-transition" style={{ display: 'grid', gridTemplateColumns: 'minmax(500px, 1.15fr) minmax(420px, 0.95fr)', gap: '28px', alignItems: 'start' }}>
          {/* Left Column: Settings Cards */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* Montage Title Input */}
            <div
              style={{
                backgroundColor: '#16181f',
                border: '1px solid #232630',
                borderRadius: '10px',
                padding: '16px 20px',
              }}
            >
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 700, color: '#f1f5f9', marginBottom: '8px' }}>
                Придумай название нарезки:
              </label>
              <input
                type="text"
                value={montageTitle}
                onChange={(e) => setMontageTitle(e.target.value)}
                style={{
                  width: '100%',
                  backgroundColor: '#121316',
                  border: '1px solid #2b2e38',
                  borderRadius: '6px',
                  padding: '8px 12px',
                  color: '#f1f5f9',
                  fontSize: '13px',
                }}
              />
            </div>

            {/* Main Settings Card */}
            <div
              style={{
                backgroundColor: '#16181f',
                border: '1px solid #232630',
                borderRadius: '10px',
                padding: '20px',
                display: 'flex',
                flexDirection: 'column',
                gap: '16px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #232630', paddingBottom: '12px' }}>
                <div>
                  <div style={{ fontSize: '15px', fontWeight: 700, color: '#f1f5f9', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <SlidersIcon size={16} color="#38bdf8" />
                    <span>Параметры видео и экспорта CS2</span>
                  </div>
                  <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '2px' }}>
                    Режиссер POV, киберспортивный 4:3, стили радара и тактические тумблеры
                  </div>
                </div>
              </div>

              {/* 1. POV DIRECTOR */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '8px' }}>
                  <div style={{ fontSize: '12px', fontWeight: 700, color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <CameraIcon size={14} color="#38bdf8" />
                    <span>РЕЖИССЕР КАМЕРЫ (POV)</span>
                  </div>
                  <span style={{ fontSize: '11px', color: '#38bdf8', fontWeight: 600 }}>
                    {clipSettings?.perspective === 'dynamic_killcam'
                      ? '⚡ Турнирный Килл-кам (2 сессии)'
                      : clipSettings?.perspective === 'victim'
                      ? '💀 Лицо жертвы'
                      : '🎬 Главный герой (ГГ)'}
                  </span>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
                  {/* Option 1: Attacker (Hero) */}
                  <button
                    type="button"
                    className="btn card-interactive"
                    onClick={() => onUpdateSettings && clipSettings && onUpdateSettings({ ...clipSettings, perspective: 'attacker' })}
                    style={{
                      padding: '10px',
                      textAlign: 'left',
                      backgroundColor: (!clipSettings?.perspective || clipSettings?.perspective === 'attacker') ? 'rgba(56, 189, 248, 0.12)' : '#12141c',
                      borderColor: (!clipSettings?.perspective || clipSettings?.perspective === 'attacker') ? '#38bdf8' : '#232734',
                      borderWidth: '1px',
                      borderStyle: 'solid',
                      borderRadius: '8px',
                      cursor: 'pointer',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '4px',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <span style={{ fontSize: '11px', fontWeight: 700, color: (!clipSettings?.perspective || clipSettings?.perspective === 'attacker') ? '#38bdf8' : '#e2e8f0' }}>
                        🎬 Главный Герой
                      </span>
                    </div>
                    <div style={{ fontSize: '9px', color: '#94a3b8', lineHeight: '1.2' }}>
                      100% от автора фрагов (1 запуск CS2)
                    </div>
                  </button>

                  {/* Option 2: Dynamic Killcam */}
                  <button
                    type="button"
                    className="btn card-interactive"
                    onClick={() => onUpdateSettings && clipSettings && onUpdateSettings({ ...clipSettings, perspective: 'dynamic_killcam' })}
                    style={{
                      padding: '10px',
                      textAlign: 'left',
                      backgroundColor: clipSettings?.perspective === 'dynamic_killcam' ? 'rgba(139, 92, 246, 0.15)' : '#12141c',
                      borderColor: clipSettings?.perspective === 'dynamic_killcam' ? '#8b5cf6' : '#232734',
                      borderWidth: '1px',
                      borderStyle: 'solid',
                      borderRadius: '8px',
                      cursor: 'pointer',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '4px',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <span style={{ fontSize: '11px', fontWeight: 700, color: clipSettings?.perspective === 'dynamic_killcam' ? '#a78bfa' : '#e2e8f0' }}>
                        ⚡ Килл-кам PRO
                      </span>
                    </div>
                    <div style={{ fontSize: '9px', color: '#94a3b8', lineHeight: '1.2' }}>
                      Смерти жертв ➔ Откат ➔ Триумф ГГ (2 запуска)
                    </div>
                  </button>

                  {/* Option 3: Victim */}
                  <button
                    type="button"
                    className="btn card-interactive"
                    onClick={() => onUpdateSettings && clipSettings && onUpdateSettings({ ...clipSettings, perspective: 'victim' })}
                    style={{
                      padding: '10px',
                      textAlign: 'left',
                      backgroundColor: clipSettings?.perspective === 'victim' ? 'rgba(239, 68, 68, 0.15)' : '#12141c',
                      borderColor: clipSettings?.perspective === 'victim' ? '#ef4444' : '#232734',
                      borderWidth: '1px',
                      borderStyle: 'solid',
                      borderRadius: '8px',
                      cursor: 'pointer',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '4px',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <span style={{ fontSize: '11px', fontWeight: 700, color: clipSettings?.perspective === 'victim' ? '#f87171' : '#e2e8f0' }}>
                        💀 Только Жертва
                      </span>
                    </div>
                    <div style={{ fontSize: '9px', color: '#94a3b8', lineHeight: '1.2' }}>
                      Камера от лица погибших врагов
                    </div>
                  </button>
                </div>
              </div>

              {/* 2. SCREEN, FORMAT, RESOLUTION, FPS & FOV */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', backgroundColor: '#12141c', padding: '14px', borderRadius: '8px', border: '1px solid #232734' }}>
                <div style={{ fontSize: '12px', fontWeight: 700, color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <CrosshairIcon size={14} color="#38bdf8" />
                  <span>ФОРМАТ, РАЗРЕШЕНИЕ И УГОЛ ОБЗОРА (FOV)</span>
                </div>

                {/* Aspect Ratio */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <span style={{ fontSize: '12px', color: '#f1f5f9', fontWeight: 600, display: 'block' }}>Формат экрана CS2</span>
                    <span style={{ fontSize: '10px', color: '#94a3b8' }}>4:3 расширяет модельки врагов на 33%</span>
                  </div>
                  <div style={{ display: 'flex', gap: '4px', backgroundColor: '#0e1118', padding: '2px', borderRadius: '6px', border: '1px solid #232734' }}>
                    <button
                      type="button"
                      className="card-interactive"
                      onClick={() => {
                        setAspectRatio('4:3')
                        if (onUpdateSettings && clipSettings) {
                          onUpdateSettings({ ...clipSettings, aspectRatio: '4:3', resolution: '1280x960' })
                        }
                      }}
                      style={{
                        padding: '5px 12px',
                        fontSize: '11px',
                        fontWeight: 700,
                        borderRadius: '4px',
                        border: 'none',
                        cursor: 'pointer',
                        backgroundColor: (clipSettings?.aspectRatio === '4:3' || aspectRatio === '4:3') ? '#38bdf8' : 'transparent',
                        color: (clipSettings?.aspectRatio === '4:3' || aspectRatio === '4:3') ? '#090d16' : '#94a3b8',
                      }}
                    >
                      4:3 (Киберспорт)
                    </button>
                    <button
                      type="button"
                      className="card-interactive"
                      onClick={() => {
                        setAspectRatio('16:9')
                        if (onUpdateSettings && clipSettings) {
                          onUpdateSettings({ ...clipSettings, aspectRatio: '16:9', resolution: '1080p' })
                        }
                      }}
                      style={{
                        padding: '5px 12px',
                        fontSize: '11px',
                        fontWeight: 700,
                        borderRadius: '4px',
                        border: 'none',
                        cursor: 'pointer',
                        backgroundColor: (clipSettings?.aspectRatio !== '4:3' && aspectRatio !== '4:3') ? '#38bdf8' : 'transparent',
                        color: (clipSettings?.aspectRatio !== '4:3' && aspectRatio !== '4:3') ? '#090d16' : '#94a3b8',
                      }}
                    >
                      16:9 (Широкий)
                    </button>
                  </div>
                </div>

                {/* Resolution buttons */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid #1c202d', paddingTop: '8px' }}>
                  <div>
                    <span style={{ fontSize: '12px', color: '#f1f5f9', fontWeight: 600, display: 'block' }}>
                      {(clipSettings?.aspectRatio === '4:3' || aspectRatio === '4:3') ? 'Разрешение 4:3' : 'Разрешение 16:9'}
                    </span>
                    <span style={{ fontSize: '10px', color: '#94a3b8' }}>
                      {(clipSettings?.aspectRatio === '4:3' || aspectRatio === '4:3') ? '1280x960 — выбор s1mple & m0NESY' : '1920x1080 — стандарт Full HD'}
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: '5px' }}>
                    {(clipSettings?.aspectRatio === '4:3' || aspectRatio === '4:3') ? (
                      <>
                        <button
                          type="button"
                          className="btn card-interactive"
                          onClick={() => onUpdateSettings && clipSettings && onUpdateSettings({ ...clipSettings, resolution: '1280x960', aspectRatio: '4:3' })}
                          style={{
                            padding: '4px 8px',
                            fontSize: '11px',
                            fontWeight: 700,
                            backgroundColor: (clipSettings?.resolution === '1280x960' || !clipSettings?.resolution || clipSettings?.resolution === '1080p') ? '#38bdf8' : '#1c2333',
                            color: (clipSettings?.resolution === '1280x960' || !clipSettings?.resolution || clipSettings?.resolution === '1080p') ? '#090d16' : '#cbd5e1',
                            border: '1px solid #2d3748',
                            borderRadius: '4px',
                          }}
                        >
                          1280x960
                        </button>
                        <button
                          type="button"
                          className="btn card-interactive"
                          onClick={() => onUpdateSettings && clipSettings && onUpdateSettings({ ...clipSettings, resolution: '1440x1080', aspectRatio: '4:3' })}
                          style={{
                            padding: '4px 8px',
                            fontSize: '11px',
                            fontWeight: 700,
                            backgroundColor: clipSettings?.resolution === '1440x1080' ? '#38bdf8' : '#1c2333',
                            color: clipSettings?.resolution === '1440x1080' ? '#090d16' : '#cbd5e1',
                            border: '1px solid #2d3748',
                            borderRadius: '4px',
                          }}
                        >
                          1440x1080
                        </button>
                        <button
                          type="button"
                          className="btn card-interactive"
                          onClick={() => onUpdateSettings && clipSettings && onUpdateSettings({ ...clipSettings, resolution: '1024x768', aspectRatio: '4:3' })}
                          style={{
                            padding: '4px 8px',
                            fontSize: '11px',
                            fontWeight: 700,
                            backgroundColor: clipSettings?.resolution === '1024x768' ? '#38bdf8' : '#1c2333',
                            color: clipSettings?.resolution === '1024x768' ? '#090d16' : '#cbd5e1',
                            border: '1px solid #2d3748',
                            borderRadius: '4px',
                          }}
                        >
                          1024x768
                        </button>
                      </>
                    ) : (
                      <>
                        <button
                          type="button"
                          className="btn card-interactive"
                          onClick={() => onUpdateSettings && clipSettings && onUpdateSettings({ ...clipSettings, resolution: '1080p', aspectRatio: '16:9' })}
                          style={{
                            padding: '4px 10px',
                            fontSize: '11px',
                            fontWeight: 700,
                            backgroundColor: (clipSettings?.resolution === '1080p' || clipSettings?.resolution === '1920x1080') ? '#38bdf8' : '#1c2333',
                            color: (clipSettings?.resolution === '1080p' || clipSettings?.resolution === '1920x1080') ? '#090d16' : '#cbd5e1',
                            border: '1px solid #2d3748',
                            borderRadius: '4px',
                          }}
                        >
                          1080p Full HD
                        </button>
                        <button
                          type="button"
                          className="btn card-interactive"
                          onClick={() => onUpdateSettings && clipSettings && onUpdateSettings({ ...clipSettings, resolution: '720p', aspectRatio: '16:9' })}
                          style={{
                            padding: '4px 10px',
                            fontSize: '11px',
                            fontWeight: 700,
                            backgroundColor: clipSettings?.resolution === '720p' ? '#38bdf8' : '#1c2333',
                            color: clipSettings?.resolution === '720p' ? '#090d16' : '#cbd5e1',
                            border: '1px solid #2d3748',
                            borderRadius: '4px',
                          }}
                        >
                          720p HD
                        </button>
                      </>
                    )}
                  </div>
                </div>

                {/* FPS & FOV row */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', borderTop: '1px solid #1c202d', paddingTop: '8px' }}>
                  {/* FPS */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <span style={{ fontSize: '11px', color: '#cbd5e1', fontWeight: 600 }}>Частота кадров (FPS)</span>
                    <div style={{ display: 'flex', gap: '4px' }}>
                      {([60, 120, 30] as const).map((fpsVal) => {
                        const isSelected = (clipSettings?.fps || 60) === fpsVal
                        return (
                          <button
                            key={fpsVal}
                            type="button"
                            className="btn card-interactive"
                            onClick={() => onUpdateSettings && clipSettings && onUpdateSettings({ ...clipSettings, fps: fpsVal })}
                            style={{
                              flex: 1,
                              padding: '4px 6px',
                              fontSize: '11px',
                              fontWeight: 700,
                              backgroundColor: isSelected ? '#38bdf8' : '#1c2333',
                              color: isSelected ? '#090d16' : '#cbd5e1',
                              border: '1px solid #2d3748',
                              borderRadius: '4px',
                              cursor: 'pointer',
                            }}
                          >
                            {fpsVal === 120 ? '120⚡' : `${fpsVal}`}
                          </button>
                        )
                      })}
                    </div>
                  </div>

                  {/* FOV (Field of View) */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <span style={{ fontSize: '11px', color: '#cbd5e1', fontWeight: 600 }}>Угол обзора (FOV)</span>
                    <div style={{ display: 'flex', gap: '4px' }}>
                      {[
                        { val: 68, label: '68° Дефолт' },
                        { val: 90, label: '90° Pro' },
                        { val: 100, label: '100° Wide' },
                      ].map((f) => {
                        const isSelected = (clipSettings?.fov || 90) === f.val
                        return (
                          <button
                            key={f.val}
                            type="button"
                            className="btn card-interactive"
                            onClick={() => onUpdateSettings && clipSettings && onUpdateSettings({ ...clipSettings, fov: f.val })}
                            style={{
                              flex: 1,
                              padding: '4px 4px',
                              fontSize: '10px',
                              fontWeight: 700,
                              backgroundColor: isSelected ? '#38bdf8' : '#1c2333',
                              color: isSelected ? '#090d16' : '#cbd5e1',
                              border: '1px solid #2d3748',
                              borderRadius: '4px',
                              cursor: 'pointer',
                              whiteSpace: 'nowrap',
                            }}
                          >
                            {f.label}
                          </button>
                        )
                      })}
                    </div>
                  </div>
                </div>
              </div>

              {/* 3. RADAR / MINIMAP */}
              <div style={{ backgroundColor: '#12141c', padding: '14px', borderRadius: '8px', border: '1px solid #232734' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '8px' }}>
                  <div style={{ fontSize: '12px', fontWeight: 700, color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <RadarIcon size={14} color="#38bdf8" />
                    <span>МИНИ-КАРТА / 2D РАДАР</span>
                  </div>
                  <span style={{ fontSize: '11px', color: '#10b981', fontWeight: 600 }}>
                    {clipSettings?.radarMode === 'broadcast'
                      ? 'Турнирный BLAST'
                      : clipSettings?.radarMode === 'hidden'
                      ? 'Скрыт'
                      : 'Круглый (Слежение)'}
                  </span>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
                  {[
                    { id: 'player_focus', label: 'Круглый (Слежение)', desc: 'Центр на игроке, стандарт OBS' },
                    { id: 'broadcast', label: 'Турнирный BLAST', desc: 'Вся карта как на трансляциях' },
                    { id: 'hidden', label: 'Без радара', desc: 'Скрыт для чистого экрана' },
                  ].map((r) => {
                    const isSelected = (clipSettings?.radarMode || 'player_focus') === r.id
                    return (
                      <button
                        key={r.id}
                        type="button"
                        className="btn card-interactive"
                        onClick={() => onUpdateSettings && clipSettings && onUpdateSettings({ ...clipSettings, radarMode: r.id as any })}
                        style={{
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: 'flex-start',
                          padding: '8px 10px',
                          textAlign: 'left',
                          backgroundColor: isSelected ? 'rgba(16, 185, 129, 0.15)' : '#16181f',
                          borderColor: isSelected ? '#10b981' : '#282d3c',
                          borderWidth: '1px',
                          borderStyle: 'solid',
                          borderRadius: '6px',
                          cursor: 'pointer',
                        }}
                      >
                        <div style={{ fontSize: '11px', fontWeight: 700, color: isSelected ? '#34d399' : '#e2e8f0' }}>{r.label}</div>
                        <div style={{ fontSize: '9px', color: '#64748b', marginTop: '2px', lineHeight: '1.2' }}>{r.desc}</div>
                      </button>
                    )
                  })}
                </div>
              </div>

              {/* 4. TACTICAL TOGGLES LIST [ON / OFF] */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', backgroundColor: '#12141c', padding: '14px', borderRadius: '8px', border: '1px solid #232734' }}>
                <div style={{ fontSize: '12px', fontWeight: 700, color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                  <SlidersIcon size={14} color="#38bdf8" />
                  <span>ТАКТИЧЕСКИЕ ТУМБЛЕРЫ [ВКЛ / ВЫКЛ]</span>
                </div>

                {/* Switch 1: REAL OBS Mode */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 10px', backgroundColor: '#161922', borderRadius: '6px', border: '1px solid #232738' }}>
                  <div>
                    <div style={{ fontSize: '12px', color: '#f1f5f9', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <CameraIcon size={13} color="#38bdf8" />
                      <span>Режим REAL OBS (Вид живого матча)</span>
                    </div>
                    <div style={{ fontSize: '10px', color: '#94a3b8' }}>
                      1:1 как при живой игре: скрывает нижнюю спектатор-плашку и анимированные аватары
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '10px', fontWeight: 700, color: clipSettings?.hudMode === 'real' ? '#38bdf8' : '#64748b' }}>
                      {clipSettings?.hudMode === 'real' ? 'ВКЛ' : 'ВЫКЛ'}
                    </span>
                    <label className="toggle-switch">
                      <input
                        type="checkbox"
                        checked={clipSettings?.hudMode === 'real'}
                        onChange={(e) => {
                          if (onUpdateSettings && clipSettings) {
                            const isReal = e.target.checked
                            onUpdateSettings({
                              ...clipSettings,
                              hudMode: isReal ? 'real' : 'full',
                              hudScale: isReal ? 1.0 : (clipSettings.hudScale || 0.95),
                              ...(isReal ? { xray: false, radarMode: 'player_focus' } : {}),
                            })
                          }
                        }}
                      />
                      <span className="toggle-slider" />
                    </label>
                  </div>
                </div>

                {/* Switch 2: X-Ray */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 10px', backgroundColor: '#161922', borderRadius: '6px', border: '1px solid #232738' }}>
                  <div>
                    <div style={{ fontSize: '12px', color: '#f1f5f9', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <EyeIcon size={13} color="#38bdf8" />
                      <span>Силуэты сквозь стены (X-Ray)</span>
                    </div>
                    <div style={{ fontSize: '10px', color: '#94a3b8' }}>
                      Подсветка контуров игроков через препятствия (spec_show_xray)
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '10px', fontWeight: 700, color: clipSettings?.xray !== false ? '#38bdf8' : '#64748b' }}>
                      {clipSettings?.xray !== false ? 'ВКЛ' : 'ВЫКЛ'}
                    </span>
                    <label className="toggle-switch">
                      <input
                        type="checkbox"
                        checked={clipSettings?.xray !== false}
                        onChange={(e) => onUpdateSettings && clipSettings && onUpdateSettings({ ...clipSettings, xray: e.target.checked })}
                      />
                      <span className="toggle-slider" />
                    </label>
                  </div>
                </div>

                {/* Switch 3: Overhead Names */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 10px', backgroundColor: '#161922', borderRadius: '6px', border: '1px solid #232738' }}>
                  <div>
                    <div style={{ fontSize: '12px', color: '#f1f5f9', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <CrosshairIcon size={13} color="#38bdf8" />
                      <span>Ники над головами</span>
                    </div>
                    <div style={{ fontSize: '10px', color: '#94a3b8' }}>
                      Имена и шкала здоровья над персонажами (cl_teamid_overhead_mode)
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '10px', fontWeight: 700, color: clipSettings?.overheadMode !== false ? '#38bdf8' : '#64748b' }}>
                      {clipSettings?.overheadMode !== false ? 'ВКЛ' : 'ВЫКЛ'}
                    </span>
                    <label className="toggle-switch">
                      <input
                        type="checkbox"
                        checked={clipSettings?.overheadMode !== false}
                        onChange={(e) => onUpdateSettings && clipSettings && onUpdateSettings({ ...clipSettings, overheadMode: e.target.checked })}
                      />
                      <span className="toggle-slider" />
                    </label>
                  </div>
                </div>

                {/* Switch 4: Killfeed Only */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 10px', backgroundColor: '#161922', borderRadius: '6px', border: '1px solid #232738' }}>
                  <div>
                    <div style={{ fontSize: '12px', color: '#f1f5f9', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <SkullIcon size={13} color="#38bdf8" />
                      <span>Только Киллфид (Чистый экран)</span>
                    </div>
                    <div style={{ fontSize: '10px', color: '#94a3b8' }}>
                      Скрывает полосы патронов и HP, оставляя только уведомления о фрагах
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '10px', fontWeight: 700, color: clipSettings?.killfeedOnly ? '#38bdf8' : '#64748b' }}>
                      {clipSettings?.killfeedOnly ? 'ВКЛ' : 'ВЫКЛ'}
                    </span>
                    <label className="toggle-switch">
                      <input
                        type="checkbox"
                        checked={Boolean(clipSettings?.killfeedOnly)}
                        onChange={(e) => onUpdateSettings && clipSettings && onUpdateSettings({ ...clipSettings, killfeedOnly: e.target.checked })}
                      />
                      <span className="toggle-slider" />
                    </label>
                  </div>
                </div>

                {/* Switch 5: 5v3 Counter */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 10px', backgroundColor: '#161922', borderRadius: '6px', border: '1px solid #232738' }}>
                  <div>
                    <div style={{ fontSize: '12px', color: '#f1f5f9', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <ActivityIcon size={13} color="#38bdf8" />
                      <span>Счётчик живых (5 v 3 цифрами)</span>
                    </div>
                    <div style={{ fontSize: '10px', color: '#94a3b8' }}>
                      Компактные цифры счета живых игроков сверху вместо больших аватаров
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '10px', fontWeight: 700, color: clipSettings?.teamcounterMode ? '#38bdf8' : '#64748b' }}>
                      {clipSettings?.teamcounterMode ? 'ВКЛ' : 'ВЫКЛ'}
                    </span>
                    <label className="toggle-switch">
                      <input
                        type="checkbox"
                        checked={Boolean(clipSettings?.teamcounterMode)}
                        onChange={(e) => onUpdateSettings && clipSettings && onUpdateSettings({ ...clipSettings, teamcounterMode: e.target.checked })}
                      />
                      <span className="toggle-slider" />
                    </label>
                  </div>
                </div>

                {/* Switch 6: Watermark */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 10px', backgroundColor: '#161922', borderRadius: '6px', border: '1px solid #232738' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <img
                      src="/logo_video.png"
                      alt="dem.Toshka"
                      style={{ height: '18px', maxWidth: '55px', objectFit: 'contain' }}
                    />
                    <div>
                      <div style={{ fontSize: '12px', color: '#f1f5f9', fontWeight: 600 }}>Водяной знак dem.Toshka</div>
                      <div style={{ fontSize: '10px', color: '#94a3b8' }}>Фирменный полупрозрачный логотип слева сверху</div>
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '10px', fontWeight: 700, color: clipSettings?.watermark !== false ? '#38bdf8' : '#64748b' }}>
                      {clipSettings?.watermark !== false ? 'ВКЛ' : 'ВЫКЛ'}
                    </span>
                    <label className="toggle-switch">
                      <input
                        type="checkbox"
                        checked={clipSettings?.watermark !== false}
                        onChange={(e) => onUpdateSettings && clipSettings && onUpdateSettings({ ...clipSettings, watermark: e.target.checked })}
                      />
                      <span className="toggle-slider" />
                    </label>
                  </div>
                </div>

                {/* Switch 7: Preview Recording Window & Sound */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 10px', backgroundColor: '#161922', borderRadius: '6px', border: '1px solid #232738' }}>
                  <div>
                    <div style={{ fontSize: '12px', color: '#f1f5f9', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
                      {clipSettings?.previewRecording !== false ? <VolumeIcon size={13} color="#38bdf8" /> : <VolumeMuteIcon size={13} color="#94a3b8" />}
                      <span>Окно CS2 и звук записи</span>
                    </div>
                    <div style={{ fontSize: '10px', color: '#94a3b8' }}>
                      {clipSettings?.previewRecording !== false ? 'Окно игры открыто, звук включен' : 'Тихий фоновый режим без звука CS2'}
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '10px', fontWeight: 700, color: clipSettings?.previewRecording !== false ? '#38bdf8' : '#64748b' }}>
                      {clipSettings?.previewRecording !== false ? 'ВКЛ' : 'ТИХИЙ'}
                    </span>
                    <label className="toggle-switch">
                      <input
                        type="checkbox"
                        checked={clipSettings?.previewRecording !== false}
                        onChange={(e) => onUpdateSettings && clipSettings && onUpdateSettings({ ...clipSettings, previewRecording: e.target.checked })}
                      />
                      <span className="toggle-slider" />
                    </label>
                  </div>
                </div>
              </div>

              {/* 5. HUD SCALE & CROSSHAIR */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', backgroundColor: '#12141c', padding: '14px', borderRadius: '8px', border: '1px solid #232734' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ fontSize: '12px', fontWeight: 700, color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <CrosshairIcon size={14} color="#38bdf8" />
                    <span>РАЗМЕР HUD И ПРИЦЕЛ</span>
                  </div>
                  <button
                    type="button"
                    className="btn card-interactive"
                    onClick={() => setIsTournamentHudModalOpen(true)}
                    style={{
                      padding: '3px 8px',
                      fontSize: '10px',
                      backgroundColor: 'rgba(245, 158, 11, 0.15)',
                      color: '#fbbf24',
                      border: '1px solid rgba(245, 158, 11, 0.4)',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontWeight: 600,
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                    }}
                  >
                    <TrophyIcon size={11} color="#fbbf24" />
                    <span>Турнирный HUD (GSI)...</span>
                  </button>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  {/* HUD Scale */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <span style={{ fontSize: '11px', color: '#cbd5e1', fontWeight: 600 }}>Размер HUD</span>
                    <div style={{ display: 'flex', gap: '4px' }}>
                      {[
                        { scale: 0.95, label: '95% Компакт' },
                        { scale: 1.0, label: '100% 1:1' },
                        { scale: 1.15, label: '115% Кибер' },
                      ].map((s) => (
                        <button
                          key={s.scale}
                          type="button"
                          className="btn card-interactive"
                          onClick={() => onUpdateSettings && clipSettings && onUpdateSettings({ ...clipSettings, hudScale: s.scale })}
                          style={{
                            flex: 1,
                            padding: '4px 4px',
                            fontSize: '10px',
                            fontWeight: 700,
                            borderRadius: '4px',
                            border: '1px solid #2d3748',
                            backgroundColor: clipSettings?.hudScale === s.scale ? '#38bdf8' : '#1c2333',
                            color: clipSettings?.hudScale === s.scale ? '#090d16' : '#cbd5e1',
                            cursor: 'pointer',
                            whiteSpace: 'nowrap',
                          }}
                        >
                          {s.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Crosshair Preset */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <span style={{ fontSize: '11px', color: '#cbd5e1', fontWeight: 600 }}>Прицел в CS2</span>
                    <div style={{ display: 'flex', gap: '4px' }}>
                      {[
                        { p: 'default', label: 'Дефолт' },
                        { p: 'pro_cyan', label: 'Pro Цветной' },
                        { p: 'hidden', label: 'Скрыт' },
                      ].map((c) => {
                        const isSelected = (clipSettings?.crosshairPreset || 'default') === c.p
                        return (
                          <button
                            key={c.p}
                            type="button"
                            className="btn card-interactive"
                            onClick={() =>
                              onUpdateSettings &&
                              clipSettings &&
                              onUpdateSettings({
                                ...clipSettings,
                                crosshairPreset: c.p as any,
                                customCrosshair: c.p !== 'default' && c.p !== 'hidden',
                              })
                            }
                            style={{
                              flex: 1,
                              padding: '4px 4px',
                              fontSize: '10px',
                              fontWeight: 700,
                              borderRadius: '4px',
                              border: '1px solid #2d3748',
                              backgroundColor: isSelected ? '#38bdf8' : '#1c2333',
                              color: isSelected ? '#090d16' : '#cbd5e1',
                              cursor: 'pointer',
                              whiteSpace: 'nowrap',
                            }}
                          >
                            {c.label}
                          </button>
                        )
                      })}
                    </div>
                  </div>
                </div>

                {/* Crosshair Color selection if Pro */}
                {clipSettings?.crosshairPreset !== 'default' && clipSettings?.crosshairPreset !== 'hidden' && (
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 10px', backgroundColor: '#0d1017', borderRadius: '6px', border: '1px solid #1e2433', marginTop: '2px' }}>
                    <span style={{ fontSize: '11px', color: '#94a3b8' }}>Цвет прицела:</span>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      {[
                        { name: 'cyan', hex: '#00ffff' },
                        { name: 'green', hex: '#00ff00' },
                        { name: 'yellow', hex: '#ffff00' },
                        { name: 'white', hex: '#ffffff' },
                        { name: 'pink', hex: '#ff00ff' },
                      ].map((col) => (
                        <button
                          key={col.name}
                          type="button"
                          onClick={() => onUpdateSettings && clipSettings && onUpdateSettings({ ...clipSettings, crosshairColor: col.name as any })}
                          style={{
                            width: '18px',
                            height: '18px',
                            borderRadius: '50%',
                            backgroundColor: col.hex,
                            border: (clipSettings?.crosshairColor || 'cyan') === col.name ? '2px solid #ffffff' : '1px solid #334155',
                            cursor: 'pointer',
                            outline: (clipSettings?.crosshairColor || 'cyan') === col.name ? '2px solid #38bdf8' : 'none',
                          }}
                          title={col.name}
                        />
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Column: Interactive Crosshair Preview & Montage Summary */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* Live Interactive CS2 Viewport & Crosshair Simulator */}
            <InteractiveCrosshairPreview
              config={{
                preset: clipSettings?.crosshairPreset || 'pro_cyan',
                color: clipSettings?.crosshairColor || 'cyan',
                fov: clipSettings?.fov || 90,
                viewmodelFov: clipSettings?.viewmodelFov || 60,
                hudMode: clipSettings?.hudMode || 'full',
                customCrosshair: clipSettings?.customCrosshair,
              }}
              onChangeConfig={(newCfg) => {
                if (onUpdateSettings && clipSettings) {
                  onUpdateSettings({
                    ...clipSettings,
                    crosshairColor: (newCfg.color as any) || clipSettings.crosshairColor,
                  })
                }
              }}
            />

            <div
              style={{
                backgroundColor: '#16181f',
                border: '1px solid #232630',
                borderRadius: '10px',
                padding: '20px',
              }}
            >

              {/* Recording Mode / Sound & Window Live Toggle */}
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  backgroundColor: '#0f1219',
                  border: '1px solid #232938',
                  borderRadius: '8px',
                  padding: '10px 14px',
                  marginBottom: '16px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '32px', height: '32px', borderRadius: '8px', backgroundColor: clipSettings?.previewRecording !== false ? 'rgba(56, 189, 248, 0.15)' : 'rgba(100, 116, 139, 0.15)' }}>
                    {clipSettings?.previewRecording !== false ? (
                      <VolumeIcon size={18} color="#38bdf8" />
                    ) : (
                      <VolumeMuteIcon size={18} color="#94a3b8" />
                    )}
                  </div>
                  <div>
                    <div style={{ fontSize: '12px', fontWeight: 700, color: '#f1f5f9' }}>
                      {clipSettings?.previewRecording !== false
                        ? 'Режим записи: Видеть и слышать CS2'
                        : 'Режим записи: Тихий фоновый'}
                    </div>
                    <div style={{ fontSize: '11px', color: '#64748b' }}>
                      {clipSettings?.previewRecording !== false
                        ? 'Окно игры открыто на экране, воспроизводятся звуки выстрелов и эффекты'
                        : 'Звук CS2 отключен (volume 0), чтобы не мешать работе за ПК'}
                    </div>
                  </div>
                </div>

                <button
                  type="button"
                  className="card-interactive"
                  onClick={() => {
                    if (onUpdateSettings && clipSettings) {
                      onUpdateSettings({
                        ...clipSettings,
                        previewRecording: clipSettings.previewRecording === false,
                      })
                    }
                  }}
                  style={{
                    backgroundColor: clipSettings?.previewRecording !== false ? 'rgba(56, 189, 248, 0.15)' : 'rgba(100, 116, 139, 0.15)',
                    border: `1px solid ${clipSettings?.previewRecording !== false ? '#38bdf8' : '#475569'}`,
                    color: clipSettings?.previewRecording !== false ? '#38bdf8' : '#94a3b8',
                    padding: '6px 12px',
                    borderRadius: '6px',
                    fontSize: '11px',
                    fontWeight: 700,
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px',
                  }}
                >
                  {clipSettings?.previewRecording !== false ? (
                    <>
                      <VolumeIcon size={13} color="#38bdf8" />
                      <span>Звук и Окно: ВКЛ</span>
                    </>
                  ) : (
                    <>
                      <VolumeMuteIcon size={13} color="#94a3b8" />
                      <span>Тихий режим</span>
                    </>
                  )}
                </button>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <div>
                  <div style={{ fontSize: '15px', fontWeight: 700, color: '#f1f5f9' }}>
                    Мы создадим нарезку из {selectedHighlights.length} {selectedHighlights.length === 1 ? 'момента' : 'моментов'}
                  </div>
                  <div style={{ fontSize: '12px', color: '#64748b', marginTop: '2px' }}>
                    Примерное время генерации: ~{Math.max(1, Math.ceil(selectedHighlights.length * 0.8))} минут
                  </div>
                </div>

                <button
                  type="button"
                  className="btn btn-accent card-interactive"
                  onClick={handleStartMontageCreation}
                  disabled={isCompiling || selectedHighlights.length === 0}
                  style={{ padding: '8px 20px', fontSize: '13px', fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: '8px' }}
                >
                  {isCompiling ? (
                    <>
                      <LoaderIcon size={13} color="#090d16" />
                      <span>Запись...</span>
                    </>
                  ) : (
                    <>
                      <FilmIcon size={13} color="#090d16" />
                      <span>Создать нарезку</span>
                    </>
                  )}
                </button>
              </div>

              {/* In-progress compilation status and progress bar */}
              {isCompiling && (
                <div
                  style={{
                    padding: '14px 16px',
                    backgroundColor: 'rgba(56, 189, 248, 0.08)',
                    border: '1px solid rgba(56, 189, 248, 0.25)',
                    borderRadius: '8px',
                    marginBottom: '16px',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <span style={{ fontSize: '12px', fontWeight: 600, color: '#38bdf8', display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                      <LoaderIcon size={12} color="#38bdf8" />
                      <span>{compilationStatus || 'Идет обработка...'}</span>
                    </span>
                    <button
                      type="button"
                      onClick={onOpenQueue}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: '#94a3b8',
                        textDecoration: 'underline',
                        cursor: 'pointer',
                        fontSize: '11px',
                      }}
                    >
                      Открыть очередь
                    </button>
                  </div>
                  <div
                    style={{
                      height: '6px',
                      backgroundColor: '#1e293b',
                      borderRadius: '3px',
                      overflow: 'hidden',
                    }}
                  >
                    <div
                      style={{
                        height: '100%',
                        width: `${compilationProgress}%`,
                        backgroundColor: '#38bdf8',
                        transition: 'width 0.4s ease',
                      }}
                    />
                  </div>
                </div>
              )}

              {compilationError && (
                <div style={{ padding: '10px 14px', backgroundColor: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.3)', borderRadius: '6px', color: '#fbbf24', fontSize: '12px', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <WarningIcon size={13} color="#fbbf24" />
                  <span>{compilationError}</span>
                </div>
              )}

              {/* Compiled Video Player Banner */}
              {compiledMontage && (
                <div style={{ marginBottom: '20px', padding: '14px', backgroundColor: '#101217', borderRadius: '8px', border: '1px solid #22c55e' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <span style={{ fontSize: '13px', fontWeight: 700, color: '#4ade80', display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                        <CheckIcon size={13} color="#4ade80" />
                        <span>Готовый ролик: {compiledMontage.filename}</span>
                      </span>
                      <span style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginTop: '2px' }}>
                        Длительность: {compiledMontage.duration_seconds.toFixed(1)} с • {compiledMontage.total_clips} клипов • 1080p60 H.264
                      </span>
                    </div>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button
                        type="button"
                        className="btn btn-primary card-interactive"
                        onClick={() =>
                          setActiveModalVideo({
                            url: `/api/montage/${compiledMontage.filename}`,
                            title: compiledMontage.filename,
                            subtitle: `Монтаж (${compiledMontage.duration_seconds.toFixed(1)} с, ${compiledMontage.total_clips} клипов)`,
                          })
                        }
                        style={{ padding: '6px 14px', fontSize: '12px', display: 'inline-flex', alignItems: 'center', gap: '6px' }}
                      >
                        <PlayIcon size={11} color="#090d16" />
                        <span>Смотреть в плеере</span>
                      </button>
                      <a
                        href={`/api/montage/${compiledMontage.filename}`}
                        download
                        className="btn btn-secondary card-interactive"
                        style={{ padding: '6px 12px', fontSize: '12px', textDecoration: 'none' }}
                      >
                        ⬇ Скачать MP4
                      </a>
                    </div>
                  </div>
                </div>
              )}

              {/* Table of selected moments */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '440px', overflowY: 'auto' }}>
                {selectedHighlights.map((h, i) => {
                  const kill = getHighlightKillDetails(h)
                  const killer = kill?.attacker_name || h.pov_name || 'Player'
                  const victim = kill?.victim_name || 'Opponent'
                  const weapon = cleanWeaponName(kill?.weapon)

                  return (
                    <div
                      key={h.id}
                      style={{
                        display: 'grid',
                        gridTemplateColumns: '32px 60px 80px 1fr auto',
                        alignItems: 'center',
                        gap: '10px',
                        padding: '8px 12px',
                        backgroundColor: '#121316',
                        border: '1px solid #22252e',
                        borderRadius: '6px',
                        fontSize: '12px',
                      }}
                    >
                      <span style={{ color: '#64748b', fontWeight: 700 }}>#{i + 1}</span>
                      <span style={{ backgroundColor: '#1c1f28', padding: '2px 6px', borderRadius: '4px', fontWeight: 700, textAlign: 'center' }}>
                        Р {h.round_num}
                      </span>
                      <span style={{ color: '#94a3b8', fontFamily: 'monospace' }}>
                        {formatRoundTime(h.kill_start_tick)}
                      </span>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span style={{ fontWeight: 600, color: '#f1f5f9' }}>{killer}</span>
                        <span style={{ color: '#fbbf24', fontSize: '11px' }}>[{weapon}]</span>
                        {kill?.headshot && <CrosshairIcon size={12} color="#ef4444" />}
                        <span style={{ color: '#94a3b8' }}>→ {victim}</span>
                      </div>
                      <span style={{ fontSize: '10px', fontWeight: 700, color: '#38bdf8' }}>
                        {h.highlight_type.replace('multikill_', '').toUpperCase()}
                      </span>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Advanced Video Player Modal with timeline and frame scrubbing */}
      <VideoPlayerModal
        isOpen={!!activeModalVideo}
        onClose={() => setActiveModalVideo(null)}
        videoUrl={activeModalVideo?.url || ''}
        title={activeModalVideo?.title || 'Нарезка матча'}
        subtitle={activeModalVideo?.subtitle}
      />

      {/* External Tournament HUD & Overlays Modal (Lexogrine / GSI) */}
      <TournamentHudModal
        isOpen={isTournamentHudModalOpen}
        onClose={() => setIsTournamentHudModalOpen(false)}
      />

      {/* In-depth FACEIT Analytics & Tactical Error Audit Modal */}
      {selectedPlayerForAnalytics && activeDemo && (
        <PlayerAnalyticsModal
          demoId={activeDemo.id}
          playerIdentifier={selectedPlayerForAnalytics.steamIdOrName}
          playerName={selectedPlayerForAnalytics.name}
          playerTeam={selectedPlayerForAnalytics.team}
          onClose={() => setSelectedPlayerForAnalytics(null)}
          onViewHighlights={(steamId) => {
            setSelectedPlayerForAnalytics(null)
            onSetPlayerFilter(steamId)
            setCurrentStep(3)
          }}
        />
      )}
    </div>
  )

}
