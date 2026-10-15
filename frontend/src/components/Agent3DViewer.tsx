import React from 'react'

interface Agent3DViewerProps {
  team?: 'ct' | 't' | string | null
  playerName?: string
  role?: string
  height?: number
  weapon?: string
  avatarUrl?: string
}

export const Agent3DViewer: React.FC<Agent3DViewerProps> = ({
  team = 'ct',
  playerName = 'Operator',
  role = 'Entry Fragger',
  height = 360,
  weapon = 'AK-47',
  avatarUrl,
}) => {
  const isCT = (team || '').toLowerCase().includes('ct')

  // Primary team accent colors
  const primaryColor = isCT ? '#38bdf8' : '#f59e0b'
  const primaryBg = isCT ? 'rgba(56, 189, 248, 0.12)' : 'rgba(245, 158, 11, 0.12)'
  const primaryBorder = isCT ? 'rgba(56, 189, 248, 0.35)' : 'rgba(245, 158, 11, 0.35)'

  return (
    <div
      style={{
        position: 'relative',
        height: `${height}px`,
        backgroundColor: '#0c0f17',
        borderRadius: '16px',
        border: `1px solid ${primaryBorder}`,
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: `0 12px 30px rgba(0, 0, 0, 0.6), inset 0 0 40px ${isCT ? 'rgba(56, 189, 248, 0.04)' : 'rgba(245, 158, 11, 0.04)'}`,
      }}
    >
      {/* Tactical Top HUD Bar */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '10px 16px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.07)',
          backgroundColor: 'rgba(10, 13, 20, 0.85)',
          backdropFilter: 'blur(8px)',
          zIndex: 2,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span
            style={{
              display: 'inline-block',
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: primaryColor,
              boxShadow: `0 0 8px ${primaryColor}`,
            }}
          />
          <span style={{ fontSize: '11px', fontWeight: 800, letterSpacing: '0.08em', color: '#f1f5f9' }}>
            OPERATIVE PROFILE // {isCT ? 'COUNTER-TERRORIST' : 'TERRORIST'}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span
            style={{
              fontSize: '10px',
              fontWeight: 700,
              padding: '2px 8px',
              borderRadius: '4px',
              backgroundColor: primaryBg,
              color: primaryColor,
              border: `1px solid ${primaryBorder}`,
            }}
          >
            {weapon}
          </span>
          <span
            style={{
              fontSize: '10px',
              fontWeight: 700,
              padding: '2px 8px',
              borderRadius: '4px',
              backgroundColor: 'rgba(255, 255, 255, 0.06)',
              color: '#94a3b8',
            }}
          >
            {role}
          </span>
        </div>
      </div>

      {/* Main Neutral Operative Media Showcase Area */}
      <div
        style={{
          position: 'relative',
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          overflow: 'hidden',
          background: `radial-gradient(circle at 50% 45%, ${isCT ? 'rgba(56, 189, 248, 0.12)' : 'rgba(245, 158, 11, 0.12)'} 0%, transparent 70%)`,
        }}
      >
        {/* Subtle Cyber Grid Background */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            opacity: 0.12,
            backgroundImage: `linear-gradient(${primaryColor} 1px, transparent 1px), linear-gradient(90deg, ${primaryColor} 1px, transparent 1px)`,
            backgroundSize: '28px 28px',
            pointerEvents: 'none',
          }}
        />

        {/* Center Neutral Operative Insignia / Artwork */}
        {avatarUrl ? (
          <img
            src={avatarUrl}
            alt={playerName}
            style={{
              maxHeight: '75%',
              maxWidth: '75%',
              objectFit: 'contain',
              borderRadius: '12px',
              filter: `drop-shadow(0 8px 24px ${isCT ? 'rgba(56, 189, 248, 0.3)' : 'rgba(245, 158, 11, 0.3)'})`,
              zIndex: 1,
            }}
          />
        ) : (
          <div
            style={{
              position: 'relative',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 1,
              padding: '20px',
            }}
          >
            {/* Holographic Platform Ring */}
            <div
              style={{
                position: 'relative',
                width: '130px',
                height: '130px',
                borderRadius: '50%',
                backgroundColor: primaryBg,
                border: `2px solid ${primaryBorder}`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: `0 0 35px ${isCT ? 'rgba(56, 189, 248, 0.25)' : 'rgba(245, 158, 11, 0.25)'}`,
              }}
            >
              {/* Tactical Silhouette SVG */}
              <svg
                viewBox="0 0 64 64"
                fill="none"
                style={{
                  width: '72px',
                  height: '72px',
                  color: primaryColor,
                  filter: `drop-shadow(0 0 10px ${primaryColor}88)`,
                }}
              >
                {isCT ? (
                  // Counter-Terrorist Helmet & Visor
                  <>
                    <path
                      d="M32 8 C20 8 16 16 16 26 C16 34 20 40 22 46 L42 46 C44 40 48 34 48 26 C48 16 44 8 32 8 Z"
                      fill="currentColor"
                      fillOpacity="0.25"
                      stroke="currentColor"
                      strokeWidth="2"
                    />
                    <path
                      d="M20 26 Q32 24 44 26 L42 32 Q32 30 22 32 Z"
                      fill={primaryColor}
                      stroke="none"
                    />
                    <path
                      d="M14 54 C14 46 22 46 32 46 C42 46 50 46 50 54 L14 54 Z"
                      fill="currentColor"
                      fillOpacity="0.4"
                      stroke="currentColor"
                      strokeWidth="2"
                    />
                  </>
                ) : (
                  // Terrorist Balaclava & Goggles
                  <>
                    <path
                      d="M32 8 C21 8 17 18 17 28 C17 38 21 42 23 46 L41 46 C43 42 47 38 47 28 C47 18 43 8 32 8 Z"
                      fill="currentColor"
                      fillOpacity="0.25"
                      stroke="currentColor"
                      strokeWidth="2"
                    />
                    <circle cx="26" cy="27" r="4" fill={primaryColor} />
                    <circle cx="38" cy="27" r="4" fill={primaryColor} />
                    <line x1="30" y1="27" x2="34" y2="27" stroke={primaryColor} strokeWidth="2" />
                    <path
                      d="M14 54 C14 46 22 46 32 46 C42 46 50 46 50 54 L14 54 Z"
                      fill="currentColor"
                      fillOpacity="0.4"
                      stroke="currentColor"
                      strokeWidth="2"
                    />
                  </>
                )}
              </svg>
            </div>

            {/* Operative Sub-badge */}
            <div style={{ marginTop: '14px', textAlign: 'center' }}>
              <div
                style={{
                  fontSize: '11px',
                  fontWeight: 800,
                  letterSpacing: '0.1em',
                  textTransform: 'uppercase',
                  color: primaryColor,
                }}
              >
                {isCT ? 'Counter-Terrorist' : 'Terrorist Phoenix'}
              </div>
              <div style={{ fontSize: '10px', color: '#64748b', marginTop: '2px' }}>
                CS2 Official Model · Neutral Operator
              </div>
            </div>
          </div>
        )}

        {/* Tactical Crosshair Watermark Overlay */}
        <div
          style={{
            position: 'absolute',
            top: '20px',
            right: '20px',
            width: '36px',
            height: '36px',
            border: `1px solid ${primaryBorder}`,
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            pointerEvents: 'none',
            opacity: 0.6,
          }}
        >
          <div style={{ width: '8px', height: '1px', backgroundColor: primaryColor }} />
          <div style={{ width: '1px', height: '8px', backgroundColor: primaryColor, position: 'absolute' }} />
        </div>

        {/* Player Name Tag in Bottom Left */}
        <div
          style={{
            position: 'absolute',
            bottom: '12px',
            left: '16px',
            zIndex: 2,
            backgroundColor: 'rgba(12, 15, 23, 0.85)',
            padding: '6px 12px',
            borderRadius: '8px',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            backdropFilter: 'blur(6px)',
          }}
        >
          <div style={{ fontSize: '12px', fontWeight: 800, color: '#f1f5f9' }}>
            {playerName}
          </div>
          <div style={{ fontSize: '10px', color: '#94a3b8' }}>
            {isCT ? 'CT Special Forces' : 'T Attack Unit'} · {role}
          </div>
        </div>
      </div>
    </div>
  )
}
