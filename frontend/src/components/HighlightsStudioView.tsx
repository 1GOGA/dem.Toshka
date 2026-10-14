import React, { useState, useMemo, useRef, useEffect } from 'react'
import type { ClipSettings, DemoSummary, HighlightItem, KillDTO, MontageDTO, PlayerDTO } from '../types'
import { Map2DRadar } from './Map2DRadar'
import { api } from '../api'
import { VideoPlayerModal } from './VideoPlayerModal'
import { TournamentHudModal } from './TournamentHudModal'
import { PlayerAnalyticsModal } from './PlayerAnalyticsModal'
import { Agent3DViewer } from './Agent3DViewer'
import { InteractiveCrosshairPreview } from './InteractiveCrosshairPreview'



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
  onUploadDemo,
  onParsePath,
}) => {
  // 4-step wizard: 1 = Choose match, 2 = Choose player, 3 = Choose moments (2D Map), 4 = Compile montage
  const [currentStep, setCurrentStep] = useState<1 | 2 | 3 | 4>(activeDemo ? 2 : 1)
  const [hoveredHighlightId, setHoveredHighlightId] = useState<string | null>(null)
  const [weaponFilter, setWeaponFilter] = useState<string | null>(null)
  const [aspectRatio, setAspectRatio] = useState<'16:9' | '4:3'>('16:9')
  const [step4Tab, setStep4Tab] = useState<'screen' | 'radar' | 'hud' | 'camera'>('screen')

  // Drag & drop demo state
  const [isDraggingFile, setIsDraggingFile] = useState(false)
  const [localPathInput, setLocalPathInput] = useState('')
  const [isIngestingDemo, setIsIngestingDemo] = useState(false)
  const fileInputRef = useRef<HTMLInputElement | null>(null)

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

  // Map rounds
  const rounds = useMemo(() => {
    const set = new Set<number>()
    highlights.forEach((h) => set.add(h.round_num))
    return Array.from(set).sort((a, b) => a - b)
  }, [highlights])


  // Correlate kills for each highlight
  const getHighlightKillDetails = (h: HighlightItem) => {
    if (!kills || kills.length === 0) return null
    const matched = kills.filter(
      (k) => k.round_num === h.round_num && k.tick >= h.kill_start_tick && k.tick <= h.kill_end_tick + 128
    )
    return matched.length > 0 ? matched[0] : null
  }

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
  }, [highlights, activePlayerFilter, activeTypeFilter, activeRoundFilter, weaponFilter, kills])

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
    <div style={{ maxWidth: '1360px', margin: '0 auto', padding: '24px 20px' }}>
      {/* Studio Header & Stepper */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '320px 1fr',
          gap: '32px',
          alignItems: 'start',
          marginBottom: '28px',
        }}
      >
        {/* Left Column: Title & Steps */}
        <div>
          <h1 style={{ fontSize: '26px', fontWeight: 800, color: '#f1f5f9', marginBottom: '8px', letterSpacing: '-0.02em' }}>
            Студия нарезок
          </h1>
          <p style={{ fontSize: '13px', color: '#94a3b8', lineHeight: 1.5, marginBottom: '20px' }}>
            Создавай нарезки из любимых моментов матча за пару кликов. Мы запишем и объединим выбранные моменты в единый плавный ролик.
          </p>

          {/* Stepper Wizard List */}
          <div className="studio-stepper">
            <div
              className={`studio-step-item ${currentStep === 1 ? 'active' : currentStep > 1 ? 'completed' : ''}`}
              onClick={() => setCurrentStep(1)}
              style={{ cursor: 'pointer' }}
            >
              <span className="studio-step-badge">Шаг 1</span>
              <span>Выбор демки</span>
            </div>
            <div
              className={`studio-step-item ${currentStep === 2 ? 'active' : currentStep > 2 ? 'completed' : ''}`}
              onClick={() => activeDemo && setCurrentStep(2)}
              style={{ opacity: activeDemo ? 1 : 0.4, cursor: activeDemo ? 'pointer' : 'default' }}
            >
              <span className="studio-step-badge">Шаг 2</span>
              <span>Выбор игрока</span>
            </div>
            <div
              className={`studio-step-item ${currentStep === 3 ? 'active' : currentStep > 3 ? 'completed' : ''}`}
              onClick={() => activeDemo && setCurrentStep(3)}
              style={{ opacity: activeDemo ? 1 : 0.4, cursor: activeDemo ? 'pointer' : 'default' }}
            >
              <span className="studio-step-badge">Шаг 3</span>
              <span>Моменты и 2D Радар</span>
            </div>
            <div
              className={`studio-step-item ${currentStep === 4 ? 'active' : ''}`}
              onClick={() => activeDemo && selectedIds.size > 0 && setCurrentStep(4)}
              style={{ opacity: activeDemo && selectedIds.size > 0 ? 1 : 0.4, cursor: activeDemo && selectedIds.size > 0 ? 'pointer' : 'default' }}
            >
              <span className="studio-step-badge">Шаг 4</span>
              <span>Сборка и Запись</span>
            </div>
          </div>
        </div>

        {/* Right Column: Step Actions / Breadcrumbs */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: '12px' }}>
          {currentStep === 2 && (
            <>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setCurrentStep(1)}
                style={{ padding: '8px 16px', fontSize: '13px', fontWeight: 600 }}
              >
                ← Назад к матчам
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => {
                  onSetPlayerFilter(null)
                  setCurrentStep(3)
                }}
                style={{ padding: '8px 16px', fontSize: '13px', fontWeight: 600 }}
              >
                Все игроки (Пропустить) →
              </button>
            </>
          )}

          {currentStep === 3 && (
            <>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setCurrentStep(2)}
                style={{ padding: '8px 16px', fontSize: '13px', fontWeight: 600 }}
              >
                ← Назад к выбору игрока
              </button>
              <button
                type="button"
                className="btn btn-success"
                onClick={() => setCurrentStep(4)}
                disabled={selectedIds.size === 0}
                style={{ padding: '8px 20px', fontSize: '13px', fontWeight: 700 }}
              >
                Далее: Сборка и Настройки ({selectedIds.size}) →
              </button>
            </>
          )}

          {currentStep === 4 && (
            <>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setCurrentStep(3)}
                style={{ padding: '8px 16px', fontSize: '13px', fontWeight: 600 }}
              >
                ← Назад к выбору моментов
              </button>
              <button
                type="button"
                className="btn btn-accent"
                onClick={handleStartMontageCreation}
                disabled={isCompiling || selectedIds.size === 0}
                style={{ padding: '8px 22px', fontSize: '13px', fontWeight: 700 }}
              >
                {isCompiling ? '⏳ Запись и сборка...' : `🎬 Создать нарезку (${selectedIds.size})`}
              </button>
            </>
          )}

          {onOpenQueue && (
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onOpenQueue}
              style={{ padding: '8px 14px', fontSize: '12px' }}
            >
              🎞 Очередь / Монтаж
            </button>
          )}
        </div>
      </div>

      {/* ==================================================================== */}
      {/* STEP 1: CHOOSE MATCH                                                 */}
      {/* ==================================================================== */}
      {currentStep === 1 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Drag & Drop Upload Zone */}
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
              backgroundColor: isDraggingFile ? 'rgba(56, 189, 248, 0.08)' : '#16181f',
              borderRadius: '12px',
              padding: '28px 20px',
              textAlign: 'center',
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
            <div style={{ fontSize: '32px', marginBottom: '8px' }}>📂</div>
            <div style={{ fontSize: '15px', fontWeight: 700, color: '#f1f5f9', marginBottom: '4px' }}>
              {isIngestingDemo ? '⏳ Загрузка и анализ демки CS2...' : 'Перетащите .dem файл сюда или нажмите для выбора'}
            </div>
            <div style={{ fontSize: '12px', color: '#94a3b8' }}>
              Поддерживаются официальные демки CS2 (Matchmaking, Premier, Faceit, HLTV)
            </div>
          </div>

          {/* Local Path Input Row */}
          <form
            onSubmit={async (e) => {
              e.preventDefault()
              if (localPathInput.trim() && onParsePath) {
                setIsIngestingDemo(true)
                try {
                  await onParsePath(localPathInput.trim())
                  setCurrentStep(2)
                } finally {
                  setIsIngestingDemo(false)
                }
              }
            }}
            style={{ display: 'flex', gap: '10px' }}
          >
            <input
              type="text"
              value={localPathInput}
              onChange={(e) => setLocalPathInput(e.target.value)}
              placeholder="Или укажите локальный путь: C:\CS2\match.dem"
              disabled={isIngestingDemo}
              style={{
                flex: 1,
                backgroundColor: '#16181f',
                border: '1px solid #232630',
                borderRadius: '8px',
                padding: '10px 14px',
                color: '#f1f5f9',
                fontSize: '13px',
              }}
            />
            <button
              type="submit"
              className="btn btn-secondary"
              disabled={isIngestingDemo || !localPathInput.trim()}
              style={{ padding: '10px 18px', fontSize: '13px', whiteSpace: 'nowrap' }}
            >
              {isIngestingDemo ? 'Анализ...' : 'Проанализировать путь'}
            </button>
          </form>

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
                          <div style={{ fontSize: '11px', color: '#64748b' }}>{d.tickrate} Tickrate</div>
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
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                        <span>🎮</span> Valve CS2
                      </span>
                    </td>
                    <td style={{ padding: '14px 16px', color: '#f1f5f9', fontWeight: 600 }}>
                      ⭐ {d.highlights_count} моментов
                    </td>
                    <td style={{ padding: '14px 20px', textAlign: 'right' }}>
                      <button
                        type="button"
                        className="btn btn-primary"
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
      {/* STEP 2: CHOOSE PLAYER                                                */}
      {/* ==================================================================== */}
      {currentStep === 2 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h2 style={{ fontSize: '18px', fontWeight: 700, color: '#f1f5f9', margin: '0 0 4px 0' }}>
                Выберите игрока для нарезки
              </h2>
              <div style={{ fontSize: '13px', color: '#94a3b8' }}>
                Матч: {(activeDemo?.map_name || 'Match').replace('de_', '').toUpperCase()} • Выберите игрока для фильтрации хайлайтов и отображения на 2D радаре
              </div>
            </div>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => setCurrentStep(1)}
              style={{ fontSize: '12px', padding: '6px 12px' }}
            >
              ← Сменить матч
            </button>
          </div>

          {/* 3D Agent Inspector Showcase Banner */}
          {inspectedPlayer && (
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '320px 1fr',
                gap: '24px',
                backgroundColor: '#12151e',
                border: `1px solid ${(inspectedPlayer.team || '').toLowerCase().includes('ct') ? 'rgba(56, 189, 248, 0.4)' : 'rgba(245, 158, 11, 0.4)'}`,
                borderRadius: '16px',
                padding: '20px',
                alignItems: 'center',
                boxShadow: '0 12px 35px rgba(0, 0, 0, 0.5)',
              }}
            >
              <Agent3DViewer
                team={inspectedPlayer.team}
                playerName={inspectedPlayer.name}
                role={(inspectedPlayer.team || '').toLowerCase().includes('ct') ? 'CT Specialist (Defense)' : 'Terrorist Operative (Attack)'}
                height={260}
                weapon={(inspectedPlayer.team || '').toLowerCase().includes('ct') ? 'M4A1-S' : 'AK-47'}
              />

              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span
                    style={{
                      fontSize: '11px',
                      fontWeight: 800,
                      letterSpacing: '0.06em',
                      padding: '3px 10px',
                      borderRadius: '5px',
                      backgroundColor: (inspectedPlayer.team || '').toLowerCase().includes('ct') ? 'rgba(56, 189, 248, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                      color: (inspectedPlayer.team || '').toLowerCase().includes('ct') ? '#38bdf8' : '#f59e0b',
                      border: `1px solid ${(inspectedPlayer.team || '').toLowerCase().includes('ct') ? 'rgba(56, 189, 248, 0.4)' : 'rgba(245, 158, 11, 0.4)'}`,
                    }}
                  >
                    🛡️ 3D ИНСПЕКТОР АГЕНТА CS2
                  </span>
                  <span style={{ fontSize: '12px', color: '#64748b' }}>
                    Наведите курсор на любого игрока в списке для смены 3D модели
                  </span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <h3 style={{ fontSize: '22px', fontWeight: 800, color: '#f1f5f9', margin: 0 }}>
                    {inspectedPlayer.name}
                  </h3>
                  <span
                    style={{
                      fontSize: '11px',
                      fontWeight: 700,
                      padding: '2px 8px',
                      borderRadius: '4px',
                      backgroundColor: (inspectedPlayer.team || '').toLowerCase().includes('ct') ? 'rgba(56, 189, 248, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                      color: (inspectedPlayer.team || '').toLowerCase().includes('ct') ? '#38bdf8' : '#f59e0b',
                    }}
                  >
                    {(inspectedPlayer.team || '').toUpperCase()}
                  </span>
                </div>

                <div style={{ fontSize: '13px', color: '#94a3b8' }}>
                  Сыграно раундов: <strong>{activeDemo?.rounds_count || 0}</strong> • Ключевых фраг-эпизодов в матче:{' '}
                  <strong style={{ color: '#fbbf24' }}>
                    {highlights.filter((h) => h.pov_steam_id === inspectedPlayer.steam_id).length}
                  </strong>
                </div>

                <div style={{ display: 'flex', gap: '12px', marginTop: '6px' }}>
                  <button
                    type="button"
                    className="btn btn-primary"
                    style={{ padding: '8px 20px', fontSize: '13px', fontWeight: 700 }}
                    onClick={() => {
                      onSetPlayerFilter(inspectedPlayer.steam_id)
                      setCurrentStep(3)
                    }}
                  >
                    Выбрать {inspectedPlayer.name} для нарезки →
                  </button>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    style={{ padding: '8px 16px', fontSize: '12px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}
                    onClick={() =>
                      setSelectedPlayerForAnalytics({
                        steamIdOrName: inspectedPlayer.steam_id || inspectedPlayer.name,
                        name: inspectedPlayer.name,
                        team: inspectedPlayer.team,
                      })
                    }
                  >
                    <span>📊</span> FACEIT Анализ & Ошибки
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* All Players Card */}
          <div
            onClick={() => {
              onSetPlayerFilter(null)
              setCurrentStep(3)
            }}
            style={{
              backgroundColor: '#16181f',
              border: activePlayerFilter === null ? '2px solid #38bdf8' : '1px solid #232630',
              borderRadius: '10px',
              padding: '16px 20px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              cursor: 'pointer',
              transition: 'all 0.15s ease',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
              <div
                style={{
                  width: '42px',
                  height: '42px',
                  borderRadius: '10px',
                  background: 'linear-gradient(135deg, #f59e0b, #ef4444)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '20px',
                }}
              >
                🔥
              </div>
              <div>
                <div style={{ fontWeight: 700, fontSize: '14px', color: '#f1f5f9' }}>
                  Все игроки матча
                </div>
                <div style={{ fontSize: '12px', color: '#94a3b8' }}>
                  Общий обзор всех ключевых моментов ({highlights.length} хайлайтов со всех игроков)
                </div>
              </div>
            </div>
            <button type="button" className="btn btn-primary" style={{ padding: '6px 16px', fontSize: '12px' }}>
              Выбрать всех →
            </button>
          </div>

          {/* Player Cards Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '14px' }}>
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
                    borderRadius: '10px',
                    padding: '16px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '12px',
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
                              }}
                            >
                              ⭐ ВЫ
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
                      <span style={{ backgroundColor: 'rgba(245, 158, 11, 0.15)', color: '#fbbf24', padding: '1px 6px', borderRadius: '4px', fontWeight: 600 }}>
                        ⭐ {pAces} ACE
                      </span>
                    )}
                    {pMultikills > 0 && (
                      <span style={{ backgroundColor: 'rgba(139, 92, 246, 0.15)', color: '#c084fc', padding: '1px 6px', borderRadius: '4px', fontWeight: 600 }}>
                        🎯 {pMultikills} Мультикилл
                      </span>
                    )}
                    {pClutches > 0 && (
                      <span style={{ backgroundColor: 'rgba(16, 185, 129, 0.15)', color: '#34d399', padding: '1px 6px', borderRadius: '4px', fontWeight: 600 }}>
                        ⚡ {pClutches} Клатч
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
                      className="btn btn-secondary"
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
                      title={`Подробный разбор ошибок и FACEIT аналитика для ${p.name}`}
                    >
                      <span>📊</span> Разбор & Ошибки
                    </button>
                    <button
                      type="button"
                      className="btn btn-primary"
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
        <div style={{ display: 'grid', gridTemplateColumns: '480px 1fr', gap: '24px', alignItems: 'start' }}>
          {/* Left Column: 2D Tactical Radar Map */}
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
            <div style={{ marginTop: '14px', padding: '12px 14px', backgroundColor: '#16181f', border: '1px solid #232630', borderRadius: '8px', fontSize: '12px', color: '#94a3b8' }}>
              💡 Кликните на маркер фраг-эпизода на 2D радаре для выбора, или наведите курсор для предпросмотра позиции.
            </div>
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
                    className="btn btn-secondary"
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
                    title="Открыть FACEIT аналитику и тактический аудит ошибок выбранного игрока"
                  >
                    <span>📊</span> Разбор игрока
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
                  <option value="all">Все раунды ({rounds.length})</option>
                  {rounds.map((r) => (
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
                  className="btn btn-secondary"
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
                          className="btn btn-primary"
                          style={{ padding: '6px 14px', fontSize: '11px', backgroundColor: teamColor, color: '#090d16', border: 'none', fontWeight: 700 }}
                          onClick={() => {
                            playerHighlights.forEach((h) => {
                              if (!selectedIds.has(h.id)) onToggleHighlight(h.id)
                            })
                            onSetPlayerFilter(selectedPlayer.name)
                            setCurrentStep(3)
                          }}
                        >
                          ✨ Выбрать моменты {selectedPlayer.name} ({playerHighlights.length}) →
                        </button>
                      )}
                      <button
                        type="button"
                        className="btn btn-secondary"
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
                      onClick={() => onToggleHighlight(h.id)}
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
                          <span title="Headshot" style={{ fontSize: '12px' }}>🎯</span>
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
                          className="btn btn-secondary"
                          onClick={(e) => {
                            e.stopPropagation()
                            if (!selectedIds.has(h.id)) {
                              onToggleHighlight(h.id)
                            }
                            setCurrentStep(4)
                          }}
                          title="Выбрать и перейти к настройке записи этого момента"
                          style={{ padding: '2px 8px', fontSize: '11px', borderRadius: '4px' }}
                        >
                          🎬 Запись →
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
        <div style={{ display: 'grid', gridTemplateColumns: '460px 1fr', gap: '32px', alignItems: 'start' }}>
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

            {/* Settings Card */}
            <div
              style={{
                backgroundColor: '#16181f',
                border: '1px solid #232630',
                borderRadius: '10px',
                padding: '20px',
                display: 'flex',
                flexDirection: 'column',
                gap: '18px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #232630', paddingBottom: '12px' }}>
                <div>
                  <div style={{ fontSize: '15px', fontWeight: 700, color: '#f1f5f9' }}>
                    ⚙️ Параметры видео и экспорта CS2
                  </div>
                  <div style={{ fontSize: '11px', color: '#94a3b8' }}>
                    Формат 4:3, стили 2D радара, турнирный HUD и режиссер POV
                  </div>
                </div>
              </div>

              {/* Settings Navigation Tabs */}
              <div
                style={{
                  display: 'flex',
                  gap: '6px',
                  backgroundColor: '#0d1017',
                  padding: '4px',
                  borderRadius: '8px',
                  border: '1px solid #232838',
                  overflowX: 'auto',
                }}
              >
                {[
                  { id: 'screen', label: '🎮 Экран и 4:3', desc: 'Разрешение, FPS' },
                  { id: 'radar', label: '🗺️ Карта и Радар', desc: '130% Огромный, BLAST' },
                  { id: 'hud', label: '🏆 HUD и Киллфид', desc: '115% Масштаб, X-Ray' },
                  { id: 'camera', label: '🎥 Камера и Прицел', desc: 'POV, Прицелы' },
                ].map((tab) => {
                  const isAct = step4Tab === tab.id
                  return (
                    <button
                      key={tab.id}
                      type="button"
                      onClick={() => setStep4Tab(tab.id as any)}
                      style={{
                        flex: 1,
                        minWidth: '120px',
                        padding: '8px 10px',
                        borderRadius: '6px',
                        border: 'none',
                        cursor: 'pointer',
                        backgroundColor: isAct ? '#1e2638' : 'transparent',
                        color: isAct ? '#38bdf8' : '#94a3b8',
                        borderBottom: isAct ? '2px solid #38bdf8' : '2px solid transparent',
                        transition: 'all 0.15s ease',
                        textAlign: 'left',
                      }}
                    >
                      <div style={{ fontSize: '11px', fontWeight: isAct ? 800 : 600 }}>{tab.label}</div>
                      <div style={{ fontSize: '9px', opacity: 0.7 }}>{tab.desc}</div>
                    </button>
                  )
                })}
              </div>

              {/* TAB 1: SCREEN & 4:3 */}
              {step4Tab === 'screen' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                  {/* Format & Resolution Block */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <span style={{ fontSize: '13px', color: '#f1f5f9', fontWeight: 600, display: 'block' }}>Формат экрана CS2</span>
                        <span style={{ fontSize: '11px', color: '#94a3b8' }}>4:3 делает модели врагов шире на 33%</span>
                      </div>
                      <div style={{ display: 'flex', gap: '4px', backgroundColor: '#0e1118', padding: '2px', borderRadius: '6px', border: '1px solid #232734' }}>
                        <button
                          type="button"
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
                          🎮 4:3 (Киберспорт)
                        </button>
                        <button
                          type="button"
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
                          🖥️ 16:9 (Широкий)
                        </button>
                      </div>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#12141c', padding: '10px 12px', borderRadius: '8px', border: '1px solid #232734' }}>
                      <div style={{ display: 'flex', flexDirection: 'column' }}>
                        <span style={{ fontSize: '12px', color: '#f1f5f9', fontWeight: 600 }}>
                          {(clipSettings?.aspectRatio === '4:3' || aspectRatio === '4:3') ? 'Разрешение 4:3' : 'Разрешение 16:9'}
                        </span>
                        <span style={{ fontSize: '10px', color: '#94a3b8' }}>
                          {(clipSettings?.aspectRatio === '4:3' || aspectRatio === '4:3')
                            ? '1280x960 — стандарт киберспортсменов (s1mple, m0NESY)'
                            : '1920x1080 — стандартное Full HD'}
                        </span>
                      </div>

                      <div style={{ display: 'flex', gap: '6px' }}>
                        {(clipSettings?.aspectRatio === '4:3' || aspectRatio === '4:3') ? (
                          <>
                            <button
                              type="button"
                              className="btn"
                              onClick={() => onUpdateSettings && clipSettings && onUpdateSettings({ ...clipSettings, resolution: '1280x960', aspectRatio: '4:3' })}
                              style={{
                                padding: '5px 10px',
                                fontSize: '11px',
                                fontWeight: 700,
                                backgroundColor: (clipSettings?.resolution === '1280x960' || !clipSettings?.resolution || clipSettings?.resolution === '1080p') ? '#38bdf8' : '#1c2333',
                                color: (clipSettings?.resolution === '1280x960' || !clipSettings?.resolution || clipSettings?.resolution === '1080p') ? '#090d16' : '#cbd5e1',
                                border: '1px solid #2d3748',
                                borderRadius: '4px',
                              }}
                              title="1280x960 — выбор 80% профессионалов CS2"
                            >
                              1280x960 ⭐
                            </button>
                            <button
                              type="button"
                              className="btn"
                              onClick={() => onUpdateSettings && clipSettings && onUpdateSettings({ ...clipSettings, resolution: '1440x1080', aspectRatio: '4:3' })}
                              style={{
                                padding: '5px 10px',
                                fontSize: '11px',
                                fontWeight: 700,
                                backgroundColor: clipSettings?.resolution === '1440x1080' ? '#38bdf8' : '#1c2333',
                                color: clipSettings?.resolution === '1440x1080' ? '#090d16' : '#cbd5e1',
                                border: '1px solid #2d3748',
                                borderRadius: '4px',
                              }}
                              title="1440x1080 — повышенная четкость Stretched"
                            >
                              1440x1080
                            </button>
                            <button
                              type="button"
                              className="btn"
                              onClick={() => onUpdateSettings && clipSettings && onUpdateSettings({ ...clipSettings, resolution: '1024x768', aspectRatio: '4:3' })}
                              style={{
                                padding: '5px 10px',
                                fontSize: '11px',
                                fontWeight: 700,
                                backgroundColor: clipSettings?.resolution === '1024x768' ? '#38bdf8' : '#1c2333',
                                color: clipSettings?.resolution === '1024x768' ? '#090d16' : '#cbd5e1',
                                border: '1px solid #2d3748',
                                borderRadius: '4px',
                              }}
                              title="1024x768 — классический 4:3 формат"
                            >
                              1024x768
                            </button>
                          </>
                        ) : (
                          <>
                            <button
                              type="button"
                              className="btn"
                              onClick={() => onUpdateSettings && clipSettings && onUpdateSettings({ ...clipSettings, resolution: '1080p', aspectRatio: '16:9' })}
                              style={{
                                padding: '5px 10px',
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
                              className="btn"
                              onClick={() => onUpdateSettings && clipSettings && onUpdateSettings({ ...clipSettings, resolution: '720p', aspectRatio: '16:9' })}
                              style={{
                                padding: '5px 10px',
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
                  </div>
                </div>
              )}

              {/* TAB 2: RADAR & MINIMAP */}
              {step4Tab === 'radar' && (
                <div style={{ padding: '14px', backgroundColor: '#121316', borderRadius: '8px', border: '1px solid #232630' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '8px' }}>
                    <div>
                      <span style={{ fontSize: '13px', color: '#f1f5f9', fontWeight: 600 }}>2D Радар в игре (CS2)</span>
                      <div style={{ fontSize: '11px', color: '#64748b' }}>Масштаб и ориентация мини-карты на записи</div>
                    </div>
                    <span style={{ fontSize: '11px', color: '#10b981', fontWeight: 600 }}>
                      {clipSettings?.radarMode === 'dynamic_large'
                        ? '🔥 Огромный динамический (130%)'
                        : clipSettings?.radarMode === 'broadcast_giant'
                        ? '📡 Огромный турнирный (130%)'
                        : clipSettings?.radarMode === 'player_focus'
                        ? 'Динамический'
                        : clipSettings?.radarMode === 'compact'
                        ? 'Компактный'
                        : clipSettings?.radarMode === 'hidden'
                        ? 'Скрыт'
                        : 'Broadcast Pro'}
                    </span>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '8px' }}>
                    {[
                      { id: 'dynamic_large', label: '🔥 Огромный динамика', desc: '130% вращается за POV' },
                      { id: 'broadcast_giant', label: '📡 Огромный турнирный', desc: '130% вся карта (BLAST)' },
                      { id: 'player_focus', label: '🧭 Динамика', desc: 'Вращение за POV' },
                      { id: 'broadcast', label: '📺 Pro BLAST', desc: 'Вся карта, север' },
                      { id: 'compact', label: '🔍 Мини', desc: 'Компактный' },
                      { id: 'hidden', label: '🚫 Без радара', desc: 'Скрыть радар' },
                    ].map((r) => {
                      const isSelected = (clipSettings?.radarMode || 'broadcast') === r.id
                      return (
                        <button
                          key={r.id}
                          type="button"
                          className="btn"
                          onClick={() => onUpdateSettings && clipSettings && onUpdateSettings({ ...clipSettings, radarMode: r.id as any })}
                          style={{
                            padding: '8px 6px',
                            textAlign: 'center',
                            backgroundColor: isSelected ? '#10b98122' : '#16181f',
                            borderColor: isSelected ? '#10b981' : '#2b2e38',
                            borderWidth: '1px',
                            borderStyle: 'solid',
                            borderRadius: '6px',
                            color: '#f1f5f9',
                          }}
                        >
                          <div style={{ fontSize: '11px', fontWeight: 700, color: isSelected ? '#34d399' : '#e2e8f0' }}>{r.label}</div>
                          <div style={{ fontSize: '9px', color: '#64748b', marginTop: '2px' }}>{r.desc}</div>
                        </button>
                      )
                    })}
                  </div>
                </div>
              )}

              {/* TAB 3: HUD & KILLFEED */}
              {step4Tab === 'hud' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ padding: '14px', backgroundColor: '#121316', borderRadius: '8px', border: '1px solid #232630' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <div>
                        <span style={{ fontSize: '13px', color: '#f1f5f9', fontWeight: 600 }}>HUD интерфейс и Масштаб</span>
                        <div style={{ fontSize: '11px', color: '#64748b' }}>Игровой интерфейс, киллфид и внешние оверлеи</div>
                      </div>
                      <button
                        type="button"
                        className="btn"
                        onClick={() => setIsTournamentHudModalOpen(true)}
                        style={{
                          padding: '4px 8px',
                          fontSize: '11px',
                          backgroundColor: '#f59e0b22',
                          color: '#fbbf24',
                          border: '1px solid #f59e0b66',
                          borderRadius: '6px',
                          cursor: 'pointer',
                          fontWeight: 600,
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px',
                        }}
                      >
                        🏆 Турнирный HUD (Lexogrine / GSI)...
                      </button>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '8px' }}>
                      {[
                        { mode: 'real', label: '🎥 REAL (OBS Запись)', sub: 'От первого лица, без X-Ray' },
                        { mode: 'huge_esports', label: '🔥 Огромный киберспорт', sub: '115% фраги, HP, аватары' },
                        { mode: 'huge_killfeed', label: '⚡ Огромный киллфид', sub: '115% увеличенные фраги' },
                        { mode: 'killfeed_only', label: '⚔️ Киллфид', sub: 'Только киллы (чисто)' },
                        { mode: 'full', label: '📺 Spectator', sub: 'HP, патроны, счет' },
                        { mode: 'none', label: '🎬 No HUD', sub: 'Чисто для оверлеев' },
                      ].map((h) => {
                        const isSelected = (clipSettings?.hudMode || 'full') === h.mode
                        return (
                          <button
                            key={h.mode}
                            type="button"
                            className="btn"
                            onClick={() => {
                              if (onUpdateSettings && clipSettings) {
                                const isReal = h.mode === 'real'
                                onUpdateSettings({
                                  ...clipSettings,
                                  hudMode: h.mode as any,
                                  hudScale: h.mode.startsWith('huge') ? 1.15 : (isReal ? 1.0 : 0.95),
                                  ...(isReal ? { xray: false, radarMode: 'player_focus' } : {}),
                                })
                              }
                            }}
                            style={{
                              padding: '8px 6px',
                              textAlign: 'center',
                              backgroundColor: isSelected ? (h.mode === 'real' ? '#0284c725' : '#6366f122') : '#16181f',
                              borderColor: isSelected ? (h.mode === 'real' ? '#38bdf8' : '#6366f1') : '#2b2e38',
                              borderWidth: '1px',
                              borderStyle: 'solid',
                              borderRadius: '6px',
                              color: '#f1f5f9',
                            }}
                          >
                            <div style={{ fontSize: '11px', fontWeight: 700, color: isSelected ? (h.mode === 'real' ? '#38bdf8' : '#818cf8') : '#e2e8f0' }}>{h.label}</div>
                            <div style={{ fontSize: '9px', color: '#64748b', marginTop: '2px' }}>{h.sub}</div>
                          </button>
                        )
                      })}
                    </div>
                    {clipSettings?.hudMode === 'real' && (
                      <div style={{ marginTop: '10px', padding: '10px 12px', backgroundColor: '#0284c715', border: '1px solid #0284c744', borderRadius: '6px', fontSize: '11px', color: '#bae6fd', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span>🎥</span>
                        <span><strong>Режим REAL:</strong> Запись выглядит 1:1 как при живой игре через OBS. Скрыта спектаторская полоса внизу (аватар и ник игрока), X-Ray отключен, обычный центрированный круглый радар. Все патроны, здоровье, деньги и киллфид активны.</span>
                      </div>
                    )}
                  </div>

                  {/* X-Ray toggle */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#121316', padding: '12px 14px', borderRadius: '8px', border: '1px solid #232630' }}>
                    <div>
                      <div style={{ fontSize: '13px', color: '#f1f5f9', fontWeight: 600 }}>Силуэты сквозь стены (X-Ray)</div>
                      <div style={{ fontSize: '11px', color: '#64748b' }}>Подсветка игроков через стены spec_show_xray</div>
                    </div>
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
              )}

              {/* TAB 4: CAMERA POV & CROSSHAIR */}
              {step4Tab === 'camera' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {/* POV Camera Director Mode */}
                  <div style={{ padding: '14px', backgroundColor: '#121316', borderRadius: '8px', border: '1px solid #232630' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '8px' }}>
                      <span style={{ fontSize: '13px', color: '#f1f5f9', fontWeight: 600 }}>Режиссер POV камеры</span>
                      <span style={{ fontSize: '11px', color: '#38bdf8', fontWeight: 600 }}>
                        {clipSettings?.perspective === 'dynamic_killcam'
                          ? '🎬 Килл-кам активен'
                          : clipSettings?.perspective === 'victim'
                          ? '💀 Жертва'
                          : '👑 Главный герой (ГГ)'}
                      </span>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '8px' }}>
                      <button
                        type="button"
                        className="btn"
                        onClick={() => onUpdateSettings && clipSettings && onUpdateSettings({ ...clipSettings, perspective: 'attacker' })}
                        style={{
                          padding: '8px 10px',
                          fontSize: '11px',
                          textAlign: 'left',
                          backgroundColor: (!clipSettings?.perspective || clipSettings?.perspective === 'attacker') ? '#3b82f622' : '#16181f',
                          borderColor: (!clipSettings?.perspective || clipSettings?.perspective === 'attacker') ? '#3b82f6' : '#2b2e38',
                          borderRadius: '6px',
                          borderWidth: '1px',
                          borderStyle: 'solid',
                          color: '#f1f5f9',
                        }}
                      >
                        <div style={{ fontWeight: 700, color: '#60a5fa' }}>👑 Главный герой (ГГ)</div>
                        <div style={{ fontSize: '10px', color: '#94a3b8', marginTop: '2px' }}>Камера от лица автора фрагов</div>
                      </button>
                      <button
                        type="button"
                        className="btn"
                        onClick={() => onUpdateSettings && clipSettings && onUpdateSettings({ ...clipSettings, perspective: 'dynamic_killcam' })}
                        style={{
                          padding: '8px 10px',
                          fontSize: '11px',
                          textAlign: 'left',
                          backgroundColor: clipSettings?.perspective === 'dynamic_killcam' ? '#8b5cf622' : '#16181f',
                          borderColor: clipSettings?.perspective === 'dynamic_killcam' ? '#8b5cf6' : '#2b2e38',
                          borderRadius: '6px',
                          borderWidth: '1px',
                          borderStyle: 'solid',
                          color: '#f1f5f9',
                        }}
                      >
                        <div style={{ fontWeight: 700, color: '#c084fc' }}>🎬 Турнирный Килл-кам</div>
                        <div style={{ fontSize: '10px', color: '#94a3b8', marginTop: '2px' }}>Жертва ➔ ГГ за 2+ сек до выстрела</div>
                      </button>
                    </div>
                    <button
                      type="button"
                      className="btn"
                      onClick={() =>
                        onUpdateSettings &&
                        clipSettings &&
                        onUpdateSettings({ ...clipSettings, perspective: clipSettings.perspective === 'victim' ? 'attacker' : 'victim' })
                      }
                      style={{
                        width: '100%',
                        padding: '6px 10px',
                        fontSize: '11px',
                        backgroundColor: clipSettings?.perspective === 'victim' ? '#ef444422' : '#16181f',
                        borderColor: clipSettings?.perspective === 'victim' ? '#ef4444' : '#2b2e38',
                        borderRadius: '6px',
                        borderWidth: '1px',
                        borderStyle: 'solid',
                        color: '#f1f5f9',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                      }}
                    >
                      <span style={{ color: clipSettings?.perspective === 'victim' ? '#f87171' : '#94a3b8' }}>💀 Записать всю нарезку только от лица жертвы</span>
                      <span style={{ fontSize: '10px', fontWeight: 700, color: clipSettings?.perspective === 'victim' ? '#ef4444' : '#64748b' }}>
                        {clipSettings?.perspective === 'victim' ? 'ВКЛЮЧЕНО' : 'ВЫКЛ'}
                      </span>
                    </button>
                  </div>

                  {/* Crosshair Preset Selector */}
                  <div style={{ padding: '14px', backgroundColor: '#121316', borderRadius: '8px', border: '1px solid #232630' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <div>
                        <div style={{ fontSize: '13px', color: '#f1f5f9', fontWeight: 600 }}>Киберспортивный прицел</div>
                        <div style={{ fontSize: '11px', color: '#64748b' }}>Статичный прицел, скрывает TrueView</div>
                      </div>
                      <span style={{ fontSize: '11px', color: '#38bdf8', fontWeight: 600 }}>
                        {clipSettings?.crosshairPreset || 'pro_cyan'}
                      </span>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '6px' }}>
                      {[
                        { label: 'Cyan Pro', p: 'pro_cyan' },
                        { label: 'Green', p: 'green_clean' },
                        { label: 'Точка', p: 'dot' },
                        { label: 'White', p: 'minimal_white' },
                        { label: 'Выкл', p: 'hidden' },
                      ].map((c) => {
                        const isSelected = (clipSettings?.crosshairPreset || 'pro_cyan') === c.p
                        return (
                          <button
                            key={c.p}
                            type="button"
                            className="btn"
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
                              padding: '6px 4px',
                              fontSize: '11px',
                              backgroundColor: isSelected ? '#38bdf822' : '#16181f',
                              borderColor: isSelected ? '#38bdf8' : '#2b2e38',
                              borderWidth: '1px',
                              borderStyle: 'solid',
                              borderRadius: '6px',
                              color: isSelected ? '#38bdf8' : '#cbd5e1',
                              fontWeight: isSelected ? 700 : 500,
                            }}
                          >
                            {c.label}
                          </button>
                        )
                      })}
                    </div>
                  </div>
                </div>
              )}
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
                  className="btn btn-accent"
                  onClick={handleStartMontageCreation}
                  disabled={isCompiling || selectedHighlights.length === 0}
                  style={{ padding: '8px 20px', fontSize: '13px', fontWeight: 700 }}
                >
                  {isCompiling ? '⏳ Запись...' : '🎬 Создать нарезку'}
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
                    <span style={{ fontSize: '12px', fontWeight: 600, color: '#38bdf8' }}>
                      ⏳ {compilationStatus || 'Идет обработка...'}
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
                <div style={{ padding: '10px 14px', backgroundColor: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.3)', borderRadius: '6px', color: '#fbbf24', fontSize: '12px', marginBottom: '16px' }}>
                  ℹ️ {compilationError}
                </div>
              )}

              {/* Compiled Video Player Banner */}
              {compiledMontage && (
                <div style={{ marginBottom: '20px', padding: '14px', backgroundColor: '#101217', borderRadius: '8px', border: '1px solid #22c55e' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <span style={{ fontSize: '13px', fontWeight: 700, color: '#4ade80', display: 'block' }}>
                        ✓ Готовый ролик: {compiledMontage.filename}
                      </span>
                      <span style={{ fontSize: '11px', color: '#94a3b8' }}>
                        Длительность: {compiledMontage.duration_seconds.toFixed(1)} с • {compiledMontage.total_clips} клипов • 1080p60 H.264
                      </span>
                    </div>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button
                        type="button"
                        className="btn btn-primary"
                        onClick={() =>
                          setActiveModalVideo({
                            url: `/api/montage/${compiledMontage.filename}`,
                            title: compiledMontage.filename,
                            subtitle: `Монтаж (${compiledMontage.duration_seconds.toFixed(1)} с, ${compiledMontage.total_clips} клипов)`,
                          })
                        }
                        style={{ padding: '6px 14px', fontSize: '12px' }}
                      >
                        ▶ Смотреть в плеере
                      </button>
                      <a
                        href={`/api/montage/${compiledMontage.filename}`}
                        download
                        className="btn btn-secondary"
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
                        {kill?.headshot && <span>🎯</span>}
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
