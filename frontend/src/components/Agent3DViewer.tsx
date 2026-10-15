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
  height = 250,
  weapon = 'AK-47',
  avatarUrl,
}) => {
  const isCT = (team || '').toLowerCase().includes('ct')

  // Team-based tactical styling
  const primaryColor = isCT ? '#38bdf8' : '#f59e0b'
  const primaryBg = isCT ? 'rgba(56, 189, 248, 0.12)' : 'rgba(245, 158, 11, 0.12)'
  const primaryBorder = isCT ? 'rgba(56, 189, 248, 0.3)' : 'rgba(245, 158, 11, 0.3)'

  return (
    <div
      style={{
        position: 'relative',
        height: `${height}px`,
        backgroundColor: '#0c0f17',
        borderRadius: '14px',
        border: `1px solid ${primaryBorder}`,
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: `0 8px 24px rgba(0, 0, 0, 0.5), inset 0 0 30px ${isCT ? 'rgba(56, 189, 248, 0.05)' : 'rgba(245, 158, 11, 0.05)'}`,
      }}
    >
      {/* Top Header Bar */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '8px 14px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.07)',
          backgroundColor: 'rgba(10, 13, 20, 0.9)',
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
          <span style={{ fontSize: '11px', fontWeight: 800, letterSpacing: '0.06em', color: '#f1f5f9' }}>
            {isCT ? 'COUNTER-TERRORIST' : 'TERRORIST'}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          {weapon && (
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
          )}
          {role && (
            <span
              style={{
                fontSize: '10px',
                fontWeight: 600,
                padding: '2px 8px',
                borderRadius: '4px',
                backgroundColor: 'rgba(255, 255, 255, 0.06)',
                color: '#94a3b8',
              }}
            >
              {role}
            </span>
          )}
        </div>
      </div>

      {/* Main Card Body */}
      <div
        style={{
          position: 'relative',
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '16px',
          overflow: 'hidden',
          background: `radial-gradient(circle at 50% 50%, ${isCT ? 'rgba(56, 189, 248, 0.1)' : 'rgba(245, 158, 11, 0.1)'} 0%, transparent 70%)`,
        }}
      >
        {/* Subtle Background Grid Pattern */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            opacity: 0.08,
            backgroundImage: `linear-gradient(${primaryColor} 1px, transparent 1px), linear-gradient(90deg, ${primaryColor} 1px, transparent 1px)`,
            backgroundSize: '24px 24px',
            pointerEvents: 'none',
          }}
        />

        {avatarUrl ? (
          <img
            src={avatarUrl}
            alt={playerName}
            style={{
              maxHeight: '110px',
              maxWidth: '110px',
              objectFit: 'contain',
              borderRadius: '50%',
              border: `2px solid ${primaryBorder}`,
              boxShadow: `0 6px 20px ${isCT ? 'rgba(56, 189, 248, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`,
              zIndex: 1,
            }}
          />
        ) : (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 1,
            }}
          >
            {/* Center Emblem Ring */}
            <div
              style={{
                width: '90px',
                height: '90px',
                borderRadius: '50%',
                backgroundColor: primaryBg,
                border: `2px solid ${primaryBorder}`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: `0 0 25px ${isCT ? 'rgba(56, 189, 248, 0.2)' : 'rgba(245, 158, 11, 0.2)'}`,
              }}
            >
              <svg
                viewBox="0 0 64 64"
                fill="none"
                style={{
                  width: '56px',
                  height: '56px',
                  color: primaryColor,
                  filter: `drop-shadow(0 0 8px ${primaryColor}66)`,
                }}
              >
                {isCT ? (
                  // Counter-Terrorist Emblem
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
                  // Terrorist Phoenix Emblem
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

            {/* Operative Subtitle Badge */}
            <div style={{ marginTop: '10px', textAlign: 'center' }}>
              <div
                style={{
                  fontSize: '11px',
                  fontWeight: 800,
                  letterSpacing: '0.08em',
                  textTransform: 'uppercase',
                  color: primaryColor,
                }}
              >
                {isCT ? 'CT Special Forces' : 'Terrorist Phoenix'}
              </div>
              <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '2px', fontWeight: 600 }}>
                {playerName}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
