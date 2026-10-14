import React, { useState } from 'react'

export type SimMapId = 'mirage' | 'inferno' | 'nuke' | 'dust2' | 'anubis'

export interface HudRadarScreenSimulatorProps {
  hudMode: 'huge_esports' | 'huge_killfeed' | 'full' | 'killfeed_only' | 'none'
  radarMode: 'dynamic_large' | 'broadcast_giant' | 'broadcast' | 'player_focus' | 'compact' | 'hidden'
  aspectRatio?: '16:9' | '4:3'
  mapName?: string
  onSelectPreset?: (preset: {
    hudMode: 'huge_esports' | 'huge_killfeed' | 'full' | 'killfeed_only' | 'none'
    radarMode: 'dynamic_large' | 'broadcast_giant' | 'broadcast' | 'player_focus' | 'compact' | 'hidden'
  }) => void
  onSelectMap?: (map: SimMapId) => void
}

interface MapVisualInfo {
  id: SimMapId
  name: string
  label: string
  desc: string
  gradient: string
  accentColor: string
  // Vector radar paths (scaled for 100x100 viewBox)
  radarPaths: string[]
  siteLabels: { x: number; y: number; text: string }[]
}

const MAPS_DATA: Record<SimMapId, MapVisualInfo> = {
  mirage: {
    id: 'mirage',
    name: 'de_mirage',
    label: '🏜️ Mirage',
    desc: 'Песчаные арки, А-плент и Дворец',
    gradient: 'radial-gradient(ellipse at 50% 45%, #59442a 0%, #2b2014 60%, #0d0a06 100%)',
    accentColor: '#f59e0b',
    radarPaths: [
      'M 20 25 L 35 25 L 42 40 L 30 50 Z', // B Site & Apps
      'M 45 35 L 55 35 L 55 58 L 45 58 Z', // Mid & Connector
      'M 60 45 L 85 45 L 82 72 L 58 70 Z', // A Site & Palace
      'M 35 75 L 55 75 L 55 88 L 35 88 Z', // T Spawn / Alley
    ],
    siteLabels: [
      { x: 74, y: 56, text: 'A' },
      { x: 28, y: 38, text: 'B' },
      { x: 50, y: 48, text: 'MID' },
    ],
  },
  inferno: {
    id: 'inferno',
    name: 'de_inferno',
    label: '🏰 Inferno',
    desc: 'Каменная брусчатка, Банан и Церковь',
    gradient: 'radial-gradient(ellipse at 50% 45%, #5a3d28 0%, #291a10 60%, #0e0906 100%)',
    accentColor: '#f97316',
    radarPaths: [
      'M 22 45 C 22 30 35 20 48 20 L 52 35 C 42 35 34 42 34 52 Z', // Banana curve
      'M 48 15 L 75 15 L 72 32 L 46 32 Z', // B Site & Church
      'M 40 60 L 78 60 L 78 82 L 40 82 Z', // A Site & Pit
      'M 20 85 L 38 85 L 38 95 L 20 95 Z', // T Spawn
    ],
    siteLabels: [
      { x: 62, y: 72, text: 'A' },
      { x: 60, y: 24, text: 'B' },
      { x: 28, y: 34, text: 'BAN' },
    ],
  },
  nuke: {
    id: 'nuke',
    name: 'de_nuke',
    label: '☢️ Nuke',
    desc: 'Индустриальный металл, Рампа и Силосы',
    gradient: 'radial-gradient(ellipse at 50% 45%, #2a3d52 0%, #131d28 60%, #06090e 100%)',
    accentColor: '#38bdf8',
    radarPaths: [
      'M 35 30 L 65 30 L 65 55 L 35 55 Z', // A Site & Hut
      'M 30 65 L 70 65 L 70 85 L 30 85 Z', // B Site & Vent
      'M 18 35 L 28 35 L 28 75 L 18 75 Z', // Outside / Yard
      'M 72 40 L 88 40 L 88 70 L 72 70 Z', // Ramp
    ],
    siteLabels: [
      { x: 50, y: 44, text: 'A' },
      { x: 50, y: 76, text: 'B' },
      { x: 80, y: 55, text: 'RAMP' },
    ],
  },
  dust2: {
    id: 'dust2',
    name: 'de_dust2',
    label: '⏳ Dust II',
    desc: 'Солнечный Long, Mid двери и Коробка',
    gradient: 'radial-gradient(ellipse at 50% 45%, #6e583b 0%, #342817 60%, #120e08 100%)',
    accentColor: '#eab308',
    radarPaths: [
      'M 68 20 L 86 20 L 86 65 L 72 65 Z', // Long A & Pit
      'M 45 35 L 60 35 L 60 55 L 45 55 Z', // Mid Doors & Short
      'M 15 25 L 38 25 L 35 48 L 15 48 Z', // B Site & Tunnels
      'M 35 75 L 60 75 L 55 92 L 35 92 Z', // T Spawn
    ],
    siteLabels: [
      { x: 78, y: 35, text: 'A' },
      { x: 26, y: 36, text: 'B' },
      { x: 52, y: 46, text: 'MID' },
    ],
  },
  anubis: {
    id: 'anubis',
    name: 'de_anubis',
    label: '🏺 Anubis',
    desc: 'Водный канал, Древний храм и Руины',
    gradient: 'radial-gradient(ellipse at 50% 45%, #2a4c4a 0%, #112626 60%, #050d0d 100%)',
    accentColor: '#2dd4bf',
    radarPaths: [
      'M 20 30 L 40 30 L 40 55 L 20 55 Z', // B Site & Ruins
      'M 45 25 L 55 25 L 55 75 L 45 75 Z', // Canal & Bridge
      'M 60 35 L 85 35 L 80 60 L 60 60 Z', // A Site & Temple
      'M 35 80 L 65 80 L 60 95 L 35 95 Z', // T Spawn
    ],
    siteLabels: [
      { x: 72, y: 48, text: 'A' },
      { x: 30, y: 42, text: 'B' },
      { x: 50, y: 52, text: 'CANAL' },
    ],
  },
}

