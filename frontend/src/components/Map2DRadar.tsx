import React, { useState, useMemo } from 'react'
import type { HighlightItem } from '../types'

interface Map2DRadarProps {
  mapName?: string | null
  highlights: HighlightItem[]
  selectedIds: Set<string>
  hoveredId: string | null
  onSelectHighlight: (id: string) => void
  activeRound?: number | null
}

interface MapMeta {
  displayName: string
  hasLevels: boolean
  radarFile: string
  radarFileLower?: string
  levels: string[]
  fallbackCenter: { x: number; y: number }
}

const MAP_CATALOG: Record<string, MapMeta> = {
  de_dust2: {
    displayName: 'Dust II',
    hasLevels: false,
    radarFile: 'de_dust2.png',
    levels: ['main'],
    fallbackCenter: { x: 500, y: 500 },
  },
  de_mirage: {
    displayName: 'Mirage',
    hasLevels: false,
    radarFile: 'de_mirage.png',
    levels: ['main'],
    fallbackCenter: { x: 500, y: 480 },
  },
  de_inferno: {
    displayName: 'Inferno',
    hasLevels: false,
    radarFile: 'de_inferno.png',
    levels: ['main'],
    fallbackCenter: { x: 520, y: 480 },
  },
  de_nuke: {
    displayName: 'Nuke',
    hasLevels: true,
    radarFile: 'de_nuke.png',
    radarFileLower: 'de_nuke_lower.png',
    levels: ['upper', 'lower'],
    fallbackCenter: { x: 510, y: 450 },
  },
  de_ancient: {
    displayName: 'Ancient',
    hasLevels: false,
    radarFile: 'de_ancient.png',
    levels: ['main'],
    fallbackCenter: { x: 500, y: 500 },
  },
  de_anubis: {
    displayName: 'Anubis',
    hasLevels: false,
    radarFile: 'de_anubis.png',
    levels: ['main'],
    fallbackCenter: { x: 490, y: 510 },
  },
  de_vertigo: {
    displayName: 'Vertigo',
    hasLevels: true,
    radarFile: 'de_vertigo.png',
    radarFileLower: 'de_vertigo_lower.png',
    levels: ['upper', 'lower'],
    fallbackCenter: { x: 510, y: 480 },
  },
  de_overpass: {
    displayName: 'Overpass',
    hasLevels: false,
    radarFile: 'de_overpass.png',
    levels: ['main'],
    fallbackCenter: { x: 500, y: 480 },
  },
  cs_office: {
    displayName: 'Office',
    hasLevels: false,
    radarFile: 'cs_office.png',
    levels: ['main'],
    fallbackCenter: { x: 500, y: 500 },
  },
  cs_italy: {
    displayName: 'Italy',
    hasLevels: false,
    radarFile: 'cs_italy.png',
    levels: ['main'],
    fallbackCenter: { x: 500, y: 500 },
  },
  de_train: {
    displayName: 'Train',
    hasLevels: true,
    radarFile: 'de_train.png',
    radarFileLower: 'de_train_lower.png',
    levels: ['upper', 'lower'],
    fallbackCenter: { x: 500, y: 500 },
  },
}

const DEFAULT_MAP_META = MAP_CATALOG['de_nuke']

