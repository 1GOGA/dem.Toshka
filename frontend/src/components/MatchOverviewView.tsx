import React, { useState, useEffect } from 'react'
import type { DemoSummary, MatchScoreboard, PlayerStats, RoundDTO } from '../types'
import { PlayerAnalyticsModal } from './PlayerAnalyticsModal'

interface MatchOverviewViewProps {
  demo: DemoSummary
  stats: MatchScoreboard | null
  rounds: RoundDTO[]
  isLoading: boolean
  onFilterPlayerHighlights: (steamId: string | null) => void
}

export const MatchOverviewView: React.FC<MatchOverviewViewProps> = ({
  demo,
  stats,
  rounds,
  isLoading,
  onFilterPlayerHighlights,
}) => {
  const [selectedPlayerForAnalytics, setSelectedPlayerForAnalytics] = useState<{
    steamIdOrName: string
    name: string
    team?: string | null
  } | null>(null)

  const [viewMode, setViewMode] = useState<'faceit' | 'all' | 'weapons'>('faceit')

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

  if (isLoading || !stats) {
    return (
      <div className="container" style={{ textAlign: 'center', padding: '64px 0', color: 'var(--text-muted)' }}>
        Loading match statistics...
      </div>
    )
  }

  const ctScore = stats.score['ct'] || 0
  const tScore = stats.score['t'] || 0
  const isCtWinner = ctScore > tScore
  const isTWinner = tScore > ctScore

  // Helper to get FACEIT level styling (1 to 10)
  const getFaceitBadge = (level?: number, rating?: number) => {
    const lvl = level || (rating ? (rating >= 1.5 ? 10 : rating >= 1.35 ? 9 : rating >= 1.25 ? 8 : rating >= 1.15 ? 7 : rating >= 1.05 ? 6 : rating >= 0.95 ? 5 : rating >= 0.85 ? 4 : rating >= 0.75 ? 3 : rating >= 0.65 ? 2 : 1) : 5)
    const colors: Record<number, { color: string; bg: string }> = {
      10: { color: '#ef4444', bg: 'rgba(239, 68, 68, 0.2)' },
      9: { color: '#f97316', bg: 'rgba(249, 115, 22, 0.2)' },
      8: { color: '#fbbf24', bg: 'rgba(251, 191, 36, 0.2)' },
      7: { color: '#a3e635', bg: 'rgba(163, 230, 53, 0.2)' },
      6: { color: '#22c55e', bg: 'rgba(34, 197, 94, 0.2)' },
      5: { color: '#38bdf8', bg: 'rgba(56, 189, 248, 0.2)' },
      4: { color: '#818cf8', bg: 'rgba(129, 140, 248, 0.2)' },
      3: { color: '#c084fc', bg: 'rgba(192, 132, 252, 0.2)' },
      2: { color: '#94a3b8', bg: 'rgba(148, 163, 184, 0.2)' },
      1: { color: '#64748b', bg: 'rgba(100, 116, 139, 0.2)' },
    }
    const c = colors[lvl] || colors[5]
    return { level: lvl, color: c.color, bg: c.bg }
  }

  // Split into CT and T teams
  const ctPlayers = stats.players.filter((p) => (p.team || '').toLowerCase() === 'ct')
  const tPlayers = stats.players.filter((p) => (p.team || '').toLowerCase() === 't')
  const otherPlayers = stats.players.filter(
    (p) => (p.team || '').toLowerCase() !== 'ct' && (p.team || '').toLowerCase() !== 't'
  )

  // Top fragger, MVP, Opening Master
  const topFragger = [...stats.players].sort((a, b) => b.kills - a.kills)[0]
  const matchMvp = [...stats.players].sort((a, b) => (b.performance_rating || 0) - (a.performance_rating || 0))[0]
  const topOpener = [...stats.players].sort((a, b) => (b.opening_kills || 0) - (a.opening_kills || 0))[0]

  const renderPlayerTable = (playersList: PlayerStats[], teamLabel?: string, teamScore?: number, isWinner?: boolean, teamColor?: string) => (
    <div
      style={{
        backgroundColor: '#13161f',
        border: `1px solid ${teamColor ? `${teamColor}44` : '#222838'}`,
        borderRadius: '12px',
        overflow: 'hidden',
        marginBottom: '20px',
        boxShadow: teamColor ? `0 4px 20px ${teamColor}11` : 'none',
      }}
    >
      {/* Team Header Bar */}
      {teamLabel && (
        <div
          style={{
            padding: '12px 20px',
            backgroundColor: teamColor ? `${teamColor}15` : '#161922',
            borderBottom: '1px solid #222838',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '14px', fontWeight: 800, color: teamColor || '#f1f5f9', letterSpacing: '0.04em' }}>
              {teamLabel}
            </span>
            {isWinner !== undefined && (
              <span
                style={{
                  fontSize: '10px',
                  fontWeight: 800,
                  padding: '2px 8px',
                  borderRadius: '4px',
                  backgroundColor: isWinner ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                  color: isWinner ? '#22c55e' : '#f87171',
                  border: `1px solid ${isWinner ? 'rgba(34, 197, 94, 0.4)' : 'rgba(239, 68, 68, 0.4)'}`,
                }}
              >
                {isWinner ? '🏆 ПОБЕДИТЕЛЬ' : 'ПОРАЖЕНИЕ'}
              </span>
            )}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            {teamScore !== undefined && (
              <div style={{ fontSize: '18px', fontWeight: 900, color: teamColor || '#f1f5f9' }}>
                {teamScore} <span style={{ fontSize: '11px', color: '#64748b', fontWeight: 600 }}>РАУНДОВ</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Scoreboard Table */}
      <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
        <thead>
          <tr style={{ backgroundColor: '#0f1218', color: '#64748b', borderBottom: '1px solid #1e2433', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            <th style={{ padding: '12px 18px' }}>Игрок</th>
            <th style={{ padding: '12px 10px', textAlign: 'center' }}>FACEIT</th>
            <th style={{ padding: '12px 10px', textAlign: 'right' }}>K - D - A</th>
            <th style={{ padding: '12px 10px', textAlign: 'right' }}>+/-</th>
            <th style={{ padding: '12px 10px', textAlign: 'right' }}>K/D</th>
            <th style={{ padding: '12px 10px', textAlign: 'right' }}>KR</th>
            <th style={{ padding: '12px 10px', textAlign: 'right' }}>HS%</th>
            <th style={{ padding: '12px 10px', textAlign: 'right' }}>FK</th>
            <th style={{ padding: '12px 10px', textAlign: 'center' }}>Мультикиллы</th>
            <th style={{ padding: '12px 18px', textAlign: 'right' }}>Действия</th>
          </tr>
        </thead>
        <tbody>
          {playersList.map((p, idx) => {
            const isMe = mySteamId && (mySteamId === p.steam_id || mySteamId === p.name)
            const badge = getFaceitBadge(p.faceit_level, p.performance_rating)
            const diff = p.differential !== undefined ? p.differential : (p.kills - p.deaths)
            const kr = p.kpr !== undefined ? p.kpr : (stats.total_rounds > 0 ? (p.kills / stats.total_rounds) : 0)

            return (
              <tr
                key={p.steam_id || p.name || idx}
                style={{
                  borderBottom: '1px solid #1a202c',
                  backgroundColor: isMe
                    ? 'rgba(245, 158, 11, 0.08)'
                    : idx % 2 === 0
                    ? 'transparent'
                    : 'rgba(255, 255, 255, 0.015)',
                  transition: 'background-color 0.15s ease',
                }}
              >
                {/* Player Name & Profile Tag */}
                <td style={{ padding: '12px 18px', fontWeight: 600 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div
                      style={{
                        width: '32px',
                        height: '32px',
                        borderRadius: '8px',
                        backgroundColor: '#1b202c',
                        border: '1px solid #2d3548',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontWeight: 800,
                        fontSize: '13px',
                        color: '#94a3b8',
                      }}
                    >
                      {p.name.slice(0, 2).toUpperCase()}
                    </div>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span style={{ color: '#f1f5f9', fontWeight: 700 }}>{p.name}</span>
                        {isMe && (
                          <span
                            style={{
                              fontSize: '10px',
                              fontWeight: 800,
                              padding: '1px 6px',
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
                      <div style={{ fontSize: '10px', color: '#64748b', marginTop: '1px' }}>
                        {p.steam_id ? `ID: ${p.steam_id}` : 'Local Account'}
                      </div>
                    </div>
                  </div>
                </td>

                {/* FACEIT Level Badge */}
                <td style={{ padding: '12px 10px', textAlign: 'center' }}>
                  <div
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      width: '28px',
                      height: '28px',
                      borderRadius: '8px',
                      backgroundColor: badge.bg,
                      border: `1.5px solid ${badge.color}`,
                      color: badge.color,
                      fontWeight: 900,
                      fontSize: '13px',
                    }}
                    title={`FACEIT Level: ${badge.level} (Score: ${(p.performance_rating || 1.0).toFixed(2)})`}
                  >
                    {badge.level}
                  </div>
                </td>

                {/* K - D - A */}
                <td className="num" style={{ padding: '12px 10px', textAlign: 'right', fontWeight: 700 }}>
                  <span style={{ color: '#f1f5f9' }}>{p.kills}</span>
                  <span style={{ color: '#64748b' }}> - </span>
                  <span style={{ color: '#94a3b8' }}>{p.deaths}</span>
                  <span style={{ color: '#64748b' }}> - </span>
                  <span style={{ color: '#64748b' }}>{p.assists}</span>
                </td>

                {/* +/- (Differential) */}
                <td
                  className="num"
                  style={{
                    padding: '12px 10px',
                    textAlign: 'right',
                    fontWeight: 800,
                    color: diff > 0 ? '#22c55e' : diff < 0 ? '#ef4444' : '#94a3b8',
                  }}
                >
                  {diff > 0 ? `+${diff}` : diff}
                </td>

                {/* K/D Ratio */}
                <td
                  className="num"
                  style={{
                    padding: '12px 10px',
                    textAlign: 'right',
                    fontWeight: 700,
                    color: p.kd_ratio >= 1.0 ? '#22c55e' : '#f87171',
                  }}
                >
                  {p.kd_ratio.toFixed(2)}
                </td>

                {/* KR (Kills Per Round) */}
                <td className="num" style={{ padding: '12px 10px', textAlign: 'right', color: '#e2e8f0', fontWeight: 600 }}>
                  {kr.toFixed(2)}
                </td>

                {/* HS % */}
                <td className="num" style={{ padding: '12px 10px', textAlign: 'right', color: '#94a3b8' }}>
                  {p.headshot_pct.toFixed(1)}%
                </td>

                {/* FK (First Kills / Opening Duels) */}
                <td className="num" style={{ padding: '12px 10px', textAlign: 'right', color: (p.opening_kills || 0) > 0 ? '#38bdf8' : '#64748b', fontWeight: 700 }}>
                  {p.opening_kills || 0}
                </td>

                {/* Multikills Badges */}
                <td style={{ padding: '12px 10px', textAlign: 'center' }}>
                  <div style={{ display: 'inline-flex', gap: '4px', justifyContent: 'center' }}>
                    {p.multikills && p.multikills['5k'] > 0 && (
                      <span style={{ fontSize: '9px', fontWeight: 800, padding: '2px 5px', borderRadius: '4px', backgroundColor: 'rgba(239, 68, 68, 0.25)', color: '#ef4444', border: '1px solid #ef4444' }}>
                        ACE ({p.multikills['5k']})
                      </span>
                    )}
                    {p.multikills && p.multikills['4k'] > 0 && (
                      <span style={{ fontSize: '9px', fontWeight: 800, padding: '2px 5px', borderRadius: '4px', backgroundColor: 'rgba(249, 115, 22, 0.25)', color: '#f97316' }}>
                        4K ({p.multikills['4k']})
                      </span>
                    )}
                    {p.multikills && p.multikills['3k'] > 0 && (
                      <span style={{ fontSize: '9px', fontWeight: 800, padding: '2px 5px', borderRadius: '4px', backgroundColor: 'rgba(234, 179, 8, 0.25)', color: '#eab308' }}>
                        3K ({p.multikills['3k']})
                      </span>
                    )}
                    {p.multikills && p.multikills['2k'] > 0 && (
                      <span style={{ fontSize: '9px', fontWeight: 700, padding: '2px 5px', borderRadius: '4px', backgroundColor: 'rgba(56, 189, 248, 0.15)', color: '#38bdf8' }}>
                        2K ({p.multikills['2k']})
                      </span>
                    )}
                    {(!p.multikills || (p.multikills['2k'] === 0 && p.multikills['3k'] === 0 && p.multikills['4k'] === 0 && p.multikills['5k'] === 0)) && (
                      <span style={{ color: '#475569', fontSize: '11px' }}>-</span>
                    )}
                  </div>
                </td>

                {/* Actions */}
                <td style={{ padding: '12px 18px', textAlign: 'right' }}>
                  <div style={{ display: 'inline-flex', gap: '6px' }}>
                    <button
                      className="btn btn-primary"
                      style={{ padding: '4px 10px', fontSize: '11px' }}
                      onClick={() =>
                        setSelectedPlayerForAnalytics({
                          steamIdOrName: p.steam_id || p.name,
                          name: p.name,
                          team: p.team,
                        })
                      }
                      title={`Подробный разбор ошибок и FACEIT аналитика для ${p.name}`}
                    >
                      📊 Анализ & Ошибки
                    </button>
                    <button
                      className="btn btn-secondary"
                      style={{ padding: '4px 10px', fontSize: '11px' }}
                      onClick={() => onFilterPlayerHighlights(p.steam_id)}
                      title={`Open Highlights Studio filtered for ${p.name}`}
                    >
                      Хайлайты →
                    </button>
                  </div>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )

  return (
    <div className="container">
      {/* 1. Score & Match Hero Banner */}
      <div
        style={{
          background: 'linear-gradient(135deg, #131722 0%, #0d1017 100%)',
          border: '1px solid #232a3c',
          borderRadius: '16px',
          padding: '24px 28px',
          marginBottom: '20px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          boxShadow: '0 8px 30px rgba(0,0,0,0.4)',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h2 style={{ fontSize: '24px', fontWeight: 900, color: '#f1f5f9', margin: 0 }}>
              {(demo.map_name || 'Match').replace('de_', '').toUpperCase()}
            </h2>
            <span
              style={{
                fontSize: '11px',
                fontWeight: 800,
                padding: '3px 8px',
                borderRadius: '5px',
                backgroundColor: 'rgba(56, 189, 248, 0.15)',
                color: '#38bdf8',
                border: '1px solid rgba(56, 189, 248, 0.3)',
              }}
            >
              FACEIT COMPETITIVE
            </span>
          </div>
          <div style={{ fontSize: '13px', color: '#94a3b8', marginTop: '4px' }}>
            Всего раундов: <strong>{stats.total_rounds}</strong> • Tickrate: <strong>{demo.tickrate}</strong> • Игроков: <strong>{stats.players.length}</strong>
          </div>
        </div>

        {/* Team Score Display */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '11px', fontWeight: 800, color: '#38bdf8', letterSpacing: '0.06em' }}>
              COUNTER-TERRORISTS {isCtWinner && '🏆'}
            </div>
            <div className="num" style={{ fontSize: '38px', fontWeight: 900, color: '#38bdf8', lineHeight: 1.1 }}>
              {ctScore}
            </div>
          </div>
          <div style={{ fontSize: '26px', fontWeight: 800, color: '#475569' }}>:</div>
          <div style={{ textAlign: 'left' }}>
            <div style={{ fontSize: '11px', fontWeight: 800, color: '#f59e0b', letterSpacing: '0.06em' }}>
              {isTWinner && '🏆'} TERRORISTS
            </div>
            <div className="num" style={{ fontSize: '38px', fontWeight: 900, color: '#f59e0b', lineHeight: 1.1 }}>
              {tScore}
            </div>
          </div>
        </div>
      </div>

      {/* 2. Top Match Award Highlights */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '14px', marginBottom: '20px' }}>
        {matchMvp && (
          <div style={{ backgroundColor: '#131620', border: '1px solid #232a3c', borderRadius: '12px', padding: '14px 18px', display: 'flex', alignItems: 'center', gap: '14px' }}>
            <div style={{ width: '44px', height: '44px', borderRadius: '12px', backgroundColor: 'rgba(245, 158, 11, 0.15)', border: '1px solid rgba(245, 158, 11, 0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '22px' }}>
              👑
            </div>
            <div>
              <div style={{ fontSize: '11px', fontWeight: 700, color: '#fbbf24', textTransform: 'uppercase' }}>Матч MVP</div>
              <div style={{ fontSize: '15px', fontWeight: 800, color: '#f1f5f9' }}>{matchMvp.name}</div>
              <div style={{ fontSize: '11px', color: '#94a3b8' }}>Рейтинг: <strong>{(matchMvp.performance_rating || 1.0).toFixed(2)}</strong> • K/D: <strong>{matchMvp.kd_ratio.toFixed(2)}</strong></div>
            </div>
          </div>
        )}

        {topFragger && (
          <div style={{ backgroundColor: '#131620', border: '1px solid #232a3c', borderRadius: '12px', padding: '14px 18px', display: 'flex', alignItems: 'center', gap: '14px' }}>
            <div style={{ width: '44px', height: '44px', borderRadius: '12px', backgroundColor: 'rgba(56, 189, 248, 0.15)', border: '1px solid rgba(56, 189, 248, 0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '22px' }}>
              🎯
            </div>
            <div>
              <div style={{ fontSize: '11px', fontWeight: 700, color: '#38bdf8', textTransform: 'uppercase' }}>Топ Фраггер</div>
              <div style={{ fontSize: '15px', fontWeight: 800, color: '#f1f5f9' }}>{topFragger.name}</div>
              <div style={{ fontSize: '11px', color: '#94a3b8' }}>Фрагов: <strong>{topFragger.kills}</strong> • HS: <strong>{topFragger.headshot_pct.toFixed(0)}%</strong></div>
            </div>
          </div>
        )}

        {topOpener && (
          <div style={{ backgroundColor: '#131620', border: '1px solid #232a3c', borderRadius: '12px', padding: '14px 18px', display: 'flex', alignItems: 'center', gap: '14px' }}>
            <div style={{ width: '44px', height: '44px', borderRadius: '12px', backgroundColor: 'rgba(34, 197, 94, 0.15)', border: '1px solid rgba(34, 197, 94, 0.4)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '22px' }}>
              ⚡
            </div>
            <div>
              <div style={{ fontSize: '11px', fontWeight: 700, color: '#22c55e', textTransform: 'uppercase' }}>Мастер первых дуэлей</div>
              <div style={{ fontSize: '15px', fontWeight: 800, color: '#f1f5f9' }}>{topOpener.name}</div>
              <div style={{ fontSize: '11px', color: '#94a3b8' }}>Первых киллов (FK): <strong>{topOpener.opening_kills || 0}</strong></div>
            </div>
          </div>
        )}
      </div>

      {/* 3. Rounds Outcome Strip */}
      {rounds.length > 0 && (
        <div
          style={{
            backgroundColor: '#13161f',
            border: '1px solid #202636',
            borderRadius: '12px',
            padding: '14px 18px',
            marginBottom: '20px',
          }}
        >
          <div style={{ fontSize: '11px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px' }}>
            ХРОНОЛОГИЯ ПОБЕД В РАУНДАХ
          </div>
          <div style={{ display: 'flex', gap: '5px', overflowX: 'auto', paddingBottom: '4px' }}>
            {rounds.map((r) => {
              const isCt = r.winner === 'ct'
              const isT = r.winner === 't'
              return (
                <div
                  key={r.id}
                  title={`Раунд ${r.round_num}: Победитель ${r.winner?.toUpperCase() || 'Неизвестно'} (${r.reason || 'Ликвидация'})`}
                  style={{
                    minWidth: '30px',
                    height: '34px',
                    borderRadius: '6px',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    backgroundColor: isCt ? 'rgba(56, 189, 248, 0.15)' : isT ? 'rgba(245, 158, 11, 0.15)' : '#1a202c',
                    border: `1px solid ${isCt ? '#38bdf8' : isT ? '#f59e0b' : '#334155'}`,
                  }}
                >
                  <span className="num" style={{ fontSize: '10px', fontWeight: 700, color: '#94a3b8' }}>{r.round_num}</span>
                  <span style={{ fontSize: '9px', fontWeight: 800, color: isCt ? '#38bdf8' : isT ? '#f59e0b' : '#64748b' }}>
                    {r.winner?.toUpperCase() || '-'}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* 4. Scoreboard Tabs Switcher */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            type="button"
            className={viewMode === 'faceit' ? 'btn btn-primary' : 'btn btn-secondary'}
            onClick={() => setViewMode('faceit')}
            style={{ fontSize: '12px', padding: '7px 14px', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <span>🏆 FACEIT Табло команд</span>
          </button>
          <button
            type="button"
            className={viewMode === 'all' ? 'btn btn-primary' : 'btn btn-secondary'}
            onClick={() => setViewMode('all')}
            style={{ fontSize: '12px', padding: '7px 14px', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <span>📋 Общий рейтинг (Все игроки)</span>
          </button>
          <button
            type="button"
            className={viewMode === 'weapons' ? 'btn btn-primary' : 'btn btn-secondary'}
            onClick={() => setViewMode('weapons')}
            style={{ fontSize: '12px', padding: '7px 14px', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <span>🎯 Оружие матча</span>
          </button>
        </div>

        <div style={{ fontSize: '12px', color: '#64748b' }}>
          Кликните <strong>📊 Анализ & Ошибки</strong> любого игрока для глубокого разбора SWING и тактики
        </div>
      </div>

      {/* 5. Scoreboard Views */}
      {viewMode === 'faceit' && (
        <>
          {ctPlayers.length > 0 && renderPlayerTable(ctPlayers, 'COUNTER-TERRORISTS', ctScore, isCtWinner, '#38bdf8')}
          {tPlayers.length > 0 && renderPlayerTable(tPlayers, 'TERRORISTS', tScore, isTWinner, '#f59e0b')}
          {otherPlayers.length > 0 && renderPlayerTable(otherPlayers, 'ДРУГИЕ ИГРОКИ')}
        </>
      )}

      {viewMode === 'all' && renderPlayerTable(stats.players)}

      {viewMode === 'weapons' && Object.keys(stats.weapon_summary).length > 0 && (
        <div
          style={{
            backgroundColor: '#13161f',
            border: '1px solid #222838',
            borderRadius: '12px',
            padding: '24px',
            marginBottom: '20px',
          }}
        >
          <h3 style={{ fontSize: '16px', fontWeight: 800, color: '#f1f5f9', marginBottom: '16px' }}>
            Распределение фрагов по типам оружия
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '12px' }}>
            {Object.entries(stats.weapon_summary)
              .sort(([, a], [, b]) => b - a)
              .map(([weapon, count]) => (
                <div
                  key={weapon}
                  style={{
                    backgroundColor: '#161922',
                    border: '1px solid #232a3c',
                    borderRadius: '8px',
                    padding: '12px 16px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                  }}
                >
                  <span style={{ fontSize: '13px', fontWeight: 700, color: '#f1f5f9', textTransform: 'uppercase' }}>
                    {weapon.replace('weapon_', '').replace('_', ' ')}
                  </span>
                  <span className="num" style={{ fontSize: '15px', fontWeight: 800, color: '#fbbf24' }}>
                    {count} фрагов
                  </span>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Analytics Modal */}
      {selectedPlayerForAnalytics && (
        <PlayerAnalyticsModal
          demoId={demo.id}
          playerIdentifier={selectedPlayerForAnalytics.steamIdOrName}
          playerName={selectedPlayerForAnalytics.name}
          playerTeam={selectedPlayerForAnalytics.team}
          onClose={() => setSelectedPlayerForAnalytics(null)}
          onViewHighlights={(steamId) => {
            setSelectedPlayerForAnalytics(null)
            onFilterPlayerHighlights(steamId)
          }}
        />
      )}
    </div>
  )
}
