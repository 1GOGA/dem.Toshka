import React, { useState } from 'react'

interface Agent3DViewerProps {
  team?: 'ct' | 't' | string | null
  playerName?: string
  role?: string
  interactive?: boolean
  height?: number
  weapon?: string
}

interface AgentProfile {
  id: string
  name: string
  title: string
  team: 'ct' | 't'
  gifUrl: string
  fallbackAvatar: string
  description: string
  quote: string
}

const AGENTS: AgentProfile[] = [
  {
    id: 'ct_ava',
    name: 'Special Agent Ava',
    title: 'FBI SWAT Commander',
    team: 'ct',
    gifUrl: 'https://media.tenor.com/qR3L5whq4mUAAAAM/time-out-cs2.gif',
    fallbackAvatar: '🛡️',
    description: 'Special Agent Ava was the FBI\'s first female operative deployed into high-threat tactical scenarios.',
    quote: '"They see me, they freeze. Simple as that."',
  },
  {
    id: 'ct_mae',
    name: 'Cmdr. Mae "Dead Cold"',
    title: 'SWAT Special Forces',
    team: 'ct',
    gifUrl: 'https://media.tenor.com/ad6HfaJtqU4AAAAM/agent-cs2-dancing-cmdr-mae-dead-cold-jamison-swat.gif',
    fallbackAvatar: '⚡',
    description: 'Renowned for exceptional clutch reactions and tactical discipline under hostile fire.',
    quote: '"Round won. Ready for the next engagement."',
  },
  {
    id: 't_phoenix',
    name: 'Street Soldier',
    title: 'Phoenix Connexion',
    team: 't',
    gifUrl: 'https://media.tenor.com/ad6HfaJtqU4AAAAM/agent-cs2-dancing-cmdr-mae-dead-cold-jamison-swat.gif',
    fallbackAvatar: '🔥',
    description: 'Veterans of eastern European conflicts, heavily armed and relentless on entry duels.',
    quote: '"Plant the bomb and hold every corridor."',
  },
]

export const Agent3DViewer: React.FC<Agent3DViewerProps> = ({
  team = 'ct',
  playerName = 'Operator',
  role = 'Entry Fragger',
  interactive = true,
  height = 360,
  weapon = 'AK-47',
}) => {
  const isCT = (team || '').toLowerCase().includes('ct')
  const [selectedAgentIndex, setSelectedAgentIndex] = useState<number>(isCT ? 0 : 2)
  const [tacticalMode, setTacticalMode] = useState<'combat' | 'tactical' | 'mvp'>('tactical')
  const [imgError, setImgError] = useState<boolean>(false)

  // Primary colors
  const primaryColor = isCT ? '#38bdf8' : '#f59e0b'
  const primaryBg = isCT ? 'rgba(56, 189, 248, 0.12)' : 'rgba(245, 158, 11, 0.12)'
  const primaryBorder = isCT ? 'rgba(56, 189, 248, 0.35)' : 'rgba(245, 158, 11, 0.35)'

  const currentAgent = AGENTS[selectedAgentIndex] || AGENTS[0]

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
            OPERATIVE HUD // {isCT ? 'COUNTER-TERRORIST' : 'TERRORIST'}
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

      {/* Main Agent Media Showcase Area */}
      <div
        style={{
          position: 'relative',
          flex: 1,
          display: 'flex',
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
            opacity: 0.15,
            backgroundImage: `linear-gradient(${primaryColor} 1px, transparent 1px), linear-gradient(90deg, ${primaryColor} 1px, transparent 1px)`,
            backgroundSize: '32px 32px',
            pointerEvents: 'none',
          }}
        />

        {/* Animated CS2 Agent GIF or Fallback Card */}
        {!imgError ? (
          <img
            src={currentAgent.gifUrl}
            alt={currentAgent.name}
            onError={() => setImgError(true)}
            style={{
              maxHeight: '85%',
              maxWidth: '85%',
              objectFit: 'contain',
              borderRadius: '12px',
              filter: `drop-shadow(0 8px 24px ${isCT ? 'rgba(56, 189, 248, 0.3)' : 'rgba(245, 158, 11, 0.3)'})`,
              zIndex: 1,
              transition: 'transform 0.3s ease',
            }}
          />
        ) : (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '12px',
              zIndex: 1,
            }}
          >
            <div
              style={{
                width: '100px',
                height: '100px',
                borderRadius: '50%',
                backgroundColor: primaryBg,
                border: `2px solid ${primaryColor}`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '44px',
                boxShadow: `0 0 25px ${primaryColor}55`,
              }}
            >
              {currentAgent.fallbackAvatar}
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '15px', fontWeight: 800, color: '#f8fafc' }}>
                {currentAgent.name}
              </div>
              <div style={{ fontSize: '11px', color: primaryColor, fontWeight: 600 }}>
                {currentAgent.title}
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
            {currentAgent.name} · {currentAgent.title}
          </div>
        </div>
      </div>

      {/* Interactive Controls Footer */}
      {interactive && (
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '8px 16px',
            backgroundColor: 'rgba(8, 11, 18, 0.9)',
            borderTop: '1px solid rgba(255, 255, 255, 0.07)',
            zIndex: 2,
          }}
        >
          {/* Agent Switcher Pills */}
          <div style={{ display: 'flex', gap: '6px' }}>
            {AGENTS.map((ag, idx) => (
              <button
                key={ag.id}
                onClick={() => {
                  setSelectedAgentIndex(idx)
                  setImgError(false)
                }}
                style={{
                  fontSize: '10px',
                  fontWeight: 700,
                  padding: '3px 8px',
                  borderRadius: '6px',
                  border: selectedAgentIndex === idx ? `1px solid ${primaryColor}` : '1px solid rgba(255, 255, 255, 0.1)',
                  backgroundColor: selectedAgentIndex === idx ? primaryBg : 'transparent',
                  color: selectedAgentIndex === idx ? primaryColor : '#94a3b8',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                }}
              >
                {ag.name.split(' ')[0]}
              </button>
            ))}
          </div>

          {/* Action Mood Selector */}
          <div style={{ display: 'flex', gap: '4px' }}>
            <button
              onClick={() => setTacticalMode('tactical')}
              style={{
                fontSize: '10px',
                fontWeight: tacticalMode === 'tactical' ? 800 : 500,
                color: tacticalMode === 'tactical' ? '#38bdf8' : '#64748b',
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
              }}
            >
              Tactical
            </button>
            <span style={{ color: 'rgba(255, 255, 255, 0.2)', fontSize: '10px' }}>•</span>
            <button
              onClick={() => setTacticalMode('combat')}
              style={{
                fontSize: '10px',
                fontWeight: tacticalMode === 'combat' ? 800 : 500,
                color: tacticalMode === 'combat' ? '#f59e0b' : '#64748b',
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
              }}
            >
              Combat
            </button>
            <span style={{ color: 'rgba(255, 255, 255, 0.2)', fontSize: '10px' }}>•</span>
            <button
              onClick={() => setTacticalMode('mvp')}
              style={{
                fontSize: '10px',
                fontWeight: tacticalMode === 'mvp' ? 800 : 500,
                color: tacticalMode === 'mvp' ? '#a855f7' : '#64748b',
                background: 'transparent',
                border: 'none',
                cursor: 'pointer',
              }}
            >
              MVP
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
