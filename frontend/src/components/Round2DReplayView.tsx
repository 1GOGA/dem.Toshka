import { useEffect, useMemo, useRef, useState } from 'react'
import { api } from '../api'
import type { DemoSummary, HighlightItem, RoundDTO, RoundReplayData } from '../types'

interface Round2DReplayViewProps {
  demo: DemoSummary | null
  rounds: RoundDTO[]
  highlights: HighlightItem[]
  onSelectHighlight?: (hl: HighlightItem) => void
}

export function Round2DReplayView({
  demo,
  rounds,
  highlights,
}: Round2DReplayViewProps) {
  const [selectedRoundNum, setSelectedRoundNum] = useState<number>(rounds[0]?.round_num || 1)
  const [replayData, setReplayData] = useState<RoundReplayData | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showTrails, setShowTrails] = useState(true)
  const [showShots, setShowShots] = useState(true)

  // Playback state
  const [currentFrameIndex, setCurrentFrameIndex] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1)
  const [currentLevel, setCurrentLevel] = useState<'upper' | 'lower'>('upper')

  const animationTimerRef = useRef<number | null>(null)

  // Synchronize selected round if rounds change or load asynchronously
  useEffect(() => {
    if (rounds.length > 0 && !rounds.some((r) => r.round_num === selectedRoundNum)) {
      setSelectedRoundNum(rounds[0].round_num)
    }
  }, [rounds, selectedRoundNum])

  // Load round data on round change
  useEffect(() => {
    if (!demo) return
    setIsLoading(true)
    setError(null)
    setIsPlaying(false)
    setCurrentFrameIndex(0)

    api
      .getRoundReplay(demo.id, selectedRoundNum, 32)
      .then((data) => {
        setReplayData(data)
        setIsLoading(false)
      })
      .catch((err) => {
        console.error('Failed to load replay data:', err)
        setError(err?.message || 'Не удалось загрузить данные тактического повтора раунда')
        setIsLoading(false)
      })
  }, [demo, selectedRoundNum])

  // Animation playback loop
  useEffect(() => {
    if (!isPlaying || !replayData || replayData.frames.length === 0) {
      if (animationTimerRef.current) clearInterval(animationTimerRef.current)
      return
    }

    const intervalMs = Math.max(30, Math.floor(125 / playbackSpeed))
    animationTimerRef.current = window.setInterval(() => {
      setCurrentFrameIndex((prev) => {
        if (prev >= replayData.frames.length - 1) {
          setIsPlaying(false)
          return prev
        }
        return prev + 1
      })
    }, intervalMs)

    return () => {
      if (animationTimerRef.current) clearInterval(animationTimerRef.current)
    }
  }, [isPlaying, replayData, playbackSpeed])

  const currentFrame = useMemo(() => {
    if (!replayData || replayData.frames.length === 0) return null
    return replayData.frames[Math.min(currentFrameIndex, replayData.frames.length - 1)]
  }, [replayData, currentFrameIndex])

  // Filter kills that have occurred up to current tick
  const pastKills = useMemo(() => {
    if (!replayData || !currentFrame) return []
    return replayData.kills.filter((k) => k.tick <= currentFrame.tick)
  }, [replayData, currentFrame])

  // Accumulate breadcrumb movement trails for each player up to currentFrameIndex
  const playerTrails = useMemo(() => {
    if (!replayData || !replayData.frames || replayData.frames.length === 0) return {}
    const trails: Record<string, Array<{ x: number; y: number; is_alive: boolean }>> = {}
    const maxIdx = Math.min(currentFrameIndex, replayData.frames.length - 1)
    for (let i = 0; i <= maxIdx; i++) {
      const f = replayData.frames[i]
      for (const p of f.players) {
        if (!trails[p.steam_id]) trails[p.steam_id] = []
        trails[p.steam_id].push({ x: p.x, y: p.y, is_alive: p.is_alive })
      }
    }
    return trails
  }, [replayData, currentFrameIndex])

  // Highlights occurring in this round
  const roundHighlights = useMemo(() => {
    return highlights.filter((h) => h.round_num === selectedRoundNum)
  }, [highlights, selectedRoundNum])

  const hasMultipleLevels = Boolean(replayData?.levels && replayData.levels.length > 1)

  const radarImageUrl = useMemo(() => {
    if (!replayData) return ''
    if (currentLevel === 'lower' && replayData.radar_file_lower) {
      return `/maps/${replayData.radar_file_lower}`
    }
    return `/maps/${replayData.radar_file || (demo?.map_name ? `${demo.map_name}.png` : 'de_nuke.png')}`
  }, [replayData, currentLevel, demo])

  const formatRoundTime = (tick: number, startTick: number, tickrate: number) => {
    const elapsedSec = Math.max(0, Math.floor((tick - startTick) / (tickrate || 128)))
    const mins = Math.floor(elapsedSec / 60)
    const secs = elapsedSec % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const handleJumpToTick = (targetTick: number) => {
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
    setCurrentFrameIndex(bestIdx)
    setIsPlaying(false)
  }

  return (
    <div style={{ maxWidth: '1440px', margin: '0 auto', padding: '24px 20px' }}>
      {/* Header bar */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '20px',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <h1 style={{ fontSize: '24px', fontWeight: 800, color: '#f1f5f9', letterSpacing: '-0.02em', margin: 0 }}>
              2D Tactical Replay
            </h1>
            <span
              style={{
                backgroundColor: 'rgba(56, 189, 248, 0.1)',
                border: '1px solid rgba(56, 189, 248, 0.3)',
                color: '#38bdf8',
                padding: '3px 8px',
                borderRadius: '4px',
                fontSize: '11px',
                fontWeight: 700,
                textTransform: 'uppercase',
              }}
            >
              {demo?.map_name || 'de_nuke'}
            </span>
          </div>
          <p style={{ fontSize: '13px', color: '#94a3b8', margin: '4px 0 0 0' }}>
            Реальные мировые координаты игроков из CS2 Source 2 (Awpy), траектории перемещений и выстрелы.
          </p>
        </div>

        {/* Round switcher pills */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', overflowX: 'auto', maxWidth: '600px' }}>
          <span style={{ fontSize: '12px', color: '#64748b', fontWeight: 600 }}>Раунд:</span>
          {rounds.map((r) => {
            const isWinnerCT = r.winner === 'ct'
            return (
              <button
                key={r.round_num}
                type="button"
                onClick={() => setSelectedRoundNum(r.round_num)}
                style={{
                  padding: '4px 10px',
                  borderRadius: '6px',
                  border: selectedRoundNum === r.round_num ? '1px solid #38bdf8' : '1px solid #232733',
                  backgroundColor:
                    selectedRoundNum === r.round_num
                      ? 'rgba(56, 189, 248, 0.15)'
                      : r.winner
                      ? isWinnerCT
                        ? 'rgba(59, 130, 246, 0.08)'
                        : 'rgba(249, 115, 22, 0.08)'
                      : '#13151b',
                  color: selectedRoundNum === r.round_num ? '#38bdf8' : '#94a3b8',
                  fontSize: '12px',
                  fontWeight: selectedRoundNum === r.round_num ? 700 : 500,
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                R{r.round_num}
              </button>
            )
          })}
        </div>
      </div>

      {isLoading && (
        <div style={{ padding: '60px', textAlign: 'center', color: '#38bdf8', fontSize: '14px' }}>
          <svg
            style={{ width: '24px', height: '24px', animation: 'spin 1s linear infinite', display: 'inline-block', marginRight: '8px' }}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <circle cx="12" cy="12" r="10" strokeOpacity="0.25" />
            <path d="M12 2a10 10 0 0 1 10 10" />
          </svg>
          Загрузка тиковых траекторий раунда из демки...
        </div>
      )}

      {error && (
        <div style={{ padding: '16px', backgroundColor: 'rgba(239, 68, 68, 0.1)', border: '1px solid #ef4444', borderRadius: '8px', color: '#f87171', fontSize: '13px', marginBottom: '20px' }}>
          {error}
        </div>
      )}

      {replayData && !isLoading && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '24px', alignItems: 'start' }}>
          {/* Main 2D Radar Canvas & Controls */}
          <div
            style={{
              backgroundColor: '#12141a',
              border: '1px solid #232734',
              borderRadius: '12px',
              padding: '20px',
              display: 'flex',
              flexDirection: 'column',
              gap: '16px',
            }}
          >
            {/* Top Toolbar: Levels & Legend */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                {hasMultipleLevels ? (
                  <>
                    <span style={{ fontSize: '12px', color: '#64748b', fontWeight: 600 }}>Ярус карты:</span>
                    <button
                      type="button"
                      onClick={() => setCurrentLevel('upper')}
                      style={{
                        padding: '4px 12px',
                        borderRadius: '5px',
                        fontSize: '11px',
                        fontWeight: 700,
                        border: currentLevel === 'upper' ? '1px solid #38bdf8' : '1px solid #232734',
                        backgroundColor: currentLevel === 'upper' ? 'rgba(56, 189, 248, 0.15)' : '#181b24',
                        color: currentLevel === 'upper' ? '#38bdf8' : '#94a3b8',
                        cursor: 'pointer',
                        transition: 'all 0.15s ease',
                      }}
                    >
                      Верхний (Upper / A)
                    </button>
                    <button
                      type="button"
                      onClick={() => setCurrentLevel('lower')}
                      style={{
                        padding: '4px 12px',
                        borderRadius: '5px',
                        fontSize: '11px',
                        fontWeight: 700,
                        border: currentLevel === 'lower' ? '1px solid #38bdf8' : '1px solid #232734',
                        backgroundColor: currentLevel === 'lower' ? 'rgba(56, 189, 248, 0.15)' : '#181b24',
                        color: currentLevel === 'lower' ? '#38bdf8' : '#94a3b8',
                        cursor: 'pointer',
                        transition: 'all 0.15s ease',
                      }}
                    >
                      Нижний (Lower / B)
                    </button>
                  </>
                ) : (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span
                      style={{
                        fontSize: '11px',
                        fontWeight: 700,
                        backgroundColor: 'rgba(56, 189, 248, 0.1)',
                        border: '1px solid rgba(56, 189, 248, 0.25)',
                        color: '#38bdf8',
                        padding: '3px 8px',
                        borderRadius: '4px',
                        textTransform: 'uppercase',
                        letterSpacing: '0.05em',
                      }}
                    >
                      {demo?.map_name || 'Радар'}
                    </span>
                    <span style={{ fontSize: '12px', color: '#64748b' }}>
                      Официальный радар Source 2 • Координаты 1:1
                    </span>
                  </div>
                )}
              </div>

              {/* Legend & Display Toggles */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '14px', fontSize: '12px' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', color: '#cbd5e1' }}>
                  <input
                    type="checkbox"
                    checked={showTrails}
                    onChange={(e) => setShowTrails(e.target.checked)}
                    style={{ accentColor: '#38bdf8', cursor: 'pointer' }}
                  />
                  <span>Траектории</span>
                </label>

                <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', color: '#cbd5e1' }}>
                  <input
                    type="checkbox"
                    checked={showShots}
                    onChange={(e) => setShowShots(e.target.checked)}
                    style={{ accentColor: '#fbbf24', cursor: 'pointer' }}
                  />
                  <span>Выстрелы</span>
                </label>

                <div style={{ width: '1px', height: '14px', backgroundColor: '#232733' }} />

                <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#60a5fa', fontWeight: 600 }}>
                  <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#3b82f6', display: 'inline-block', boxShadow: '0 0 6px rgba(59, 130, 246, 0.5)' }} />
                  CT
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#fb923c', fontWeight: 600 }}>
                  <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#f97316', display: 'inline-block', boxShadow: '0 0 6px rgba(249, 115, 22, 0.5)' }} />
                  T
                </span>
              </div>
            </div>

            {/* 2D Vector Radar Map Container */}
            <div
              style={{
                position: 'relative',
                width: '100%',
                aspectRatio: '1 / 1',
                maxHeight: '640px',
                margin: '0 auto',
                backgroundColor: '#0c0e13',
                borderRadius: '8px',
                border: '1px solid #1a1d27',
                overflow: 'hidden',
                boxShadow: '0 8px 24px rgba(0, 0, 0, 0.5)',
              }}
            >
              {/* Official Radar Image Backdrop */}
              {radarImageUrl && (
                <img
                  src={radarImageUrl}
                  alt={demo?.map_name || 'CS2 Radar'}
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: '100%',
                    objectFit: 'contain',
                    pointerEvents: 'none',
                    opacity: 0.92,
                    filter: 'brightness(0.95) contrast(1.08)',
                    zIndex: 1,
                  }}
                />
              )}

              {/* Tactical Vectors, Rings, Trails & Kill Lines */}
              <svg
                viewBox="0 0 1000 1000"
                style={{
                  width: '100%',
                  height: '100%',
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  pointerEvents: 'none',
                  zIndex: 2,
                }}
              >
                {/* Subtle Radar Concentric Distance Rings */}
                <circle cx="500" cy="500" r="460" fill="none" stroke="#38bdf8" strokeWidth="0.8" strokeDasharray="6 6" opacity="0.12" />
                <circle cx="500" cy="500" r="280" fill="none" stroke="#38bdf8" strokeWidth="0.8" strokeDasharray="6 6" opacity="0.1" />

                {/* Player Movement Breadcrumb Trails */}
                {showTrails &&
                  Object.entries(playerTrails).map(([steamId, points]) => {
                    if (points.length < 2) return null
                    const pInfo = replayData?.players[steamId]
                    const isCT = pInfo?.side === 'ct'
                    const stroke = isCT ? '#3b82f6' : '#f97316'
                    const polyPoints = points.map((pt) => `${pt.x * 10},${pt.y * 10}`).join(' ')
                    return (
                      <polyline
                        key={`trail-${steamId}`}
                        points={polyPoints}
                        fill="none"
                        stroke={stroke}
                        strokeWidth="2.5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeOpacity="0.45"
                        strokeDasharray="4 2"
                      />
                    )
                  })}

                {/* Active Gunfire Muzzle Burst & Tracer Beams */}
                {showShots &&
                  pastKills
                    .filter((k) => Math.abs(k.tick - (currentFrame?.tick || 0)) < (replayData?.tickrate || 64) * 2.0)
                    .map((k, i) => (
                      <g key={`shot-${i}`}>
                        <line
                          x1={k.attacker_x * 10}
                          y1={k.attacker_y * 10}
                          x2={k.victim_x * 10}
                          y2={k.victim_y * 10}
                          stroke="#facc15"
                          strokeWidth="3.5"
                          strokeOpacity="0.9"
                        />
                        <circle
                          cx={k.attacker_x * 10}
                          cy={k.attacker_y * 10}
                          r="14"
                          fill="rgba(250, 204, 21, 0.4)"
                          stroke="#facc15"
                          strokeWidth="2"
                        />
                      </g>
                    ))}

                {/* Kill Vectors Lines */}
                {pastKills.map((k, i) => (
                  <line
                    key={`kill-line-${i}`}
                    x1={k.attacker_x * 10}
                    y1={k.attacker_y * 10}
                    x2={k.victim_x * 10}
                    y2={k.victim_y * 10}
                    stroke={k.attacker_side === 'ct' ? '#38bdf8' : '#f97316'}
                    strokeWidth="1.5"
                    strokeDasharray="4 3"
                    opacity="0.5"
                  />
                ))}
              </svg>

              {/* Real Player Markers (HTML Overlays on Radar) */}
              {currentFrame?.players.map((p) => {
                const isCurrentLevel = hasMultipleLevels ? p.level === currentLevel : true
                const opacity = isCurrentLevel ? (p.is_alive ? 1 : 0.3) : 0.2
                const isCT = p.side === 'ct'
                const color = isCT ? '#3b82f6' : '#f97316'

                return (
                  <div
                    key={p.steam_id}
                    style={{
                      position: 'absolute',
                      left: `${p.x}%`,
                      top: `${p.y}%`,
                      transform: 'translate(-50%, -50%)',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      pointerEvents: 'none',
                      opacity,
                      transition: 'left 0.12s linear, top 0.12s linear, opacity 0.2s ease',
                      zIndex: isCurrentLevel ? 10 : 2,
                    }}
                  >
                    {/* Player Dot */}
                    <div
                      style={{
                        width: '18px',
                        height: '18px',
                        borderRadius: '50%',
                        backgroundColor: color,
                        border: '2px solid #ffffff',
                        boxShadow: `0 0 10px ${color}`,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '9px',
                        fontWeight: 800,
                        color: '#ffffff',
                      }}
                    >
                      {p.is_alive ? (isCT ? 'CT' : 'T') : '✕'}
                    </div>

                    {/* Name & HP Tag */}
                    {isCurrentLevel && (
                      <div
                        style={{
                          marginTop: '3px',
                          backgroundColor: 'rgba(10, 12, 16, 0.85)',
                          padding: '1px 5px',
                          borderRadius: '3px',
                          border: `1px solid ${color}44`,
                          fontSize: '10px',
                          fontWeight: 600,
                          color: '#f1f5f9',
                          whiteSpace: 'nowrap',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px',
                        }}
                      >
                        <span>{p.name.slice(0, 10)}</span>
                        {p.is_alive && (
                          <span style={{ color: p.health < 40 ? '#ef4444' : '#22c55e', fontSize: '9px' }}>
                            {Math.round(p.health)}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                )
              })}

              {/* Kill Skull Markers */}
              {pastKills.map((k, i) => (
                <div
                  key={`skull-${i}`}
                  style={{
                    position: 'absolute',
                    left: `${k.victim_x}%`,
                    top: `${k.victim_y}%`,
                    transform: 'translate(-50%, -50%)',
                    width: '14px',
                    height: '14px',
                    borderRadius: '50%',
                    backgroundColor: 'rgba(239, 68, 68, 0.7)',
                    border: '1px solid #ef4444',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '9px',
                    color: '#ffffff',
                    fontWeight: 800,
                    zIndex: 5,
                    pointerEvents: 'none',
                  }}
                >
                  ☠
                </div>
              ))}
            </div>

            {/* Timeline Scrubber & Controls */}
            <div
              style={{
                backgroundColor: '#0e1015',
                padding: '12px 16px',
                borderRadius: '8px',
                border: '1px solid #1a1e28',
                display: 'flex',
                flexDirection: 'column',
                gap: '10px',
              }}
            >
              {/* Progress Slider */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span style={{ fontSize: '12px', fontFamily: 'monospace', color: '#94a3b8', minWidth: '40px' }}>
                  {currentFrame ? formatRoundTime(currentFrame.tick, replayData.start_tick, replayData.tickrate) : '0:00'}
                </span>
                <input
                  type="range"
                  min="0"
                  max={Math.max(0, replayData.frames.length - 1)}
                  value={currentFrameIndex}
                  onChange={(e) => {
                    setCurrentFrameIndex(parseInt(e.target.value, 10))
                    setIsPlaying(false)
                  }}
                  style={{ flex: 1, accentColor: '#38bdf8', cursor: 'pointer' }}
                />
                <span style={{ fontSize: '11px', color: '#64748b', fontFamily: 'monospace' }}>
                  Тик {currentFrame?.tick || 0}
                </span>
              </div>

              {/* Playback action buttons */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <button
                    type="button"
                    onClick={() => setIsPlaying(!isPlaying)}
                    style={{
                      padding: '6px 16px',
                      borderRadius: '6px',
                      backgroundColor: isPlaying ? 'rgba(239, 68, 68, 0.2)' : 'rgba(56, 189, 248, 0.2)',
                      border: isPlaying ? '1px solid #ef4444' : '1px solid #38bdf8',
                      color: isPlaying ? '#ef4444' : '#38bdf8',
                      fontSize: '12px',
                      fontWeight: 700,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                    }}
                  >
                    {isPlaying ? '⏸ Пауза' : '▶ Воспроизведение'}
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setCurrentFrameIndex(0)
                      setIsPlaying(false)
                    }}
                    style={{
                      padding: '6px 12px',
                      borderRadius: '6px',
                      backgroundColor: '#161922',
                      border: '1px solid #232734',
                      color: '#94a3b8',
                      fontSize: '12px',
                      cursor: 'pointer',
                    }}
                  >
                    ⏮ В начало
                  </button>
                </div>

                {/* Speed Controls */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <span style={{ fontSize: '11px', color: '#64748b', marginRight: '4px' }}>Скорость:</span>
                  {[0.5, 1, 2, 4].map((spd) => (
                    <button
                      key={spd}
                      type="button"
                      onClick={() => setPlaybackSpeed(spd)}
                      style={{
                        padding: '3px 8px',
                        borderRadius: '4px',
                        fontSize: '11px',
                        fontWeight: 700,
                        border: playbackSpeed === spd ? '1px solid #38bdf8' : '1px solid #1f2330',
                        backgroundColor: playbackSpeed === spd ? 'rgba(56, 189, 248, 0.15)' : '#12141a',
                        color: playbackSpeed === spd ? '#38bdf8' : '#64748b',
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

          {/* Right Sidebar: Round Highlights & Event Feed */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {/* Highlights in this round */}
            <div
              style={{
                backgroundColor: '#12141a',
                border: '1px solid #232734',
                borderRadius: '10px',
                padding: '16px',
              }}
            >
              <div style={{ fontSize: '13px', fontWeight: 700, color: '#f1f5f9', marginBottom: '12px' }}>
                Хайлайты в этом раунде ({roundHighlights.length})
              </div>

              {roundHighlights.length === 0 ? (
                <div style={{ fontSize: '12px', color: '#64748b' }}>В этом раунде нет хайлайтов</div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {roundHighlights.map((hl) => (
                    <div
                      key={hl.id}
                      onClick={() => handleJumpToTick(hl.kill_start_tick)}
                      style={{
                        padding: '8px 12px',
                        backgroundColor: '#171a23',
                        border: '1px solid #232734',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        transition: 'border-color 0.15s ease',
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.borderColor = '#38bdf8')}
                      onMouseLeave={(e) => (e.currentTarget.style.borderColor = '#232734')}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '12px', fontWeight: 700, color: '#38bdf8' }}>
                          {hl.highlight_type.replace('multikill_', '').toUpperCase()}
                        </span>
                        <span style={{ fontSize: '11px', fontFamily: 'monospace', color: '#94a3b8' }}>
                          Тик {hl.kill_start_tick}
                        </span>
                      </div>
                      <div style={{ fontSize: '11px', color: '#cbd5e1', marginTop: '3px' }}>
                        {hl.pov_name || 'Player'} ({hl.kill_count} киллов)
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Kill Events Stream */}
            <div
              style={{
                backgroundColor: '#12141a',
                border: '1px solid #232734',
                borderRadius: '10px',
                padding: '16px',
                maxHeight: '400px',
                overflowY: 'auto',
              }}
            >
              <div style={{ fontSize: '13px', fontWeight: 700, color: '#f1f5f9', marginBottom: '12px' }}>
                События убийств ({pastKills.length}/{replayData.kills.length})
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {replayData.kills.map((k, i) => {
                  const hasOccurred = currentFrame && k.tick <= currentFrame.tick
                  return (
                    <div
                      key={`kill-ev-${i}`}
                      onClick={() => handleJumpToTick(k.tick)}
                      style={{
                        padding: '6px 10px',
                        backgroundColor: hasOccurred ? '#181b24' : '#0e1015',
                        border: '1px solid #222633',
                        borderRadius: '6px',
                        fontSize: '11px',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        opacity: hasOccurred ? 1 : 0.4,
                        cursor: 'pointer',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span style={{ color: k.attacker_side === 'ct' ? '#60a5fa' : '#fb923c', fontWeight: 700 }}>
                          {k.attacker_name}
                        </span>
                        <span style={{ color: '#fbbf24', fontSize: '10px' }}>
                          [{k.weapon.replace('weapon_', '')}]
                        </span>
                        {k.headshot && <span>🎯</span>}
                        <span style={{ color: '#94a3b8' }}>→</span>
                        <span style={{ color: k.victim_side === 'ct' ? '#60a5fa' : '#fb923c' }}>
                          {k.victim_name}
                        </span>
                      </div>
                      <span style={{ fontSize: '10px', fontFamily: 'monospace', color: '#64748b' }}>
                        {formatRoundTime(k.tick, replayData.start_tick, replayData.tickrate)}
                      </span>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