export const Map2DRadar: React.FC<Map2DRadarProps> = ({
  mapName,
  highlights,
  selectedIds,
  hoveredId,
  onSelectHighlight,
  activeRound,
}) => {
  const [activeLevel, setActiveLevel] = useState<'upper' | 'lower'>('upper')
  const [zoom, setZoom] = useState<number>(1)
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 })
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 })

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

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault()
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

  const handleMouseDown = (e: React.MouseEvent) => {
    if (zoom > 1) {
      setIsDragging(true)
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y })
    }
  }

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging && zoom > 1) {
      const maxPan = (zoom - 1) * 200
      const nextX = Math.max(-maxPan, Math.min(maxPan, e.clientX - dragStart.x))
      const nextY = Math.max(-maxPan, Math.min(maxPan, e.clientY - dragStart.y))
      setPan({ x: nextX, y: nextY })
    }
  }

  const handleMouseUp = () => {
    setIsDragging(false)
  }

  // Resolve map metadata from official catalog
  const cleanMap = (mapName || 'de_nuke').toLowerCase().replace('workshop/', '').trim()
  const meta = MAP_CATALOG[cleanMap] || DEFAULT_MAP_META

  const radarImageUrl = useMemo(() => {
    if (activeLevel === 'lower' && meta.radarFileLower) {
      return `/maps/${meta.radarFileLower}`
    }
    return `/maps/${meta.radarFile}`
  }, [activeLevel, meta])

  // Get coordinates for highlight (use real coords if available, otherwise gentle jitter near center)
  const getHighlightPosition = (h: HighlightItem, idx: number) => {
    if (h.radar_x !== undefined && h.radar_x !== null && h.radar_y !== undefined && h.radar_y !== null) {
      return {
        x: h.radar_x * 10,
        y: h.radar_y * 10,
        level: h.radar_level || 'upper',
        hasRealCoords: true,
      }
    }

    // Fallback if coordinates missing: slight natural offset around map center
    const angle = ((h.round_num * 47 + idx * 83) % 360) * (Math.PI / 180)
    const dist = 60 + ((h.round_num * 19) % 180)
    const cx = meta.fallbackCenter.x
    const cy = meta.fallbackCenter.y
    return {
      x: Math.max(100, Math.min(900, cx + Math.cos(angle) * dist)),
      y: Math.max(100, Math.min(900, cy + Math.sin(angle) * dist)),
      level: (h.round_num % 2 === 0 && meta.hasLevels) ? 'lower' : 'upper',
      hasRealCoords: false,
    }
  }

  return (
    <div
      style={{
        position: 'relative',
        backgroundColor: '#111318',
        border: '1px solid #232734',
        borderRadius: '12px',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 8px 30px rgba(0, 0, 0, 0.45)',
      }}
    >
      {/* Radar Header Toolbar */}
      <div
        style={{
          padding: '12px 16px',
          borderBottom: '1px solid #232734',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          backgroundColor: '#161922',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" />
            <line x1="22" y1="12" x2="18" y2="12" />
            <line x1="6" y1="12" x2="2" y2="12" />
            <line x1="12" y1="6" x2="12" y2="2" />
            <line x1="12" y1="22" x2="12" y2="18" />
          </svg>
          <span style={{ fontWeight: 800, fontSize: '13px', color: '#f1f5f9', letterSpacing: '0.02em' }}>
            2D Tactical Radar — {meta.displayName}
          </span>
          <span
            style={{
              fontSize: '10px',
              fontWeight: 700,
              color: '#38bdf8',
              backgroundColor: 'rgba(56, 189, 248, 0.12)',
              border: '1px solid rgba(56, 189, 248, 0.3)',
              padding: '2px 7px',
              borderRadius: '4px',
              textTransform: 'uppercase',
            }}
          >
            Source 2
          </span>
          {activeRound !== null && activeRound !== undefined && (
            <span
              style={{
                fontSize: '11px',
                fontWeight: 700,
                color: '#f59e0b',
                backgroundColor: 'rgba(245, 158, 11, 0.12)',
                border: '1px solid rgba(245, 158, 11, 0.3)',
                padding: '2px 7px',
                borderRadius: '4px',
              }}
            >
              Раунд {activeRound}
            </span>
          )}
        </div>

        {meta.hasLevels ? (
          <div style={{ display: 'flex', gap: '4px', background: '#0e1015', padding: '3px', borderRadius: '6px', border: '1px solid #232734' }}>
            <button
              type="button"
              onClick={() => setActiveLevel('upper')}
              style={{
                padding: '3px 10px',
                fontSize: '11px',
                fontWeight: 700,
                backgroundColor: activeLevel === 'upper' ? 'rgba(56, 189, 248, 0.2)' : 'transparent',
                color: activeLevel === 'upper' ? '#38bdf8' : '#94a3b8',
                border: activeLevel === 'upper' ? '1px solid #38bdf8' : '1px solid transparent',
                borderRadius: '4px',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              Upper (A)
            </button>
            <button
              type="button"
              onClick={() => setActiveLevel('lower')}
              style={{
                padding: '3px 10px',
                fontSize: '11px',
                fontWeight: 700,
                backgroundColor: activeLevel === 'lower' ? 'rgba(56, 189, 248, 0.2)' : 'transparent',
                color: activeLevel === 'lower' ? '#38bdf8' : '#94a3b8',
                border: activeLevel === 'lower' ? '1px solid #38bdf8' : '1px solid transparent',
                borderRadius: '4px',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              Lower (B)
            </button>
          </div>
        ) : (
          <span style={{ fontSize: '11px', color: '#64748b', fontWeight: 600 }}>
            Калибровка 1:1
          </span>
        )}
      </div>

      {/* Map & SVG Overlay Canvas */}
      <div
        style={{
          position: 'relative',
          width: '100%',
          aspectRatio: '1 / 1',
          maxHeight: '480px',
          backgroundColor: '#0c0e13',
          overflow: 'hidden',
          cursor: zoom > 1 ? (isDragging ? 'grabbing' : 'grab') : 'default',
          userSelect: 'none',
        }}
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        {/* Floating Zoom Controls & Indicator */}
        <div
          style={{
            position: 'absolute',
            top: '10px',
            right: '10px',
            zIndex: 15,
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            backgroundColor: 'rgba(15, 20, 30, 0.92)',
            backdropFilter: 'blur(8px)',
            border: '1px solid rgba(56, 189, 248, 0.3)',
            borderRadius: '8px',
            padding: '3px 6px',
            boxShadow: '0 4px 14px rgba(0,0,0,0.5)',
          }}
        >
          <button
            type="button"
            onClick={handleZoomOut}
            disabled={zoom <= 1}
            title="Уменьшить масштаб (Колёсико мыши вниз)"
            style={{
              background: 'none',
              border: 'none',
              color: zoom <= 1 ? '#475569' : '#f1f5f9',
              fontSize: '15px',
              fontWeight: 700,
              cursor: zoom <= 1 ? 'not-allowed' : 'pointer',
              padding: '2px 6px',
              borderRadius: '4px',
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
              background: 'none',
              border: 'none',
              color: '#38bdf8',
              fontSize: '11px',
              fontWeight: 700,
              fontFamily: 'monospace',
              cursor: 'pointer',
              padding: '2px 4px',
            }}
          >
            {Math.round(zoom * 100)}%
          </button>
          <button
            type="button"
            onClick={handleZoomIn}
            disabled={zoom >= 3.5}
            title="Увеличить масштаб (Колёсико мыши вверх)"
            style={{
              background: 'none',
              border: 'none',
              color: zoom >= 3.5 ? '#475569' : '#f1f5f9',
              fontSize: '15px',
              fontWeight: 700,
              cursor: zoom >= 3.5 ? 'not-allowed' : 'pointer',
              padding: '2px 6px',
              borderRadius: '4px',
              lineHeight: 1,
            }}
          >
            +
          </button>
        </div>

        {/* Scaled and panned content container */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
            transformOrigin: 'center center',
            transition: isDragging ? 'none' : 'transform 0.15s cubic-bezier(0.2, 0.8, 0.2, 1)',
          }}
        >
          {/* Real Source 2 Radar Map PNG Backdrop */}
          <img
            src={radarImageUrl}
            alt={meta.displayName}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              objectFit: 'contain',
              pointerEvents: 'none',
              opacity: 0.94,
              filter: 'brightness(0.95) contrast(1.12)',
              zIndex: 1,
            }}
          />

          {/* SVG Tactical Vectors & Interactive Markers Overlay */}
          <svg
            viewBox="0 0 1000 1000"
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              zIndex: 2,
              display: 'block',
            }}
          >
            <defs>
              {/* Pulsing glow filter */}
              <filter id="radar-glow-filter" x="-40%" y="-40%" width="180%" height="180%">
              <feGaussianBlur stdDeviation="8" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* Concentric subtle distance rings */}
          <circle cx="500" cy="500" r="460" fill="none" stroke="#38bdf8" strokeWidth="0.8" strokeDasharray="6 6" opacity="0.12" pointerEvents="none" />
          <circle cx="500" cy="500" r="280" fill="none" stroke="#38bdf8" strokeWidth="0.8" strokeDasharray="6 6" opacity="0.1" pointerEvents="none" />

          {/* Kill Vector Lines for selected or hovered highlights */}
          {highlights.map((h, idx) => {
            const isSelected = selectedIds.has(h.id)
            const isHovered = hoveredId === h.id
            if (!isSelected && !isHovered) return null

            const pos = getHighlightPosition(h, idx)
            if (h.victim_radar_x !== undefined && h.victim_radar_x !== null && h.victim_radar_y !== undefined && h.victim_radar_y !== null) {
              const vx = h.victim_radar_x * 10
              const vy = h.victim_radar_y * 10
              return (
                <g key={`vector-${h.id}`} pointerEvents="none">
                  <line
                    x1={pos.x}
                    y1={pos.y}
                    x2={vx}
                    y2={vy}
                    stroke={isSelected ? '#a855f7' : '#38bdf8'}
                    strokeWidth="3"
                    strokeDasharray="6 3"
                    opacity="0.85"
                  />
                  <circle cx={vx} cy={vy} r="8" fill="#ef4444" opacity="0.8" />
                  <text x={vx} y={vy + 4} fill="#fff" fontSize="10" fontWeight="bold" textAnchor="middle">☠</text>
                </g>
              )
            }
            return null
          })}

          {/* Highlight Kill Markers */}
          {highlights.map((h, idx) => {
            const pos = getHighlightPosition(h, idx)
            const isSelected = selectedIds.has(h.id)
            const isHovered = hoveredId === h.id

            // Check if highlight belongs to current map level
            const isCurrentLevel = !meta.hasLevels || pos.level === activeLevel
            const opacity = isCurrentLevel ? 1 : 0.22

            const isAce = h.highlight_type === 'ace' || h.kill_count >= 5
            const isClutch = h.highlight_type === 'clutch_candidate'
            const isMultikill = h.kill_count >= 2

            // Colors: Gold for Ace, Emerald for Clutch, Purple for Multikill / Selected, Cyan for Solo Kill
            const baseColor = isAce
              ? '#f59e0b'
              : isClutch
              ? '#10b981'
              : isSelected
              ? '#a855f7'
              : isMultikill
              ? '#8b5cf6'
              : '#38bdf8'

            const radius = isHovered || isSelected ? 17 : 12

            return (
              <g
                key={h.id}
                transform={`translate(${pos.x}, ${pos.y})`}
                onClick={() => onSelectHighlight(h.id)}
                style={{ cursor: 'pointer', transition: 'transform 0.15s ease' }}
                opacity={opacity}
              >
                {/* Outer glowing halo ring on selection or hover */}
                {(isHovered || isSelected) && (
                  <circle
                    cx="0"
                    cy="0"
                    r={radius + 8}
                    fill="none"
                    stroke={baseColor}
                    strokeWidth="2.5"
                    opacity="0.7"
                    filter="url(#radar-glow-filter)"
                  />
                )}

                {/* Base Marker Circle */}
                <circle
                  cx="0"
                  cy="0"
                  r={radius}
                  fill={baseColor}
                  stroke="#ffffff"
                  strokeWidth={isSelected ? 3 : 1.8}
                  box-shadow="0 0 10px rgba(0,0,0,0.5)"
                />

                {/* Kill count icon or text badge */}
                <text
                  x="0"
                  y="4"
                  fill="#ffffff"
                  fontSize={h.kill_count > 1 ? '11' : '10'}
                  fontWeight="900"
                  fontFamily="system-ui, sans-serif"
                  textAnchor="middle"
                  pointerEvents="none"
                >
                  {h.kill_count > 1 ? `${h.kill_count}K` : '1K'}
                </text>

                {/* Interactive Tooltip Card on Hover */}
                {isHovered && (
                  <g transform="translate(0, -32)" pointerEvents="none">
                    <rect
                      x="-85"
                      y="-22"
                      width="170"
                      height="28"
                      rx="6"
                      fill="rgba(10, 12, 17, 0.96)"
                      stroke={baseColor}
                      strokeWidth="1.5"
                    />
                    <text
                      x="0"
                      y="-4"
                      fill="#f1f5f9"
                      fontSize="11"
                      fontWeight="700"
                      textAnchor="middle"
                    >
                      {h.pov_name || 'Player'} • {h.kill_count}K (R{h.round_num})
                    </text>
                  </g>
                )}
              </g>
            )
          })}
        </svg>
      </div>

        {/* Floating Legend / Stats Bar at bottom */}
        <div
          style={{
            position: 'absolute',
            bottom: '10px',
            left: '10px',
            right: '10px',
            backgroundColor: 'rgba(15, 17, 23, 0.88)',
            backdropFilter: 'blur(8px)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderRadius: '6px',
            padding: '6px 12px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontSize: '11px',
            color: '#94a3b8',
            zIndex: 10,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#f59e0b' }} />
              <span>ACE (5K)</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#8b5cf6' }} />
              <span>Multikill (2-4K)</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#38bdf8' }} />
              <span>1K Frag</span>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontWeight: 600 }}>
            <span>Всего: {highlights.length}</span>
            <span style={{ color: selectedIds.size > 0 ? '#38bdf8' : '#64748b' }}>
              Выбрано: {selectedIds.size}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
