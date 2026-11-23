import React, { useEffect, useState } from 'react'
import { api } from '../api'
import type { MultiMatchAnalyticsDTO, PlayerProfileDTO } from '../types'
import { useTranslation } from '../i18n'

interface MultiMatchPlayerAnalyticsViewProps {
  initialSteamId?: string
  onJumpToDemoVision?: (target: { demoId: number; roundNum: number; tick: number }) => void
}

export const MultiMatchPlayerAnalyticsView: React.FC<MultiMatchPlayerAnalyticsViewProps> = ({
  initialSteamId,
  onJumpToDemoVision,
}) => {
  const { lang } = useTranslation()
  const [profiles, setProfiles] = useState<PlayerProfileDTO[]>([])
  const [selectedSteamId, setSelectedSteamId] = useState<string>(initialSteamId || '')
  const [analytics, setAnalytics] = useState<MultiMatchAnalyticsDTO | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  // Load profiles list on mount
  useEffect(() => {
    api
      .getPlayerProfiles()
      .then((profs) => {
        setProfiles(profs)
        if (profs.length > 0 && !selectedSteamId) {
          setSelectedSteamId(profs[0].steam_id)
        }
      })
      .catch((err) => console.error('Failed to load player profiles:', err))
  }, [])

  // Load analytics when selected player changes
  useEffect(() => {
    if (!selectedSteamId) return
    setIsLoading(true)
    setError(null)

    api
      .getPlayerMultiMatchAnalytics(selectedSteamId)
      .then((data) => {
        setAnalytics(data)
        setIsLoading(false)
      })
      .catch((err) => {
        console.error('Failed to load multi-match analytics:', err)
        setError(err?.message || 'Analytics load error')
        setIsLoading(false)
      })
  }, [selectedSteamId])

  // Helper to render hexagonal SVG radar
  const renderRadarPolygon = (radar: MultiMatchAnalyticsDTO['radar']) => {
    const size = 260
    const center = size / 2
    const radius = 95
    const pillars = [
      { key: 'aim_duels', label: lang === 'ru' ? 'Стрельба' : 'Aim', val: radar.aim_duels },
      { key: 'positioning', label: lang === 'ru' ? 'Позиция' : 'Position', val: radar.positioning },
      { key: 'decision_making', label: lang === 'ru' ? 'Решения' : 'Decisions', val: radar.decision_making },
      { key: 'utility', label: lang === 'ru' ? 'Гранаты' : 'Utility', val: radar.utility },
      { key: 'trading', label: lang === 'ru' ? 'Размен' : 'Trading', val: radar.trading },
      { key: 'clutch', label: lang === 'ru' ? 'Клатчи' : 'Clutch', val: radar.clutch },
    ]

    const numPoints = pillars.length
    const getCoordinates = (index: number, valuePct: number) => {
      const angle = (Math.PI * 2 / numPoints) * index - Math.PI / 2
      const r = (valuePct / 100) * radius
      return {
        x: center + r * Math.cos(angle),
        y: center + r * Math.sin(angle),
      }
    }

    const polygonPoints = pillars
      .map((p, i) => {
        const { x, y } = getCoordinates(i, p.val)
        return `${x.toFixed(1)},${y.toFixed(1)}`
      })
      .join(' ')

    return (
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ display: 'block', margin: '0 auto' }}>
        {/* Background Rings */}
        {[25, 50, 75, 100].map((level) => {
          const ringPoints = pillars
            .map((_, i) => {
              const { x, y } = getCoordinates(i, level)
              return `${x.toFixed(1)},${y.toFixed(1)}`
            })
            .join(' ')
          return (
            <polygon
              key={level}
              points={ringPoints}
              fill="none"
              stroke="#1e293b"
              strokeWidth="1"
              strokeDasharray={level === 100 ? 'none' : '3,3'}
            />
          )
        })}

        {/* Axis Lines */}
        {pillars.map((_, i) => {
          const { x, y } = getCoordinates(i, 100)
          return <line key={i} x1={center} y1={center} x2={x} y2={y} stroke="#1e293b" strokeWidth="1" />
        })}

        {/* Data Filled Polygon */}
        <polygon
          points={polygonPoints}
          fill="rgba(0, 242, 254, 0.25)"
          stroke="#00f2fe"
          strokeWidth="2"
          style={{ filter: 'drop-shadow(0 0 8px rgba(0, 242, 254, 0.4))' }}
        />

        {/* Labels & Data Dots */}
        {pillars.map((p, i) => {
          const pt = getCoordinates(i, p.val)
          const labelPt = getCoordinates(i, 122)
          return (
            <g key={p.key}>
              <circle cx={pt.x} cy={pt.y} r="3.5" fill="#00f2fe" stroke="#ffffff" strokeWidth="1" />
              <text
                x={labelPt.x}
                y={labelPt.y}
                fill="#94a3b8"
                fontSize="11"
                fontWeight="700"
                textAnchor="middle"
                dominantBaseline="central"
              >
                {p.label} ({Math.round(p.val)})
              </text>
            </g>
          )
        })}
      </svg>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Header & Player Selection Strip */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          backgroundColor: '#0c1017',
          padding: '14px 20px',
          borderRadius: '12px',
          border: '1px solid #1a2233',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div
            style={{
              width: '44px',
              height: '44px',
              borderRadius: '50%',
              backgroundColor: '#1e293b',
              border: '2px solid #00f2fe',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '20px',
            }}
          >
            👤
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '18px', fontWeight: 900, color: '#f8fafc' }}>
                {analytics?.nickname || (lang === 'ru' ? 'Аналитика игрока' : 'Player Analytics')}
              </span>
              {analytics?.primary_role && (
                <span
                  style={{
                    backgroundColor: 'rgba(56, 189, 248, 0.15)',
                    color: '#38bdf8',
                    border: '1px solid rgba(56, 189, 248, 0.4)',
                    padding: '2px 8px',
                    borderRadius: '12px',
                    fontSize: '11px',
                    fontWeight: 700,
                  }}
                >
                  {analytics.primary_role}
                </span>
              )}
            </div>
            <span style={{ fontSize: '12px', color: '#64748b', fontFamily: 'monospace' }}>
              SteamID: {analytics?.steam_id || selectedSteamId || '—'}
            </span>
          </div>
        </div>

        {/* Profile Switcher Dropdown */}
        {profiles.length > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '12px', color: '#94a3b8' }}>
              {lang === 'ru' ? 'Выбрать игрока:' : 'Select Player:'}
            </span>
            <select
              value={selectedSteamId}
              onChange={(e) => setSelectedSteamId(e.target.value)}
              style={{
                backgroundColor: '#131926',
                color: '#f8fafc',
                border: '1px solid #334155',
                borderRadius: '8px',
                padding: '6px 12px',
                fontSize: '13px',
                fontWeight: 600,
                outline: 'none',
              }}
            >
              {profiles.map((p) => (
                <option key={p.id} value={p.steam_id}>
                  {p.nickname} ({p.primary_role || 'Rifler'})
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {isLoading && (
        <div style={{ textAlign: 'center', padding: '40px', color: '#94a3b8', fontSize: '14px' }}>
          ⏳ {lang === 'ru' ? 'Агрегация истории матчей и расчет метрик...' : 'Aggregating match history and calculating metrics...'}
        </div>
      )}

      {error && (
        <div style={{ padding: '16px', backgroundColor: 'rgba(239, 68, 68, 0.15)', border: '1px solid #ef4444', borderRadius: '8px', color: '#fca5a5' }}>
          ⚠️ {error}
        </div>
      )}

      {analytics && !isLoading && (
        <>
          {/* Main Grid: Competency Radar + KPI Overview */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            {/* 6-Pillar Radar Card */}
            <div
              style={{
                backgroundColor: '#0c1017',
                border: '1px solid #1a2233',
                borderRadius: '12px',
                padding: '18px',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '14px', fontWeight: 800, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  🎯 {lang === 'ru' ? 'Лепестковая диаграмма компетенций' : '6-Pillar Competency Radar'}
                </span>
                <span style={{ fontSize: '11px', color: '#64748b' }}>
                  {analytics.matches_count} {lang === 'ru' ? 'матчей' : 'matches'} • {analytics.total_rounds} {lang === 'ru' ? 'раундов' : 'rounds'}
                </span>
              </div>
              {renderRadarPolygon(analytics.radar)}
            </div>

            {/* Overview KPIs & CT/T Split */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(3, 1fr)',
                  gap: '10px',
                }}
              >
                {[
                  { label: 'Rating 2.0', val: analytics.overview.rating.toFixed(2), color: analytics.overview.rating >= 1.15 ? '#22c55e' : '#38bdf8' },
                  { label: 'K/D Ratio', val: analytics.overview.kd_ratio.toFixed(2), color: '#38bdf8' },
                  { label: 'ADR', val: analytics.overview.adr.toFixed(1), color: '#f59e0b' },
                  { label: 'HS %', val: `${analytics.overview.headshot_pct.toFixed(1)}%`, color: '#ec4899' },
                  { label: 'KAST %', val: `${analytics.overview.kast_pct.toFixed(1)}%`, color: '#a855f7' },
                  { label: 'Kills / Deaths', val: `${analytics.overview.kills} / ${analytics.overview.deaths}`, color: '#94a3b8' },
                ].map((item, idx) => (
                  <div
                    key={idx}
                    style={{
                      backgroundColor: '#0c1017',
                      border: '1px solid #1a2233',
                      borderRadius: '10px',
                      padding: '12px',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '4px',
                    }}
                  >
                    <span style={{ fontSize: '11px', color: '#64748b', fontWeight: 600 }}>{item.label}</span>
                    <span style={{ fontSize: '18px', fontWeight: 900, color: item.color }}>{item.val}</span>
                  </div>
                ))}
              </div>

              {/* CT vs T Side Split Card */}
              <div
                style={{
                  backgroundColor: '#0c1017',
                  border: '1px solid #1a2233',
                  borderRadius: '10px',
                  padding: '14px 16px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '10px',
                }}
              >
                <span style={{ fontSize: '12px', fontWeight: 800, color: '#f8fafc' }}>
                  ⚖️ {lang === 'ru' ? 'Баланс эффективности сторон (CT vs T)' : 'Side Performance Split (CT vs T)'}
                </span>
                <div style={{ display: 'flex', gap: '16px' }}>
                  <div style={{ flex: 1, backgroundColor: 'rgba(56, 189, 248, 0.1)', border: '1px solid rgba(56, 189, 248, 0.3)', borderRadius: '8px', padding: '8px 12px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#38bdf8', fontWeight: 700 }}>
                      <span>CT Side</span>
                      <span>Rating {analytics.side_split.ct_rating}</span>
                    </div>
                  </div>
                  <div style={{ flex: 1, backgroundColor: 'rgba(249, 115, 22, 0.1)', border: '1px solid rgba(249, 115, 22, 0.3)', borderRadius: '8px', padding: '8px 12px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#fb923c', fontWeight: 700 }}>
                      <span>T Side</span>
                      <span>Rating {analytics.side_split.t_rating}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Map Pool Performance Breakdown */}
          {analytics.maps.length > 0 && (
            <div
              style={{
                backgroundColor: '#0c1017',
                border: '1px solid #1a2233',
                borderRadius: '12px',
                padding: '16px 20px',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px',
              }}
            >
              <span style={{ fontSize: '14px', fontWeight: 800, color: '#f8fafc' }}>
                🗺️ {lang === 'ru' ? 'Результативность по картам соревновательного пула' : 'Map Pool Performance'}
              </span>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                <thead>
                  <tr style={{ color: '#64748b', borderBottom: '1px solid #1e293b', textAlign: 'left' }}>
                    <th style={{ padding: '8px' }}>{lang === 'ru' ? 'Карта' : 'Map'}</th>
                    <th style={{ padding: '8px' }}>{lang === 'ru' ? 'Матчей' : 'Matches'}</th>
                    <th style={{ padding: '8px' }}>Rating</th>
                    <th style={{ padding: '8px' }}>ADR</th>
                    <th style={{ padding: '8px' }}>K/D</th>
                    <th style={{ padding: '8px' }}>Winrate %</th>
                  </tr>
                </thead>
                <tbody>
                  {analytics.maps.map((m) => (
                    <tr key={m.map_name} style={{ borderBottom: '1px solid #131926', color: '#f1f5f9' }}>
                      <td style={{ padding: '8px', fontWeight: 700 }}>{m.map_name}</td>
                      <td style={{ padding: '8px' }}>{m.matches}</td>
                      <td style={{ padding: '8px', color: m.rating >= 1.15 ? '#22c55e' : '#38bdf8', fontWeight: 700 }}>{m.rating}</td>
                      <td style={{ padding: '8px' }}>{m.adr}</td>
                      <td style={{ padding: '8px' }}>{m.kd_ratio}</td>
                      <td style={{ padding: '8px', color: m.win_rate_pct >= 50 ? '#22c55e' : '#f87171' }}>{m.win_rate_pct}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* 7-Component Evidence-Based Coaching Recommendations */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '16px', fontWeight: 900, color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '8px' }}>
                📋 {lang === 'ru' ? 'Доказательные рекомендации и аудит хронических ошибок' : 'Evidence-Based Tactical Recommendations'}
              </span>
              <span style={{ fontSize: '11px', color: '#64748b' }}>
                {lang === 'ru' ? 'Строгий 7-компонентный доказательный контракт' : '7-component empirical contract'}
              </span>
            </div>

            {analytics.insights.map((ins) => {
              const severityColor =
                ins.severity === 'CRITICAL'
                  ? '#ef4444'
                  : ins.severity === 'WARNING'
                  ? '#facc15'
                  : ins.severity === 'OPTIMIZATION'
                  ? '#00f2fe'
                  : '#22c55e'

              return (
                <div
                  key={ins.id}
                  style={{
                    backgroundColor: '#0c1017',
                    border: `1px solid ${severityColor}40`,
                    borderLeft: `4px solid ${severityColor}`,
                    borderRadius: '10px',
                    padding: '16px 20px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '10px',
                    boxShadow: `0 4px 20px ${severityColor}10`,
                  }}
                >
                  {/* Card Title & Badges */}
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span
                        style={{
                          fontSize: '10px',
                          fontWeight: 800,
                          padding: '2px 7px',
                          borderRadius: '4px',
                          backgroundColor: `${severityColor}20`,
                          color: severityColor,
                        }}
                      >
                        {ins.severity}
                      </span>
                      <span style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 600 }}>
                        {ins.category}
                      </span>
                      <span style={{ fontSize: '14px', fontWeight: 800, color: '#f8fafc' }}>
                        {ins.title}
                      </span>
                    </div>

                    {/* Direct Jump Anchor into Demo Vision */}
                    {ins.jump_demo_id && ins.jump_round_num && ins.jump_tick && (
                      <button
                        type="button"
                        onClick={() =>
                          onJumpToDemoVision?.({
                            demoId: ins.jump_demo_id!,
                            roundNum: ins.jump_round_num!,
                            tick: ins.jump_tick!,
                          })
                        }
                        title={lang === 'ru' ? 'Открыть эпизод в 2D Demo Vision' : 'Open in 2D Demo Vision'}
                        style={{
                          backgroundColor: 'rgba(0, 242, 254, 0.15)',
                          border: '1px solid #00f2fe',
                          color: '#00f2fe',
                          padding: '4px 10px',
                          borderRadius: '6px',
                          fontSize: '11px',
                          fontWeight: 700,
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '5px',
                        }}
                      >
                        <span>Перейти в Demo Vision ➔ R{ins.jump_round_num}</span>
                      </button>
                    )}
                  </div>

                  {/* 1. Pattern Description */}
                  <div style={{ fontSize: '13px', color: '#cbd5e1', lineHeight: 1.4 }}>
                    <strong style={{ color: '#ffffff' }}>{lang === 'ru' ? 'Паттерн: ' : 'Pattern: '}</strong>
                    {ins.pattern_description}
                  </div>

                  {/* 2. Empirical Evidence (Sample size + Objective Metric) */}
                  <div
                    style={{
                      backgroundColor: '#111726',
                      borderRadius: '6px',
                      padding: '8px 12px',
                      fontSize: '12px',
                      color: '#94a3b8',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '4px',
                      border: '1px solid #1a2233',
                    }}
                  >
                    <div>
                      <strong style={{ color: '#f1f5f9' }}>{lang === 'ru' ? 'Объективные данные: ' : 'Objective Data: '}</strong>
                      {ins.objective_metric_str}
                    </div>
                    <div style={{ fontSize: '11px', color: '#64748b' }}>{ins.sample_size_str}</div>
                  </div>

                  {/* 3. Context & Alternative Strategy */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '12px' }}>
                    <div style={{ color: '#94a3b8' }}>
                      <strong style={{ color: '#e2e8f0' }}>{lang === 'ru' ? 'Контекст: ' : 'Context: '}</strong>
                      {ins.context_conditions_str}
                    </div>
                    <div style={{ color: '#a7f3d0' }}>
                      <strong style={{ color: '#34d399' }}>{lang === 'ru' ? 'Альтернатива: ' : 'Solution: '}</strong>
                      {ins.alternative_strategy_str}
                    </div>
                  </div>

                  {/* 4. Expected Impact */}
                  <div style={{ fontSize: '11px', color: '#facc15', fontWeight: 600 }}>
                    📈 {lang === 'ru' ? 'Оценка импакта: ' : 'Expected Impact: '} {ins.impact_estimate_str}
                  </div>
                </div>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}