export const HudRadarScreenSimulator: React.FC<HudRadarScreenSimulatorProps> = ({
  hudMode,
  radarMode,
  aspectRatio = '16:9',
  mapName,
  onSelectPreset,
  onSelectMap,
}) => {
  const [compareMode, setCompareMode] = useState<'current' | 'compare_old'>('current')
  const [activeMapId, setActiveMapId] = useState<SimMapId>(() => {
    const raw = (mapName || '').toLowerCase()
    if (raw.includes('inferno')) return 'inferno'
    if (raw.includes('nuke')) return 'nuke'
    if (raw.includes('dust')) return 'dust2'
    if (raw.includes('anubis')) return 'anubis'
    return 'mirage'
  })
  const [showScreenshotGallery, setShowScreenshotGallery] = useState(false)

  // When comparing to old mode:
  const activeHud = compareMode === 'compare_old' ? 'full' : hudMode
  const activeRadar = compareMode === 'compare_old' ? 'broadcast' : radarMode

  const isHugeHud = activeHud === 'huge_esports' || activeHud === 'huge_killfeed'
  const isHugeRadar = activeRadar === 'dynamic_large' || activeRadar === 'broadcast_giant'
  const isMovingRadar = activeRadar === 'dynamic_large' || activeRadar === 'player_focus'

  const currentMap = MAPS_DATA[activeMapId] || MAPS_DATA.mirage

  const handleMapChange = (id: SimMapId) => {
    setActiveMapId(id)
    if (onSelectMap) onSelectMap(id)
  }

  return (
    <div
      style={{
        backgroundColor: '#0d1117',
        border: '1px solid #232836',
        borderRadius: '14px',
        padding: '16px',
        marginBottom: '20px',
      }}
    >
      {/* Top Header & Comparison Controls */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '10px',
          flexWrap: 'wrap',
          gap: '8px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '16px' }}>📺</span>
          <span style={{ fontSize: '13px', fontWeight: 700, color: '#f1f5f9' }}>
            Интерактивный симулятор экрана CS2
          </span>
          <span
            style={{
              fontSize: '10px',
              fontWeight: 800,
              padding: '2px 6px',
              borderRadius: '4px',
              backgroundColor: isHugeHud ? 'rgba(56, 189, 248, 0.2)' : 'rgba(255, 255, 255, 0.08)',
              color: isHugeHud ? '#38bdf8' : '#94a3b8',
              border: `1px solid ${isHugeHud ? 'rgba(56, 189, 248, 0.4)' : '#2d3345'}`,
            }}
          >
            {isHugeHud ? '🔥 115% МАСШТАБ HUD' : '95% СТАНДАРТ'}
          </span>
        </div>

        {/* Buttons: Comparison & Screenshot Showcase */}
        <div style={{ display: 'flex', gap: '6px' }}>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => setShowScreenshotGallery(!showScreenshotGallery)}
            style={{
              padding: '4px 10px',
              fontSize: '11px',
              backgroundColor: showScreenshotGallery ? 'rgba(245, 158, 11, 0.2)' : 'rgba(255, 255, 255, 0.05)',
              borderColor: showScreenshotGallery ? '#f59e0b' : '#334155',
              color: showScreenshotGallery ? '#fbbf24' : '#cbd5e1',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              fontWeight: 600,
            }}
            title="Посмотреть визуальные примеры и скриншоты каждого режима"
          >
            <span>📸 Примеры со скриншотами</span>
          </button>

          <button
            type="button"
            className={compareMode === 'current' ? 'btn btn-primary' : 'btn btn-secondary'}
            onClick={() => setCompareMode('current')}
            style={{ padding: '4px 8px', fontSize: '11px', display: 'flex', alignItems: 'center', gap: '4px' }}
          >
            <span>🟢 Выбранный</span>
          </button>

          <button
            type="button"
            className={compareMode === 'compare_old' ? 'btn btn-primary' : 'btn btn-secondary'}
            onClick={() => setCompareMode('compare_old')}
            style={{ padding: '4px 8px', fontSize: '11px', display: 'flex', alignItems: 'center', gap: '4px' }}
            title="Сравнить со стандартным мелким CS2 HUD"
          >
            <span>🔴 Как было</span>
          </button>
        </div>
      </div>

      {/* Map Selector Pills */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          marginBottom: '12px',
          overflowX: 'auto',
          paddingBottom: '4px',
        }}
      >
        <span style={{ fontSize: '11px', color: '#64748b', fontWeight: 600, marginRight: '4px' }}>
          Карта:
        </span>
        {(Object.keys(MAPS_DATA) as SimMapId[]).map((mId) => {
          const m = MAPS_DATA[mId]
          const isAct = activeMapId === mId
          return (
            <button
              key={mId}
              type="button"
              onClick={() => handleMapChange(mId)}
              style={{
                padding: '3px 10px',
                fontSize: '11px',
                fontWeight: isAct ? 700 : 500,
                borderRadius: '6px',
                border: '1px solid',
                borderColor: isAct ? m.accentColor : '#232838',
                backgroundColor: isAct ? 'rgba(255, 255, 255, 0.12)' : 'rgba(15, 20, 30, 0.6)',
                color: isAct ? '#f1f5f9' : '#94a3b8',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
                transition: 'all 0.15s ease',
              }}
            >
              {m.label}
            </button>
          )
        })}
      </div>

      {/* Screen Viewport Mockup (Dynamic 16:9 or 4:3 CS2) */}
      <div
        style={{
          position: 'relative',
          width: '100%',
          aspectRatio: aspectRatio === '4:3' ? '4 / 3' : '16 / 9',
          maxHeight: '340px',
          margin: '0 auto',
          borderRadius: '10px',
          overflow: 'hidden',
          backgroundColor: '#0a0d14',
          border: '1px solid #1e2433',
          boxShadow: 'inset 0 0 40px rgba(0,0,0,0.8), 0 8px 24px rgba(0,0,0,0.5)',
          background: currentMap.gradient,
          transition: 'background 0.4s ease',
        }}
      >
        {/* Scenic Map Architectural Silhouettes */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            opacity: 0.25,
            pointerEvents: 'none',
          }}
        >
          {activeMapId === 'mirage' && (
            <svg width="100%" height="100%" viewBox="0 0 800 450" preserveAspectRatio="none">
              <polygon points="120,450 120,240 280,240 280,450" fill="#000" opacity="0.5" />
              <polygon points="500,450 500,200 680,200 680,450" fill="#000" opacity="0.6" />
              <polygon points="290,320 480,320 480,450 290,450" fill="#000" opacity="0.4" />
            </svg>
          )}
          {activeMapId === 'inferno' && (
            <svg width="100%" height="100%" viewBox="0 0 800 450" preserveAspectRatio="none">
              <path d="M 0 450 L 0 280 C 120 280 180 200 320 200 L 320 450 Z" fill="#000" opacity="0.55" />
              <polygon points="520,450 520,180 720,180 720,450" fill="#000" opacity="0.5" />
            </svg>
          )}
          {activeMapId === 'nuke' && (
            <svg width="100%" height="100%" viewBox="0 0 800 450" preserveAspectRatio="none">
              <circle cx="180" cy="300" r="140" fill="#000" opacity="0.5" />
              <polygon points="450,450 450,150 700,150 700,450" fill="#000" opacity="0.6" />
              <line x1="0" y1="260" x2="800" y2="260" stroke="#38bdf8" strokeWidth="2" opacity="0.2" />
            </svg>
          )}
          {activeMapId === 'dust2' && (
            <svg width="100%" height="100%" viewBox="0 0 800 450" preserveAspectRatio="none">
              <polygon points="80,450 80,180 260,180 260,450" fill="#000" opacity="0.5" />
              <polygon points="550,450 550,220 760,220 760,450" fill="#000" opacity="0.55" />
            </svg>
          )}
          {activeMapId === 'anubis' && (
            <svg width="100%" height="100%" viewBox="0 0 800 450" preserveAspectRatio="none">
              <polygon points="100,450 100,200 300,200 300,450" fill="#000" opacity="0.5" />
              <polygon points="500,450 500,220 700,220 700,450" fill="#000" opacity="0.5" />
            </svg>
          )}
        </div>

        {/* Subtle grid pattern resembling CS2 crosshair grid */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            opacity: 0.1,
            backgroundImage:
              'linear-gradient(#38bdf8 1px, transparent 1px), linear-gradient(90deg, #38bdf8 1px, transparent 1px)',
            backgroundSize: '40px 40px',
            pointerEvents: 'none',
          }}
        />

        {/* Center Crosshair Simulator */}
        <div
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            pointerEvents: 'none',
            zIndex: 3,
          }}
        >
          <div style={{ position: 'relative', width: '16px', height: '16px' }}>
            <div style={{ position: 'absolute', top: '7px', left: '0', width: '5px', height: '2px', backgroundColor: '#00ffb4' }} />
            <div style={{ position: 'absolute', top: '7px', right: '0', width: '5px', height: '2px', backgroundColor: '#00ffb4' }} />
            <div style={{ position: 'absolute', left: '7px', top: '0', width: '2px', height: '5px', backgroundColor: '#00ffb4' }} />
            <div style={{ position: 'absolute', left: '7px', bottom: '0', width: '2px', height: '5px', backgroundColor: '#00ffb4' }} />
          </div>
        </div>

        {/* 1. TOP-LEFT: RADAR / MINIMAP */}
        {activeRadar !== 'hidden' && (
          <div
            style={{
              position: 'absolute',
              top: '12px',
              left: '12px',
              width: isHugeRadar ? '112px' : '78px',
              height: isHugeRadar ? '112px' : '78px',
              borderRadius: '50%',
              backgroundColor: 'rgba(10, 15, 24, 0.92)',
              border: `2px solid ${isHugeRadar ? '#38bdf8' : '#475569'}`,
              boxShadow: isHugeRadar ? '0 0 18px rgba(56, 189, 248, 0.45)' : 'none',
              overflow: 'hidden',
              transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
              zIndex: 4,
            }}
          >
            {/* Radar Content Container */}
            <div
              style={{
                position: 'relative',
                width: '100%',
                height: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              {/* Authentic 2D Vector Minimap Lines of the chosen map */}
              <svg
                viewBox="0 0 100 100"
                style={{
                  position: 'absolute',
                  inset: 0,
                  width: '100%',
                  height: '100%',
                  transform: isMovingRadar ? 'rotate(28deg)' : 'none',
                  transition: 'transform 0.4s ease',
                  opacity: 0.75,
                }}
              >
                {currentMap.radarPaths.map((d, idx) => (
                  <path
                    key={idx}
                    d={d}
                    fill="rgba(56, 189, 248, 0.08)"
                    stroke={isHugeRadar ? 'rgba(56, 189, 248, 0.5)' : 'rgba(148, 163, 184, 0.4)'}
                    strokeWidth="1.5"
                  />
                ))}

                {/* Site labels A & B on map */}
                {currentMap.siteLabels.map((lbl, idx) => (
                  <text
                    key={idx}
                    x={lbl.x}
                    y={lbl.y}
                    fill={isHugeRadar ? '#38bdf8' : '#cbd5e1'}
                    fontSize="7"
                    fontWeight="900"
                    textAnchor="middle"
                  >
                    {lbl.text}
                  </text>
                ))}
              </svg>

              {/* Rotating compass grid */}
              <div
                style={{
                  position: 'absolute',
                  inset: 0,
                  border: '1px dashed rgba(56, 189, 248, 0.25)',
                  borderRadius: '50%',
                }}
              />

              {/* Player Icon at center */}
              <div
                style={{
                  width: isHugeRadar ? '12px' : '9px',
                  height: isHugeRadar ? '12px' : '9px',
                  backgroundColor: '#38bdf8',
                  borderRadius: '50%',
                  position: 'relative',
                  boxShadow: '0 0 8px #38bdf8',
                  zIndex: 2,
                }}
              >
                {/* Vision Cone */}
                <div
                  style={{
                    position: 'absolute',
                    top: '-18px',
                    left: '-7px',
                    width: 0,
                    height: 0,
                    borderLeft: '13px solid transparent',
                    borderRight: '13px solid transparent',
                    borderBottom: '18px solid rgba(56, 189, 248, 0.4)',
                    transform: isMovingRadar ? 'rotate(15deg)' : 'none',
                  }}
                />
              </div>

              {/* Red Enemy Blips */}
              <div
                style={{
                  position: 'absolute',
                  top: isHugeRadar ? '24px' : '16px',
                  right: isHugeRadar ? '28px' : '18px',
                  width: isHugeRadar ? '9px' : '6px',
                  height: isHugeRadar ? '9px' : '6px',
                  backgroundColor: '#ef4444',
                  borderRadius: '50%',
                  boxShadow: '0 0 8px #ef4444',
                  animation: 'pulse 1.5s infinite',
                  zIndex: 2,
                }}
              />
              <div
                style={{
                  position: 'absolute',
                  bottom: isHugeRadar ? '28px' : '20px',
                  left: isHugeRadar ? '24px' : '16px',
                  width: isHugeRadar ? '8px' : '5px',
                  height: isHugeRadar ? '8px' : '5px',
                  backgroundColor: '#ef4444',
                  borderRadius: '50%',
                  boxShadow: '0 0 6px #ef4444',
                  zIndex: 2,
                }}
              />

              {/* Teammate Blip */}
              <div
                style={{
                  position: 'absolute',
                  bottom: isHugeRadar ? '22px' : '14px',
                  right: isHugeRadar ? '38px' : '26px',
                  width: isHugeRadar ? '8px' : '5px',
                  height: isHugeRadar ? '8px' : '5px',
                  backgroundColor: '#22c55e',
                  borderRadius: '50%',
                  zIndex: 2,
                }}
              />

              {/* Radar Mode Pill */}
              <div
                style={{
                  position: 'absolute',
                  bottom: '4px',
                  fontSize: isHugeRadar ? '8px' : '6px',
                  fontWeight: 800,
                  color: isHugeRadar ? '#38bdf8' : '#94a3b8',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  backgroundColor: 'rgba(0,0,0,0.7)',
                  padding: '1px 5px',
                  borderRadius: '3px',
                  zIndex: 3,
                }}
              >
                {isMovingRadar ? 'LIVE 130% DYNAMIC' : 'STATIC 130% BLAST'}
              </div>
            </div>
          </div>
        )}

        {/* 2. TOP-CENTER: MATCH & TEAM STATUS (SPECTATOR BARS) */}
        {(activeHud === 'huge_esports' || activeHud === 'full') && (
          <div
            style={{
              position: 'absolute',
              top: '8px',
              left: '50%',
              transform: 'translateX(-50%)',
              display: 'flex',
              alignItems: 'center',
              gap: isHugeHud ? '12px' : '8px',
              backgroundColor: 'rgba(15, 20, 28, 0.9)',
              padding: isHugeHud ? '6px 14px' : '4px 10px',
              borderRadius: '8px',
              border: '1px solid rgba(255, 255, 255, 0.12)',
              backdropFilter: 'blur(4px)',
              zIndex: 4,
            }}
          >
            {/* CT Team Score */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div style={{ fontSize: isHugeHud ? '11px' : '9px', fontWeight: 800, color: '#38bdf8' }}>CT</div>
              <div style={{ fontSize: isHugeHud ? '16px' : '13px', fontWeight: 900, color: '#f1f5f9' }}>12</div>
            </div>

            {/* Timer */}
            <div
              style={{
                fontSize: isHugeHud ? '12px' : '10px',
                fontWeight: 700,
                color: '#fbbf24',
                padding: '0 4px',
              }}
            >
              1:24
            </div>

            {/* T Team Score */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div style={{ fontSize: isHugeHud ? '16px' : '13px', fontWeight: 900, color: '#f1f5f9' }}>9</div>
              <div style={{ fontSize: isHugeHud ? '11px' : '9px', fontWeight: 800, color: '#f59e0b' }}>TERROR</div>
            </div>
          </div>
        )}

        {/* 3. TOP-RIGHT: KILLFEED (DEATHNOTICES) */}
        {activeHud !== 'none' && (
          <div
            style={{
              position: 'absolute',
              top: '12px',
              right: '12px',
              display: 'flex',
              flexDirection: 'column',
              gap: isHugeHud ? '6px' : '3px',
              alignItems: 'flex-end',
              zIndex: 4,
            }}
          >
            {/* Kill Item 1 */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: isHugeHud ? '8px' : '5px',
                backgroundColor: 'rgba(12, 16, 24, 0.94)',
                borderLeft: '3px solid #38bdf8',
                borderRadius: '4px',
                padding: isHugeHud ? '6px 12px' : '3px 6px',
                boxShadow: isHugeHud ? '0 4px 14px rgba(0,0,0,0.7)' : 'none',
                transform: isHugeHud ? 'scale(1.12)' : 'scale(1)',
                transformOrigin: 'right center',
                transition: 'all 0.2s ease',
              }}
            >
              <span style={{ fontSize: isHugeHud ? '12px' : '9px', fontWeight: 800, color: '#38bdf8' }}>s1mple</span>
              <span style={{ fontSize: isHugeHud ? '13px' : '10px' }}>🔫 AK-47</span>
              <span
                style={{
                  fontSize: isHugeHud ? '10px' : '8px',
                  fontWeight: 800,
                  color: '#ef4444',
                  backgroundColor: 'rgba(239, 68, 68, 0.2)',
                  padding: '1px 3px',
                  borderRadius: '2px',
                }}
              >
                💥 HS
              </span>
              <span style={{ fontSize: isHugeHud ? '12px' : '9px', fontWeight: 800, color: '#f59e0b' }}>ZywOo</span>
            </div>

            {/* Kill Item 2 */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: isHugeHud ? '8px' : '5px',
                backgroundColor: 'rgba(12, 16, 24, 0.94)',
                borderLeft: '3px solid #38bdf8',
                borderRadius: '4px',
                padding: isHugeHud ? '6px 12px' : '3px 6px',
                transform: isHugeHud ? 'scale(1.12)' : 'scale(1)',
                transformOrigin: 'right center',
                transition: 'all 0.2s ease',
              }}
            >
              <span style={{ fontSize: isHugeHud ? '12px' : '9px', fontWeight: 800, color: '#38bdf8' }}>s1mple</span>
              <span style={{ fontSize: isHugeHud ? '13px' : '10px' }}>🎯 AWP</span>
              <span style={{ fontSize: isHugeHud ? '12px' : '9px', fontWeight: 800, color: '#f59e0b' }}>NiKo</span>
            </div>
          </div>
        )}

        {/* 4. BOTTOM CORNERS: HEALTH & AMMO */}
        {(activeHud === 'huge_esports' || activeHud === 'full') && (
          <>
            {/* Health Bottom-Left */}
            <div
              style={{
                position: 'absolute',
                bottom: '12px',
                left: '14px',
                display: 'flex',
                alignItems: 'center',
                gap: isHugeHud ? '8px' : '5px',
                backgroundColor: 'rgba(10, 15, 24, 0.9)',
                padding: isHugeHud ? '6px 12px' : '4px 8px',
                borderRadius: '6px',
                border: '1px solid rgba(255, 255, 255, 0.12)',
                zIndex: 4,
              }}
            >
              <span style={{ color: '#22c55e', fontSize: isHugeHud ? '14px' : '11px', fontWeight: 900 }}>+</span>
              <span style={{ color: '#f1f5f9', fontSize: isHugeHud ? '18px' : '13px', fontWeight: 900 }}>100</span>
            </div>

            {/* Ammo Bottom-Right */}
            <div
              style={{
                position: 'absolute',
                bottom: '12px',
                right: '14px',
                display: 'flex',
                alignItems: 'center',
                gap: isHugeHud ? '6px' : '4px',
                backgroundColor: 'rgba(10, 15, 24, 0.9)',
                padding: isHugeHud ? '6px 12px' : '4px 8px',
                borderRadius: '6px',
                border: '1px solid rgba(255, 255, 255, 0.12)',
                zIndex: 4,
              }}
            >
              <span style={{ color: '#f1f5f9', fontSize: isHugeHud ? '18px' : '13px', fontWeight: 900 }}>30</span>
              <span style={{ color: '#64748b', fontSize: isHugeHud ? '12px' : '10px' }}>/ 90</span>
            </div>
          </>
        )}

        {/* Watermark mode info at bottom center */}
        <div
          style={{
            position: 'absolute',
            bottom: '6px',
            left: '50%',
            transform: 'translateX(-50%)',
            fontSize: '10px',
            color: 'rgba(255, 255, 255, 0.45)',
            letterSpacing: '0.05em',
            textTransform: 'uppercase',
            zIndex: 4,
          }}
        >
          {compareMode === 'compare_old'
            ? 'РЕЖИМ СРАВНЕНИЯ: СТАНДАРТНЫЙ МЕЛКИЙ CS2'
            : `${currentMap.name.toUpperCase()} • ${isHugeHud ? 'HUGE ESPORTS HUD (115%)' : 'STANDARD HUD'}`}
        </div>
      </div>

      {/* Preset 1-Click Cards */}
      {onSelectPreset && (
        <div style={{ marginTop: '14px' }}>
          <div style={{ fontSize: '11px', fontWeight: 700, color: '#94a3b8', marginBottom: '8px', textTransform: 'uppercase' }}>
            ⚡ Быстрые пресеты визуальной видимости:
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '8px' }}>
            <button
              type="button"
              className={`btn ${hudMode === 'huge_esports' && radarMode === 'dynamic_large' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => onSelectPreset({ hudMode: 'huge_esports', radarMode: 'dynamic_large' })}
              style={{ textAlign: 'left', padding: '8px 10px' }}
            >
              <div style={{ fontWeight: 800, fontSize: '12px', color: '#38bdf8' }}>
                🔥 Макс. Видимость (130%)
              </div>
              <div style={{ fontSize: '10px', opacity: 0.8 }}>
                Огромный HUD 1.15x + Вращающийся радар
              </div>
            </button>

            <button
              type="button"
              className={`btn ${hudMode === 'huge_killfeed' && radarMode === 'dynamic_large' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => onSelectPreset({ hudMode: 'huge_killfeed', radarMode: 'dynamic_large' })}
              style={{ textAlign: 'left', padding: '8px 10px' }}
            >
              <div style={{ fontWeight: 800, fontSize: '12px', color: '#fbbf24' }}>
                ⚡ Огромный Киллфид
              </div>
              <div style={{ fontSize: '10px', opacity: 0.8 }}>
                Крупные фраги + Динамический радар
              </div>
            </button>

            <button
              type="button"
              className={`btn ${hudMode === 'huge_esports' && radarMode === 'broadcast_giant' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => onSelectPreset({ hudMode: 'huge_esports', radarMode: 'broadcast_giant' })}
              style={{ textAlign: 'left', padding: '8px 10px' }}
            >
              <div style={{ fontWeight: 800, fontSize: '12px', color: '#a78bfa' }}>
                📡 Pro Tournament (BLAST)
              </div>
              <div style={{ fontSize: '10px', opacity: 0.8 }}>
                Вся карта 130% обзор + Крупный HUD
              </div>
            </button>

            <button
              type="button"
              className={`btn ${hudMode === 'none' && radarMode === 'hidden' ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => onSelectPreset({ hudMode: 'none', radarMode: 'hidden' })}
              style={{ textAlign: 'left', padding: '8px 10px' }}
            >
              <div style={{ fontWeight: 800, fontSize: '12px', color: '#94a3b8' }}>
                🎬 Чистый Синематик
              </div>
              <div style={{ fontSize: '10px', opacity: 0.8 }}>
                Без худа и без карты (No-HUD)
              </div>
            </button>
          </div>
        </div>
      )}

      {/* Visual Examples Showcase Modal / Drawer */}
      {showScreenshotGallery && (
        <div
          style={{
            marginTop: '16px',
            backgroundColor: '#121622',
            border: '1px solid #2d3852',
            borderRadius: '12px',
            padding: '16px',
            animation: 'fadeIn 0.2s ease',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <div>
              <div style={{ fontSize: '14px', fontWeight: 800, color: '#f1f5f9' }}>
                📸 Наглядные примеры режимов в CS2 (Скриншоты и параметры)
              </div>
              <div style={{ fontSize: '11px', color: '#94a3b8' }}>
                Реальные параметры CS2 консоли и как они выглядят в готовом ролике
              </div>
            </div>
            <button
              type="button"
              onClick={() => setShowScreenshotGallery(false)}
              style={{ background: 'none', border: 'none', color: '#94a3b8', fontSize: '18px', cursor: 'pointer' }}
            >
              ✕
            </button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '14px' }}>
            {/* Card 1: Макс. Видимость */}
            <div
              style={{
                backgroundColor: '#161b28',
                border: '1px solid #232c42',
                borderRadius: '8px',
                padding: '12px',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '13px', fontWeight: 800, color: '#38bdf8' }}>
                  🔥 Огромный киберспорт (130%)
                </span>
                <span style={{ fontSize: '10px', backgroundColor: '#0284c733', color: '#38bdf8', padding: '1px 5px', borderRadius: '4px', fontWeight: 700 }}>
                  ТОП ДЛЯ КЛИПОВ
                </span>
              </div>
              {/* Mini visual mockup */}
              <div
                style={{
                  height: '90px',
                  backgroundColor: '#0a0d14',
                  borderRadius: '6px',
                  border: '1px solid #1e2536',
                  position: 'relative',
                  overflow: 'hidden',
                  background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
                }}
              >
                {/* 130% Glowing radar */}
                <div style={{ position: 'absolute', top: '6px', left: '6px', width: '38px', height: '38px', borderRadius: '50%', border: '2px solid #38bdf8', backgroundColor: '#0f172a' }}>
                  <div style={{ position: 'absolute', top: '16px', left: '16px', width: '6px', height: '6px', backgroundColor: '#38bdf8', borderRadius: '50%' }} />
                </div>
                {/* Huge Killfeed */}
                <div style={{ position: 'absolute', top: '6px', right: '6px', backgroundColor: '#0f172a', borderLeft: '2px solid #38bdf8', padding: '2px 6px', fontSize: '8px', color: '#f1f5f9', fontWeight: 700, borderRadius: '2px' }}>
                  s1mple 🔫 AK-47 💥 ZywOo
                </div>
                {/* Health & Ammo */}
                <div style={{ position: 'absolute', bottom: '4px', left: '6px', fontSize: '8px', color: '#22c55e', fontWeight: 900 }}>+ 100</div>
                <div style={{ position: 'absolute', bottom: '4px', right: '6px', fontSize: '8px', color: '#f1f5f9', fontWeight: 900 }}>30 / 90</div>
              </div>
              <div style={{ fontSize: '11px', color: '#cbd5e1' }}>
                Радар увеличен на 30%, динамически вращается по прицелу, фраги в киллфиде увеличены, аватары и HP четко читаются с экрана смартфона.
              </div>
              <div style={{ fontSize: '10px', color: '#64748b', fontFamily: 'monospace' }}>
                cl_hud_radar_scale 1.30; hud_scaling 1.15
              </div>
              {onSelectPreset && (
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => {
                    onSelectPreset({ hudMode: 'huge_esports', radarMode: 'dynamic_large' })
                    setShowScreenshotGallery(false)
                  }}
                  style={{ padding: '4px 8px', fontSize: '11px', marginTop: 'auto' }}
                >
                  Применить этот режим
                </button>
              )}
            </div>

            {/* Card 2: Pro BLAST Tournament */}
            <div
              style={{
                backgroundColor: '#161b28',
                border: '1px solid #232c42',
                borderRadius: '8px',
                padding: '12px',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '13px', fontWeight: 800, color: '#a78bfa' }}>
                  📡 Pro Tournament (BLAST)
                </span>
                <span style={{ fontSize: '10px', backgroundColor: '#7c3aed33', color: '#c084fc', padding: '1px 5px', borderRadius: '4px', fontWeight: 700 }}>
                  ESL / BLAST
                </span>
              </div>
              {/* Mini visual mockup */}
              <div
                style={{
                  height: '90px',
                  backgroundColor: '#0a0d14',
                  borderRadius: '6px',
                  border: '1px solid #1e2536',
                  position: 'relative',
                  overflow: 'hidden',
                  background: 'linear-gradient(135deg, #1a1e2d 0%, #0d101a 100%)',
                }}
              >
                {/* 130% Static Radar */}
                <div style={{ position: 'absolute', top: '6px', left: '6px', width: '38px', height: '38px', borderRadius: '50%', border: '2px solid #a78bfa', backgroundColor: '#0f172a' }}>
                  <div style={{ position: 'absolute', top: '4px', left: '16px', fontSize: '6px', color: '#a78bfa', fontWeight: 900 }}>N</div>
                </div>
                {/* Match score bar */}
                <div style={{ position: 'absolute', top: '4px', left: '50%', transform: 'translateX(-50%)', backgroundColor: '#0f172a', padding: '1px 8px', fontSize: '7px', color: '#f1f5f9', fontWeight: 800, borderRadius: '4px' }}>
                  CT 12 : 9 T
                </div>
                {/* Killfeed */}
                <div style={{ position: 'absolute', top: '6px', right: '6px', backgroundColor: '#0f172a', borderLeft: '2px solid #38bdf8', padding: '2px 6px', fontSize: '8px', color: '#f1f5f9', fontWeight: 700, borderRadius: '2px' }}>
                  m0NESY 🎯 AWP b1t
                </div>
              </div>
              <div style={{ fontSize: '11px', color: '#cbd5e1' }}>
                Официальный турнирный радар трансляций BLAST. Зафиксирован на север и показывает сразу 100% территории всей карты.
              </div>
              <div style={{ fontSize: '10px', color: '#64748b', fontFamily: 'monospace' }}>
                cl_radar_rotate 0; cl_radar_scale 0.55
              </div>
              {onSelectPreset && (
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => {
                    onSelectPreset({ hudMode: 'huge_esports', radarMode: 'broadcast_giant' })
                    setShowScreenshotGallery(false)
                  }}
                  style={{ padding: '4px 8px', fontSize: '11px', marginTop: 'auto' }}
                >
                  Применить этот режим
                </button>
              )}
            </div>

            {/* Card 3: Огромный Киллфид */}
            <div
              style={{
                backgroundColor: '#161b28',
                border: '1px solid #232c42',
                borderRadius: '8px',
                padding: '12px',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '13px', fontWeight: 800, color: '#fbbf24' }}>
                  ⚡ Огромный Киллфид
                </span>
                <span style={{ fontSize: '10px', backgroundColor: '#d9770633', color: '#fbbf24', padding: '1px 5px', borderRadius: '4px', fontWeight: 700 }}>
                  ЧИСТЫЙ ЭКРАН
                </span>
              </div>
              {/* Mini visual mockup */}
              <div
                style={{
                  height: '90px',
                  backgroundColor: '#0a0d14',
                  borderRadius: '6px',
                  border: '1px solid #1e2536',
                  position: 'relative',
                  overflow: 'hidden',
                  background: 'linear-gradient(135deg, #241d14 0%, #0d0b07 100%)',
                }}
              >
                {/* Killfeed dominant */}
                <div style={{ position: 'absolute', top: '8px', right: '6px', display: 'flex', flexDirection: 'column', gap: '3px' }}>
                  <div style={{ backgroundColor: '#18120b', borderLeft: '2px solid #fbbf24', padding: '2px 6px', fontSize: '8px', color: '#f1f5f9', fontWeight: 700, borderRadius: '2px' }}>
                    donk 🔫 AK-47 💥 NiKo
                  </div>
                  <div style={{ backgroundColor: '#18120b', borderLeft: '2px solid #fbbf24', padding: '2px 6px', fontSize: '8px', color: '#f1f5f9', fontWeight: 700, borderRadius: '2px' }}>
                    donk 🔫 AK-47 💥 m0NESY
                  </div>
                </div>
                {/* Empty bottom center to emphasize clean screen */}
                <div style={{ position: 'absolute', bottom: '6px', left: '50%', transform: 'translateX(-50%)', fontSize: '7px', color: '#64748b' }}>
                  [Нижний худ скрыт]
                </div>
              </div>
              <div style={{ fontSize: '11px', color: '#cbd5e1' }}>
                Максимальный акцент на фрагах автора. Нижние цифры HP и патронов скрыты, вверху справа крупные яркие плашки фрагов.
              </div>
              <div style={{ fontSize: '10px', color: '#64748b', fontFamily: 'monospace' }}>
                cl_draw_only_deathnotices 1; hud_scaling 1.15
              </div>
              {onSelectPreset && (
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => {
                    onSelectPreset({ hudMode: 'huge_killfeed', radarMode: 'dynamic_large' })
                    setShowScreenshotGallery(false)
                  }}
                  style={{ padding: '4px 8px', fontSize: '11px', marginTop: 'auto' }}
                >
                  Применить этот режим
                </button>
              )}
            </div>

            {/* Card 4: Чистый Синематик */}
            <div
              style={{
                backgroundColor: '#161b28',
                border: '1px solid #232c42',
                borderRadius: '8px',
                padding: '12px',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '13px', fontWeight: 800, color: '#94a3b8' }}>
                  🎬 Чистый Синематик (No-HUD)
                </span>
                <span style={{ fontSize: '10px', backgroundColor: '#33415544', color: '#94a3b8', padding: '1px 5px', borderRadius: '4px', fontWeight: 700 }}>
                  ДЛЯ МУВИКОВ
                </span>
              </div>
              {/* Mini visual mockup */}
              <div
                style={{
                  height: '90px',
                  backgroundColor: '#0a0d14',
                  borderRadius: '6px',
                  border: '1px solid #1e2536',
                  position: 'relative',
                  overflow: 'hidden',
                  background: 'linear-gradient(135deg, #1e2433 0%, #0d121c 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <div style={{ fontSize: '10px', color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 700 }}>
                  🎬 100% PURE CINEMATIC
                </div>
              </div>
              <div style={{ fontSize: '11px', color: '#cbd5e1' }}>
                Кристально чистый кадр без интерфейса, худа и карты. Идеально для красивых видео-фрагмуви и наложения турнирных оверлеев.
              </div>
              <div style={{ fontSize: '10px', color: '#64748b', fontFamily: 'monospace' }}>
                cl_drawhud 0
              </div>
              {onSelectPreset && (
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => {
                    onSelectPreset({ hudMode: 'none', radarMode: 'hidden' })
                    setShowScreenshotGallery(false)
                  }}
                  style={{ padding: '4px 8px', fontSize: '11px', marginTop: 'auto' }}
                >
                  Применить этот режим
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
