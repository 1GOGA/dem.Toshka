import React, { useState, useRef, useEffect, useMemo } from 'react'
import type { ReplayPlayerState, ReplayKillItem, ReplayGrenadeItem } from '../types'
import { SkullIcon, SmokeIcon, FlameIcon, FlashIcon, GrenadeIcon } from './Icons'

export interface TacticalReplayRadarProps {
  radarImageUrl?: string
  mapName?: string
  currentTick: number
  tickrate: number
  startTick: number
  players: ReplayPlayerState[]
  kills: ReplayKillItem[]
  grenades?: ReplayGrenadeItem[]
  playerTrails?: Record<string, Array<{ x: number; y: number; is_alive: boolean }>>
  currentLevel?: 'upper' | 'lower'
  hasMultipleLevels?: boolean
  showTrails: boolean
  showShots: boolean
  showGrenades: boolean
  onJumpToTick?: (tick: number) => void
  maxContainerHeight?: string
}

export const TacticalReplayRadar: React.FC<TacticalReplayRadarProps> = ({
  radarImageUrl,
  mapName = 'CS2 Map',
  currentTick,
  tickrate = 128,
  startTick: _startTick,
  players,
  kills,
  grenades = [],
  playerTrails = {},
  currentLevel = 'upper',
  hasMultipleLevels = false,
  showTrails,
  showShots,
  showGrenades,
  onJumpToTick,
  maxContainerHeight = '560px',
}) => {
  // Zoom & Pan state
  const [zoom, setZoom] = useState<number>(1)
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 })
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 })
  const [hoveredKill, setHoveredKill] = useState<ReplayKillItem | null>(null)
  const [hoveredGrenade, setHoveredGrenade] = useState<ReplayGrenadeItem | null>(null)

  const containerRef = useRef<HTMLDivElement>(null)

  // Zoom handlers
  const handleZoomIn = () => {
    setZoom((prev) => Math.min(3.5, Number((prev + 0.35).toFixed(2))))
  }

  const handleZoomOut = () => {
    setZoom((prev) => {
      const next = Math.max(1, Number((prev - 0.35).toFixed(2)))
      if (next === 1) setPan({ x: 0, y: 0 })
      return next
    })
  }

  const handleResetZoom = () => {
    setZoom(1)
    setPan({ x: 0, y: 0 })
  }

  // Native wheel listener on container with preventDefault to prevent window scroll
  useEffect(() => {
    const el = containerRef.current
    if (!el) return

    const onWheelNative = (e: WheelEvent) => {
      e.preventDefault()
      e.stopPropagation()
      if (e.deltaY < 0) {
        setZoom((prev) => Math.min(3.5, Number((prev + 0.25).toFixed(2))))
      } else {
        setZoom((prev) => {
          const next = Math.max(1, Number((prev - 0.25).toFixed(2)))
          if (next === 1) setPan({ x: 0, y: 0 })
          return next
        })
      }
    }

    el.addEventListener('wheel', onWheelNative, { passive: false })
    return () => {
      el.removeEventListener('wheel', onWheelNative)
    }
  }, [])

  // Drag pan handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    if (zoom > 1) {
      setIsDragging(true)
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y })
    }
  }

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging && zoom > 1) {
      const maxPan = (zoom - 1) * 220
      const nextX = Math.max(-maxPan, Math.min(maxPan, e.clientX - dragStart.x))
      const nextY = Math.max(-maxPan, Math.min(maxPan, e.clientY - dragStart.y))
      setPan({ x: nextX, y: nextY })
    }
  }

  const handleMouseUp = () => {
    setIsDragging(false)
  }

  // Kills that occurred up to current tick
  const pastKills = useMemo(() => {
    return kills.filter((k) => k.tick <= currentTick)
  }, [kills, currentTick])

  // Filter living players only (dead players do not render duplicate tokens)
  const livingPlayers = useMemo(() => {
    return players.filter((p) => p.is_alive)
  }, [players])

  // Active grenades at currentTick
  const activeGrenades = useMemo(() => {
    if (!showGrenades || !grenades || grenades.length === 0) return []
    return grenades.filter((g) => {
      // Show if in-flight or detonated and not yet expired
      return g.start_tick <= currentTick && currentTick <= g.end_tick
    })
  }, [grenades, currentTick, showGrenades])

  return (
    <div
      ref={containerRef}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      style={{
        position: 'relative',
        width: '100%',
        maxWidth: maxContainerHeight,
        aspectRatio: '1 / 1',
        margin: '0 auto',
        backgroundColor: '#0a0d14',
        borderRadius: '10px',
        border: '1px solid #1e2433',
        overflow: 'hidden',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.55)',
        cursor: zoom > 1 ? (isDragging ? 'grabbing' : 'grab') : 'default',
        userSelect: 'none',
        overscrollBehavior: 'contain',
        touchAction: 'none',
      }}
    >
      <style>{`
        @keyframes radarPing {
          0% { transform: scale(0.9); opacity: 0.95; }
          100% { transform: scale(2.5); opacity: 0; }
        }
        @keyframes smokePulse {
          0%, 100% { opacity: 0.55; }
          50% { opacity: 0.28; }
        }
        @keyframes fireGlow {
          0%, 100% { transform: scale(1); filter: drop-shadow(0 0 4px rgba(249, 115, 22, 0.6)); }
          50% { transform: scale(1.04); filter: drop-shadow(0 0 8px rgba(239, 68, 68, 0.8)); }
        }
        @keyframes flashBurst {
          0% { transform: scale(0.5); opacity: 1; }
          100% { transform: scale(2.2); opacity: 0; }
        }
      `}</style>

      {/* Floating Zoom & Pan Controls */}
      <div
        style={{
          position: 'absolute',
          top: '10px',
          right: '10px',
          zIndex: 35,
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          backgroundColor: 'rgba(11, 15, 23, 0.92)',
          backdropFilter: 'blur(8px)',
          padding: '3px 8px',
          borderRadius: '6px',
          border: '1px solid rgba(56, 189, 248, 0.3)',
          boxShadow: '0 4px 14px rgba(0, 0, 0, 0.6)',
        }}
      >
        <button
          type="button"
          onClick={handleZoomOut}
          disabled={zoom <= 1}
          title="Отдалить (-)"
          style={{
            background: 'transparent',
            border: 'none',
            color: zoom <= 1 ? '#475569' : '#38bdf8',
            cursor: zoom <= 1 ? 'not-allowed' : 'pointer',
            fontSize: '15px',
            fontWeight: 800,
            padding: '2px 5px',
            lineHeight: 1,
          }}
        >
          −
        </button>
        <button
          type="button"
          onClick={handleResetZoom}
          title="Сбросить масштаб (100%)"
          style={{
            fontSize: '11px',
            color: '#94a3b8',
            fontFamily: 'monospace',
            fontWeight: 700,
            minWidth: '34px',
            textAlign: 'center',
            background: 'none',
            border: 'none',
            cursor: 'pointer',
          }}
        >
          {zoom.toFixed(1)}x
        </button>
        <button
          type="button"
          onClick={handleZoomIn}
          disabled={zoom >= 3.5}
          title="Приблизить (+)"
          style={{
            background: 'transparent',
            border: 'none',
            color: zoom >= 3.5 ? '#475569' : '#38bdf8',
            cursor: zoom >= 3.5 ? 'not-allowed' : 'pointer',
            fontSize: '15px',
            fontWeight: 800,
            padding: '2px 5px',
            lineHeight: 1,
          }}
        >
          +
        </button>
      </div>

      {/* Tooltip Overlay for Hovered Kill or Grenade */}
      {(hoveredKill || hoveredGrenade) && (
        <div
          style={{
            position: 'absolute',
            bottom: '12px',
            left: '12px',
            zIndex: 40,
            backgroundColor: 'rgba(9, 13, 20, 0.94)',
            backdropFilter: 'blur(8px)',
            border: '1px solid rgba(56, 189, 248, 0.4)',
            padding: '5px 10px',
            borderRadius: '6px',
            fontSize: '11px',
            color: '#f1f5f9',
            boxShadow: '0 4px 16px rgba(0,0,0,0.7)',
            pointerEvents: 'none',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          {hoveredKill && (
            <>
              <SkullIcon size={12} color="#ef4444" />
              <span>
                <strong>{hoveredKill.attacker_name}</strong> [{hoveredKill.weapon || 'kill'}] ➔{' '}
                <strong>{hoveredKill.victim_name}</strong>
              </span>
              <span style={{ color: '#64748b', fontSize: '10px' }}>(клик для перехода к тику)</span>
            </>
          )}
          {hoveredGrenade && !hoveredKill && (
            <>
              {hoveredGrenade.type === 'smoke' && <SmokeIcon size={13} color="#94a3b8" />}
              {hoveredGrenade.type === 'molotov' && <FlameIcon size={13} color="#f97316" />}
              {hoveredGrenade.type === 'flash' && <FlashIcon size={13} color="#facc15" />}
              {hoveredGrenade.type === 'he' && <GrenadeIcon size={13} color="#ef4444" />}
              <span>
                <strong>
                  {hoveredGrenade.type === 'smoke'
                    ? 'Дым'
                    : hoveredGrenade.type === 'molotov'
                    ? 'Огонь / Молотов'
                    : hoveredGrenade.type === 'flash'
                    ? 'Световая граната'
                    : 'Осколочная граната (HE)'}
                </strong>
                {hoveredGrenade.thrower_name ? ` (бросил: ${hoveredGrenade.thrower_name})` : ''}
                {hoveredGrenade.type === 'smoke' || hoveredGrenade.type === 'molotov' ? (
                  <span style={{ color: '#38bdf8', marginLeft: '6px' }}>
                    Осталось: {Math.max(0, (hoveredGrenade.end_tick - currentTick) / tickrate).toFixed(1)}с
                  </span>
                ) : null}
              </span>
            </>
          )}
        </div>
      )}

      {/* Scalable Tactical Inner Canvas */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
          transformOrigin: 'center center',
          transition: isDragging ? 'none' : 'transform 0.12s ease-out',
        }}
      >
        {/* Source 2 Radar Map Backdrop */}
        {radarImageUrl && (
          <img
            src={radarImageUrl}
            alt={mapName}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              objectFit: 'fill',
              pointerEvents: 'none',
              opacity: 0.94,
              filter: 'brightness(0.96) contrast(1.08)',
              zIndex: 1,
            }}
          />
        )}

        {/* SVG Tactical Vectors, Rings, Trails, Grenades & Gunfire */}
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
          <defs>
            {/* Soft Smoke Cloud Gradient */}
            <radialGradient id="tactical-smoke-grad" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#94a3b8" stopOpacity="0.55" />
              <stop offset="50%" stopColor="#64748b" stopOpacity="0.38" />
              <stop offset="85%" stopColor="#475569" stopOpacity="0.18" />
              <stop offset="100%" stopColor="#334155" stopOpacity="0" />
            </radialGradient>

            {/* Fiery Molotov Flame Gradient */}
            <radialGradient id="tactical-molotov-grad" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#ef4444" stopOpacity="0.75" />
              <stop offset="40%" stopColor="#f97316" stopOpacity="0.45" />
              <stop offset="75%" stopColor="#f59e0b" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#d97706" stopOpacity="0" />
            </radialGradient>

            {/* Flashbang Detonation Burst Gradient */}
            <radialGradient id="tactical-flash-grad" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#ffffff" stopOpacity="0.95" />
              <stop offset="45%" stopColor="#fef08a" stopOpacity="0.6" />
              <stop offset="85%" stopColor="#facc15" stopOpacity="0.2" />
              <stop offset="100%" stopColor="#eab308" stopOpacity="0" />
            </radialGradient>

            {/* HE Explosion Shockwave Gradient */}
            <radialGradient id="tactical-he-grad" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#f97316" stopOpacity="0.8" />
              <stop offset="50%" stopColor="#ef4444" stopOpacity="0.4" />
              <stop offset="100%" stopColor="#b91c1c" stopOpacity="0" />
            </radialGradient>
          </defs>

          {/* Subtle Radar Concentric Distance Rings */}
          <circle cx="500" cy="500" r="460" fill="none" stroke="#38bdf8" strokeWidth="0.8" strokeDasharray="6 6" opacity="0.12" />
          <circle cx="500" cy="500" r="280" fill="none" stroke="#38bdf8" strokeWidth="0.8" strokeDasharray="6 6" opacity="0.1" />

          {/* Player Movement Breadcrumb Trails */}
          {showTrails &&
            Object.entries(playerTrails).map(([steamId, points]) => {
              if (points.length < 2) return null
              // Check side from living players or default to CT
              const pInfo = livingPlayers.find((p) => p.steam_id === steamId)
              const isCT = pInfo?.side === 'ct'
              const stroke = isCT ? '#3b82f6' : '#f97316'
              const polyPoints = points.map((pt) => `${pt.x * 10},${pt.y * 10}`).join(' ')
              return (
                <polyline
                  key={`trail-${steamId}`}
                  points={polyPoints}
                  fill="none"
                  stroke={stroke}
                  strokeWidth="2.2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeOpacity="0.4"
                  strokeDasharray="4 2"
                />
              )
            })}

          {/* ================================================================= */}
          {/* GRENADE LAYER: SMOKES, MOLOTOVS, FLASHBANGS, HE GRENADES         */}
          {/* ================================================================= */}
          {showGrenades &&
            activeGrenades.map((g) => {
              const gx = g.x * 10
              const gy = g.y * 10
              const isInFlight = currentTick < g.detonate_tick
              const isDetonated = currentTick >= g.detonate_tick && currentTick <= g.end_tick

              // In-flight projectile trajectory
              if (isInFlight) {
                // Find current flight position from trajectory
                let flightX = gx
                let flightY = gy
                if (g.trajectory && g.trajectory.length > 0) {
                  // Find closest trajectory frame up to currentTick
                  let closest = g.trajectory[0]
                  for (const pt of g.trajectory) {
                    if (pt.tick <= currentTick) {
                      closest = pt
                    } else {
                      break
                    }
                  }
                  flightX = closest.x * 10
                  flightY = closest.y * 10
                }

                return (
                  <g key={`grenade-flight-${g.id}`}>
                    {/* Dotted path to landing */}
                    <line
                      x1={flightX}
                      y1={flightY}
                      x2={gx}
                      y2={gy}
                      stroke={g.type === 'smoke' ? '#94a3b8' : g.type === 'molotov' ? '#f97316' : '#facc15'}
                      strokeWidth="1.5"
                      strokeDasharray="3 3"
                      strokeOpacity="0.6"
                    />
                    {/* In-flight projectile indicator */}
                    <circle
                      cx={flightX}
                      cy={flightY}
                      r="4.5"
                      fill={g.type === 'smoke' ? '#94a3b8' : g.type === 'molotov' ? '#f97316' : '#facc15'}
                      stroke="#ffffff"
                      strokeWidth="1"
                    />
                  </g>
                )
              }

              // Active Detonated Grenades
              if (isDetonated) {
                // 1. SMOKE GRENADE (20.0s duration in CS2)
                if (g.type === 'smoke') {
                  const remainingSec = Math.max(0, (g.end_tick - currentTick) / tickrate)
                  const totalDur = g.duration_seconds || 20.0
                  const ratio = Math.max(0, Math.min(1, remainingSec / totalDur))
                  const isDissipating = remainingSec <= 4.0
                  const radius = 38
                  const circumference = 2 * Math.PI * radius // ~238.76
                  const strokeDash = circumference * ratio

                  return (
                    <g
                      key={`smoke-${g.id}`}
                      pointerEvents="auto"
                      onMouseEnter={() => setHoveredGrenade(g)}
                      onMouseLeave={() => setHoveredGrenade(null)}
                      style={{ cursor: 'pointer' }}
                    >
                      {/* Volumetric Smoke Cloud Base */}
                      <circle
                        cx={gx}
                        cy={gy}
                        r={radius}
                        fill="url(#tactical-smoke-grad)"
                        opacity={isDissipating ? 0.45 : 0.85}
                        style={{
                          animation: isDissipating ? 'smokePulse 1.2s ease-in-out infinite' : undefined,
                        }}
                      />

                      {/* Subtle cloud billow rings */}
                      <circle cx={gx - 8} cy={gy - 6} r={radius * 0.72} fill="url(#tactical-smoke-grad)" opacity="0.5" />
                      <circle cx={gx + 8} cy={gy + 6} r={radius * 0.68} fill="url(#tactical-smoke-grad)" opacity="0.5" />

                      {/* Circular Countdown Progress Ring along circumference */}
                      <circle
                        cx={gx}
                        cy={gy}
                        r={radius}
                        fill="none"
                        stroke={isDissipating ? '#ef4444' : '#94a3b8'}
                        strokeWidth="2.2"
                        strokeDasharray={`${strokeDash} ${circumference}`}
                        strokeLinecap="round"
                        transform={`rotate(-90 ${gx} ${gy})`}
                        opacity={isDissipating ? 0.95 : 0.75}
                      />

                      {/* Center Smoke Badge & Remaining Seconds */}
                      <circle cx={gx} cy={gy} r="11" fill="rgba(15, 23, 42, 0.85)" stroke={isDissipating ? '#ef4444' : '#64748b'} strokeWidth="1" />
                      <text
                        x={gx}
                        y={gy + 3.5}
                        fill={isDissipating ? '#fca5a5' : '#f1f5f9'}
                        fontSize="9"
                        fontWeight="800"
                        fontFamily="monospace"
                        textAnchor="middle"
                      >
                        {Math.ceil(remainingSec)}s
                      </text>
                    </g>
                  )
                }

                // 2. MOLOTOV / INCENDIARY (7.03s duration in CS2)
                if (g.type === 'molotov') {
                  const remainingSec = Math.max(0, (g.end_tick - currentTick) / tickrate)
                  const totalDur = g.duration_seconds || 7.03
                  const ratio = Math.max(0, Math.min(1, remainingSec / totalDur))
                  const isExpiring = remainingSec <= 2.0
                  const radius = 28
                  const circumference = 2 * Math.PI * radius // ~175.93
                  const strokeDash = circumference * ratio

                  return (
                    <g
                      key={`molotov-${g.id}`}
                      pointerEvents="auto"
                      onMouseEnter={() => setHoveredGrenade(g)}
                      onMouseLeave={() => setHoveredGrenade(null)}
                      style={{ cursor: 'pointer' }}
                    >
                      {/* Fiery Fire Zone Circle */}
                      <circle
                        cx={gx}
                        cy={gy}
                        r={radius}
                        fill="url(#tactical-molotov-grad)"
                        opacity={isExpiring ? 0.5 : 0.85}
                        style={{
                          animation: 'fireGlow 1.5s ease-in-out infinite',
                        }}
                      />

                      {/* Fire Perimeter Countdown Ring */}
                      <circle
                        cx={gx}
                        cy={gy}
                        r={radius}
                        fill="none"
                        stroke={isExpiring ? '#dc2626' : '#f97316'}
                        strokeWidth="2.5"
                        strokeDasharray={`${strokeDash} ${circumference}`}
                        strokeLinecap="round"
                        transform={`rotate(-90 ${gx} ${gy})`}
                        opacity="0.9"
                      />

                      {/* Center Molotov Badge */}
                      <circle cx={gx} cy={gy} r="10" fill="rgba(24, 10, 10, 0.9)" stroke="#f97316" strokeWidth="1" />
                      <text
                        x={gx}
                        y={gy + 3.5}
                        fill="#fed7aa"
                        fontSize="8.5"
                        fontWeight="800"
                        fontFamily="monospace"
                        textAnchor="middle"
                      >
                        {remainingSec.toFixed(1)}s
                      </text>
                    </g>
                  )
                }

                // 3. FLASHBANG BURST (~1.2s post-detonation)
                if (g.type === 'flash') {
                  const elapsedSec = (currentTick - g.detonate_tick) / tickrate
                  if (elapsedSec >= 0 && elapsedSec <= 1.2) {
                    const radius = 10 + elapsedSec * 35
                    const opacity = Math.max(0, 1 - elapsedSec / 1.2) * 0.9
                    return (
                      <g key={`flash-${g.id}`}>
                        <circle cx={gx} cy={gy} r={radius} fill="url(#tactical-flash-grad)" opacity={opacity} />
                        <circle cx={gx} cy={gy} r={radius * 1.15} fill="none" stroke="#fef08a" strokeWidth="1.5" opacity={opacity * 0.8} />
                      </g>
                    )
                  }
                }

                // 4. HE GRENADE EXPLOSION SHOCKWAVE (~1.0s post-detonation)
                if (g.type === 'he') {
                  const elapsedSec = (currentTick - g.detonate_tick) / tickrate
                  if (elapsedSec >= 0 && elapsedSec <= 1.0) {
                    const radius = 12 + elapsedSec * 30
                    const opacity = Math.max(0, 1 - elapsedSec / 1.0) * 0.85
                    return (
                      <g key={`he-${g.id}`}>
                        <circle cx={gx} cy={gy} r={radius} fill="url(#tactical-he-grad)" opacity={opacity * 0.5} />
                        <circle cx={gx} cy={gy} r={radius} fill="none" stroke="#f97316" strokeWidth="2" strokeDasharray="4 2" opacity={opacity} />
                      </g>
                    )
                  }
                }
              }

              return null
            })}

          {/* Active Gunfire Muzzle Burst & Tracer Beams (Recent Kills Only) */}
          {showShots &&
            pastKills
              .filter((k) => {
                const dt = (currentTick - k.tick) / tickrate
                return dt >= 0 && dt <= 1.8
              })
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
                    r="12"
                    fill="rgba(250, 204, 21, 0.45)"
                    stroke="#facc15"
                    strokeWidth="2"
                  />
                </g>
              ))}

          {/* Kill Vector Lines: ONLY for recent kills (<= 3.5s) OR when hovering over a kill marker */}
          {pastKills
            .filter((k) => {
              const ageSec = (currentTick - k.tick) / tickrate
              return (ageSec >= 0 && ageSec <= 3.5) || (hoveredKill && hoveredKill.tick === k.tick)
            })
            .map((k, i) => {
              const ageSec = (currentTick - k.tick) / tickrate
              const opacity = hoveredKill?.tick === k.tick ? 0.95 : Math.max(0.2, (3.5 - ageSec) / 3.5)
              return (
                <line
                  key={`kill-line-${i}`}
                  x1={k.attacker_x * 10}
                  y1={k.attacker_y * 10}
                  x2={k.victim_x * 10}
                  y2={k.victim_y * 10}
                  stroke={k.attacker_side === 'ct' ? '#38bdf8' : '#f97316'}
                  strokeWidth={hoveredKill?.tick === k.tick ? '2.5' : '1.5'}
                  strokeDasharray="4 3"
                  opacity={opacity}
                />
              )
            })}
        </svg>

        {/* ================================================================= */}
        {/* LIVING PLAYERS (HTML OVERLAYS) — DEAD PLAYERS OMITTED             */}
        {/* ================================================================= */}
        {livingPlayers.map((p) => {
          const isCurrentLevel = hasMultipleLevels ? p.level === currentLevel : true
          const opacity = isCurrentLevel ? 1 : 0.22
          const isCT = p.side === 'ct'
          const color = isCT ? '#3b82f6' : '#f97316'

          return (
            <div
              key={p.steam_id}
              style={{
                position: 'absolute',
                left: `${Math.max(2, Math.min(98, p.x))}%`,
                top: `${Math.max(2, Math.min(98, p.y))}%`,
                transform: 'translate(-50%, -50%)',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                pointerEvents: 'none',
                opacity,
                transition: 'left 0.12s linear, top 0.12s linear, opacity 0.2s ease',
                zIndex: isCurrentLevel ? 15 : 2,
              }}
            >
              {/* Tactical Player Dot with Team Ring */}
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
                  fontWeight: 900,
                  color: '#ffffff',
                }}
              >
                {isCT ? 'CT' : 'T'}
              </div>

              {/* Player Name & Health Pill */}
              {isCurrentLevel && (
                <div
                  style={{
                    marginTop: '3px',
                    backgroundColor: 'rgba(9, 12, 18, 0.88)',
                    backdropFilter: 'blur(4px)',
                    padding: '1px 5px',
                    borderRadius: '4px',
                    border: `1px solid ${color}55`,
                    fontSize: '9.5px',
                    fontWeight: 700,
                    color: '#f1f5f9',
                    whiteSpace: 'nowrap',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    boxShadow: '0 2px 6px rgba(0,0,0,0.5)',
                  }}
                >
                  <span>{p.name.slice(0, 9)}</span>
                  <span
                    style={{
                      color: p.health >= 50 ? '#22c55e' : p.health >= 20 ? '#f59e0b' : '#ef4444',
                      fontSize: '9px',
                    }}
                  >
                    {Math.round(p.health)}
                  </span>
                </div>
              )}
            </div>
          )
        })}

        {/* ================================================================= */}
        {/* KILL MARKERS (TEMPORAL DECAY TO ELIMINATE CLUTTER)               */}
        {/* ================================================================= */}
        {pastKills.map((k, i) => {
          const ageSec = (currentTick - k.tick) / tickrate
          const isRecent = ageSec >= 0 && ageSec <= 3.5

          if (isRecent) {
            // RECENT KILL (<= 3.5 seconds): Active prominent death event with ping animation
            return (
              <div
                key={`kill-recent-${i}`}
                onClick={() => onJumpToTick?.(k.tick)}
                onMouseEnter={() => setHoveredKill(k)}
                onMouseLeave={() => setHoveredKill(null)}
                title={`💀 Килл: ${k.attacker_name} ➔ ${k.victim_name}. Клик для перехода`}
                style={{
                  position: 'absolute',
                  left: `${Math.max(2, Math.min(98, k.victim_x))}%`,
                  top: `${Math.max(2, Math.min(98, k.victim_y))}%`,
                  transform: 'translate(-50%, -50%)',
                  zIndex: 25,
                  cursor: 'pointer',
                  pointerEvents: 'auto',
                }}
              >
                {/* Expanding Pulsing Ping Ring */}
                <div
                  style={{
                    position: 'absolute',
                    top: '-6px',
                    left: '-6px',
                    width: '28px',
                    height: '28px',
                    borderRadius: '50%',
                    border: '2px solid #ef4444',
                    animation: 'radarPing 1.2s cubic-bezier(0, 0, 0.2, 1) infinite',
                    pointerEvents: 'none',
                  }}
                />

                {/* Main Kill Badge */}
                <div
                  style={{
                    width: '16px',
                    height: '16px',
                    borderRadius: '50%',
                    backgroundColor: '#ef4444',
                    border: '1.5px solid #ffffff',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    boxShadow: '0 0 10px rgba(239, 68, 68, 0.9)',
                  }}
                >
                  <SkullIcon size={10} color="#ffffff" />
                </div>
              </div>
            )
          }

          // HISTORICAL / OLDER KILL (> 3.5 seconds): Faint, unobtrusive tactical death marker
          return (
            <div
              key={`kill-past-${i}`}
              onClick={() => onJumpToTick?.(k.tick)}
              onMouseEnter={() => setHoveredKill(k)}
              onMouseLeave={() => setHoveredKill(null)}
              title={`💀 ${k.attacker_name} [${k.weapon || 'kill'}] ➔ ${k.victim_name}. Клик для перехода к тику`}
              style={{
                position: 'absolute',
                left: `${Math.max(2, Math.min(98, k.victim_x))}%`,
                top: `${Math.max(2, Math.min(98, k.victim_y))}%`,
                transform: hoveredKill === k ? 'translate(-50%, -50%) scale(1.3)' : 'translate(-50%, -50%)',
                width: '10px',
                height: '10px',
                borderRadius: '50%',
                backgroundColor: hoveredKill === k ? 'rgba(239, 68, 68, 0.9)' : 'rgba(15, 23, 42, 0.75)',
                border: hoveredKill === k ? '1.5px solid #ffffff' : '1px solid rgba(239, 68, 68, 0.45)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                opacity: hoveredKill === k ? 1 : 0.35,
                zIndex: hoveredKill === k ? 28 : 5,
                cursor: 'pointer',
                pointerEvents: 'auto',
                transition: 'all 0.15s ease',
              }}
            >
              <SkullIcon size={hoveredKill === k ? 7 : 6} color={hoveredKill === k ? '#ffffff' : '#f87171'} />
            </div>
          )
        })}
      </div>
    </div>
  )
}
