import React, { useState, useEffect } from 'react'
import type { PlayerAnalyticsDTO } from '../types'
import { api } from '../api'
import { Agent3DViewer } from './Agent3DViewer'


interface PlayerAnalyticsModalProps {
  demoId: number
  playerIdentifier: string
  playerName?: string
  playerTeam?: string | null
  onClose: () => void
  onViewHighlights?: (steamId: string | null) => void
}

export const PlayerAnalyticsModal: React.FC<PlayerAnalyticsModalProps> = ({
  demoId,
  playerIdentifier,
  playerName,
  playerTeam,
  onClose,
  onViewHighlights,
}) => {
  const [analytics, setAnalytics] = useState<PlayerAnalyticsDTO | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [errorFilter, setErrorFilter] = useState<'all' | 'critical' | 'warning' | 'info'>('all')
  const [show3DAgent, setShow3DAgent] = useState<boolean>(true)

  // Profile ownership in localStorage
  const [mySteamId, setMySteamId] = useState<string | null>(() => {
    return localStorage.getItem('my_steam_id')
  })

  const isMyProfile = mySteamId && (mySteamId === playerIdentifier || (analytics && mySteamId === analytics.steam_id))

  const handleToggleMyProfile = () => {
    if (isMyProfile) {
      localStorage.removeItem('my_steam_id')
      setMySteamId(null)
    } else {
      const idToSave = analytics?.steam_id || playerIdentifier
      localStorage.setItem('my_steam_id', idToSave)
      setMySteamId(idToSave)
    }
    window.dispatchEvent(new Event('my_steam_id_changed'))
  }

  useEffect(() => {
    let isCancelled = false
    setIsLoading(true)
    setError(null)

    api.getPlayerAnalytics(demoId, playerIdentifier)
      .then((data) => {
        if (!isCancelled) {
          setAnalytics(data)
          setIsLoading(false)
        }
      })
      .catch((err) => {
        if (!isCancelled) {
          setError(err.message || 'Не удалось загрузить детальную аналитику игрока')
          setIsLoading(false)
        }
      })

    return () => {
      isCancelled = true
    }
  }, [demoId, playerIdentifier])

  // Helper to calculate FACEIT level equivalent (1 to 10)
  const getFaceitLevel = (rating: number): { level: number; color: string; bg: string } => {
    if (rating >= 1.50) return { level: 10, color: '#ef4444', bg: 'rgba(239, 68, 68, 0.2)' }
    if (rating >= 1.35) return { level: 9, color: '#f97316', bg: 'rgba(249, 115, 22, 0.2)' }
    if (rating >= 1.25) return { level: 8, color: '#fbbf24', bg: 'rgba(251, 191, 36, 0.2)' }
    if (rating >= 1.15) return { level: 7, color: '#a3e635', bg: 'rgba(163, 230, 53, 0.2)' }
    if (rating >= 1.05) return { level: 6, color: '#22c55e', bg: 'rgba(34, 197, 94, 0.2)' }
    if (rating >= 0.95) return { level: 5, color: '#38bdf8', bg: 'rgba(56, 189, 248, 0.2)' }
    if (rating >= 0.85) return { level: 4, color: '#818cf8', bg: 'rgba(129, 140, 248, 0.2)' }
    if (rating >= 0.75) return { level: 3, color: '#c084fc', bg: 'rgba(192, 132, 252, 0.2)' }
    if (rating >= 0.65) return { level: 2, color: '#94a3b8', bg: 'rgba(148, 163, 184, 0.2)' }
    return { level: 1, color: '#64748b', bg: 'rgba(100, 116, 139, 0.2)' }
  }

  const faceitInfo = analytics ? getFaceitLevel(analytics.performance_rating) : { level: 5, color: '#38bdf8', bg: 'rgba(56, 189, 248, 0.2)' }

  const filteredErrors = analytics
    ? analytics.errors.filter((e) => errorFilter === 'all' || e.severity === errorFilter)
    : []

  const isCT = (playerTeam || analytics?.team || '').toLowerCase().includes('ct')

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.82)',
        backdropFilter: 'blur(8px)',
        zIndex: 1000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px',
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '920px',
          maxHeight: '90vh',
          backgroundColor: '#12141a',
          border: '1px solid #232836',
          borderRadius: '16px',
          boxShadow: '0 25px 60px rgba(0,0,0,0.7)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          animation: 'fadeIn 0.2s ease',
        }}
      >
        {/* Modal Top Bar */}
        <div
          style={{
            padding: '20px 24px',
            borderBottom: '1px solid #1f2430',
            backgroundColor: '#151821',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <div
              style={{
                width: '46px',
                height: '46px',
                borderRadius: '12px',
                backgroundColor: isCT ? 'rgba(56, 189, 248, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                color: isCT ? '#38bdf8' : '#f59e0b',
                border: `1px solid ${isCT ? 'rgba(56, 189, 248, 0.35)' : 'rgba(245, 158, 11, 0.35)'}`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 800,
                fontSize: '18px',
              }}
            >
              {(analytics?.name || playerName || 'P').slice(0, 2).toUpperCase()}
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h2 style={{ fontSize: '18px', fontWeight: 800, color: '#f1f5f9', margin: 0 }}>
                  {analytics?.name || playerName || 'Игрок'}
                </h2>
                <span
                  style={{
                    fontSize: '11px',
                    fontWeight: 700,
                    padding: '2px 8px',
                    borderRadius: '4px',
                    backgroundColor: isCT ? 'rgba(56, 189, 248, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                    color: isCT ? '#38bdf8' : '#f59e0b',
                  }}
                >
                  {isCT ? 'CT' : 'TERRORIST'}
                </span>
                {isMyProfile && (
                  <span
                    style={{
                      fontSize: '11px',
                      fontWeight: 700,
                      padding: '2px 8px',
                      borderRadius: '4px',
                      backgroundColor: 'rgba(245, 158, 11, 0.2)',
                      color: '#fbbf24',
                      border: '1px solid rgba(245, 158, 11, 0.4)',
                    }}
                  >
                    ⭐ МОЙ ПРОФИЛЬ
                  </span>
                )}
              </div>
              <div style={{ fontSize: '12px', color: '#64748b', marginTop: '2px' }}>
                Steam ID: {analytics?.steam_id || playerIdentifier || 'N/A'} • {analytics?.total_rounds || 0} сыгранных раундов
              </div>
            </div>
          </div>

          {/* Action Header Items */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button
              type="button"
              className={show3DAgent ? 'btn btn-primary' : 'btn btn-secondary'}
              onClick={() => setShow3DAgent(!show3DAgent)}
              style={{
                fontSize: '12px',
                padding: '7px 12px',
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
              }}
              title="Интерактивная 3D модель оперативника CS2"
            >
              <span>{show3DAgent ? '🛡️ 3D Модель: Вкл' : '🌐 3D Модель: Выкл'}</span>
            </button>
            <button
              type="button"
              className={isMyProfile ? 'btn btn-secondary' : 'btn btn-primary'}
              onClick={handleToggleMyProfile}
              style={{
                fontSize: '12px',
                padding: '7px 14px',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                borderColor: isMyProfile ? '#fbbf24' : undefined,
                color: isMyProfile ? '#fbbf24' : undefined,
              }}
              title="Запомнить этого игрока как ваш личный профиль"
            >
              <span>{isMyProfile ? '★ Профиль выбран' : '☆ Это я (Мой профиль)'}</span>
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onClose}
              style={{
                fontSize: '14px',
                padding: '6px 12px',
                backgroundColor: 'transparent',
                borderColor: '#2d3345',
              }}
            >
              ✕
            </button>
          </div>
        </div>

        {/* Modal Scrollable Body */}
        <div style={{ padding: '24px', overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {isLoading && (
            <div style={{ textAlign: 'center', padding: '60px 0', color: '#94a3b8' }}>
              <div style={{ fontSize: '28px', marginBottom: '12px', animation: 'spin 1.5s linear infinite' }}>⚙️</div>
              <div>Вычисляем статистику FACEIT, SWING и аудит тактических ошибок...</div>
            </div>
          )}

          {error && (
            <div
              style={{
                padding: '16px',
                borderRadius: '8px',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                color: '#f87171',
                fontSize: '14px',
              }}
            >
              ⚠️ {error}
            </div>
          )}

          {analytics && (
            <>
              {/* Interactive 3D Tactical Agent Visualizer */}
              {show3DAgent && (
                <div style={{ marginBottom: '6px' }}>
                  <Agent3DViewer
                    team={analytics.team || playerTeam}
                    playerName={analytics.name || playerName}
                    role={
                      analytics.kd_ratio >= 1.3
                        ? 'Star Fragger (MVP)'
                        : analytics.headshot_pct >= 60
                        ? 'Precision Marksman'
                        : analytics.opening_winrate_pct >= 60
                        ? 'Opening Duelist'
                        : 'Support & Anchor'
                    }
                    height={260}
                    weapon={
                      analytics.headshot_pct > 50
                        ? (analytics.team || '').toLowerCase().includes('ct')
                          ? 'M4A1-S'
                          : 'AK-47'
                        : 'AWP'
                    }
                  />
                </div>
              )}

              {/* FACEIT & COMBAT HERO CARD */}
              <div
                style={{
                  background: 'linear-gradient(135deg, #181d27 0%, #151821 100%)',
                  border: '1px solid #283042',
                  borderRadius: '14px',
                  padding: '20px 24px',
                  display: 'grid',
                  gridTemplateColumns: 'auto 1fr',
                  gap: '24px',
                  alignItems: 'center',
                }}
              >

                {/* Level Badge */}
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px' }}>
                  <div
                    style={{
                      width: '68px',
                      height: '68px',
                      borderRadius: '16px',
                      backgroundColor: faceitInfo.bg,
                      border: `2px solid ${faceitInfo.color}`,
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      justifyContent: 'center',
                      boxShadow: `0 0 20px ${faceitInfo.bg}`,
                    }}
                  >
                    <span style={{ fontSize: '10px', fontWeight: 800, color: '#94a3b8', textTransform: 'uppercase' }}>LVL</span>
                    <span style={{ fontSize: '28px', fontWeight: 900, color: faceitInfo.color, lineHeight: 1 }}>
                      {faceitInfo.level}
                    </span>
                  </div>
                  <span style={{ fontSize: '11px', fontWeight: 700, color: '#94a3b8' }}>FACEIT RATING</span>
                </div>

                {/* Main Stats Row */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '16px' }}>
                  <div style={{ backgroundColor: '#101217', padding: '12px 14px', borderRadius: '10px', border: '1px solid #1f2430' }}>
                    <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 600 }}>PERFORMANCE SCORE</div>
                    <div className="num" style={{ fontSize: '22px', fontWeight: 800, color: faceitInfo.color, marginTop: '2px' }}>
                      {analytics.performance_rating.toFixed(2)}
                    </div>
                  </div>

                  <div style={{ backgroundColor: '#101217', padding: '12px 14px', borderRadius: '10px', border: '1px solid #1f2430' }}>
                    <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 600 }}>K / D RATIO</div>
                    <div className="num" style={{ fontSize: '22px', fontWeight: 800, color: analytics.kd_ratio >= 1.0 ? '#34d399' : '#f87171', marginTop: '2px' }}>
                      {analytics.kd_ratio.toFixed(2)}
                    </div>
                    <div style={{ fontSize: '11px', color: '#94a3b8' }}>
                      {analytics.kills}K - {analytics.deaths}D
                    </div>
                  </div>

                  <div style={{ backgroundColor: '#101217', padding: '12px 14px', borderRadius: '10px', border: '1px solid #1f2430' }}>
                    <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 600 }}>HEADSHOT %</div>
                    <div className="num" style={{ fontSize: '22px', fontWeight: 800, color: '#f1f5f9', marginTop: '2px' }}>
                      {analytics.headshot_pct.toFixed(1)}%
                    </div>
                    <div style={{ fontSize: '11px', color: '#94a3b8' }}>
                      {analytics.assists} assists
                    </div>
                  </div>

                  <div style={{ backgroundColor: '#101217', padding: '12px 14px', borderRadius: '10px', border: '1px solid #1f2430' }}>
                    <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 600 }}>KAST %</div>
                    <div className="num" style={{ fontSize: '22px', fontWeight: 800, color: analytics.kast_pct >= 70 ? '#38bdf8' : '#f59e0b', marginTop: '2px' }}>
                      {analytics.kast_pct.toFixed(1)}%
                    </div>
                    <div style={{ fontSize: '11px', color: '#94a3b8' }}>
                      K / A / S / Traded
                    </div>
                  </div>

                  <div style={{ backgroundColor: '#101217', padding: '12px 14px', borderRadius: '10px', border: '1px solid #1f2430' }}>
                    <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 600 }}>KILLS PER ROUND</div>
                    <div className="num" style={{ fontSize: '22px', fontWeight: 800, color: '#f1f5f9', marginTop: '2px' }}>
                      {analytics.kpr.toFixed(2)}
                    </div>
                    <div style={{ fontSize: '11px', color: '#94a3b8' }}>
                      DPR: {analytics.dpr.toFixed(2)}
                    </div>
                  </div>
                </div>
              </div>

              {/* ADVANCED PARAMETERS: SWING, AIM & PRECISION, OPENING & TRADES */}
              <div>
                <h3 style={{ fontSize: '14px', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '12px' }}>
                  🎯 Углублённая боевая статистика (SWING & Механика)
                </h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '14px' }}>
                  {/* SWING / Peek Winrate */}
                  <div style={{ backgroundColor: '#161922', border: '1px solid #232836', borderRadius: '12px', padding: '16px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8' }}>SWING / Peek Winrate</span>
                      <span style={{ fontSize: '14px' }}>⚡</span>
                    </div>
                    <div className="num" style={{ fontSize: '24px', fontWeight: 800, color: '#38bdf8', margin: '6px 0 8px 0' }}>
                      {analytics.swing_winrate_pct.toFixed(1)}%
                    </div>
                    {/* Progress bar */}
                    <div style={{ height: '5px', backgroundColor: '#232836', borderRadius: '3px', overflow: 'hidden' }}>
                      <div
                        style={{
                          height: '100%',
                          width: `${Math.min(100, Math.max(0, analytics.swing_winrate_pct))}%`,
                          backgroundColor: '#38bdf8',
                        }}
                      />
                    </div>
                    <div style={{ fontSize: '11px', color: '#64748b', marginTop: '6px' }}>
                      Винрейт первых агрессивных выходов и пиков
                    </div>
                  </div>

                  {/* Crosshair Placement */}
                  <div style={{ backgroundColor: '#161922', border: '1px solid #232836', borderRadius: '12px', padding: '16px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8' }}>Crosshair Placement</span>
                      <span style={{ fontSize: '14px' }}>🎯</span>
                    </div>
                    <div className="num" style={{ fontSize: '24px', fontWeight: 800, color: '#34d399', margin: '6px 0 8px 0' }}>
                      {analytics.crosshair_placement_score.toFixed(0)} <span style={{ fontSize: '13px', color: '#64748b' }}>/ 100</span>
                    </div>
                    <div style={{ height: '5px', backgroundColor: '#232836', borderRadius: '3px', overflow: 'hidden' }}>
                      <div
                        style={{
                          height: '100%',
                          width: `${Math.min(100, Math.max(0, analytics.crosshair_placement_score))}%`,
                          backgroundColor: '#34d399',
                        }}
                      />
                    </div>
                    <div style={{ fontSize: '11px', color: '#64748b', marginTop: '6px' }}>
                      Точность удержания прицела на уровне головы
                    </div>
                  </div>

                  {/* First Bullet Accuracy */}
                  <div style={{ backgroundColor: '#161922', border: '1px solid #232836', borderRadius: '12px', padding: '16px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8' }}>First Bullet Accuracy</span>
                      <span style={{ fontSize: '14px' }}>🔫</span>
                    </div>
                    <div className="num" style={{ fontSize: '24px', fontWeight: 800, color: '#fbbf24', margin: '6px 0 8px 0' }}>
                      {analytics.first_bullet_accuracy_pct.toFixed(1)}%
                    </div>
                    <div style={{ height: '5px', backgroundColor: '#232836', borderRadius: '3px', overflow: 'hidden' }}>
                      <div
                        style={{
                          height: '100%',
                          width: `${Math.min(100, Math.max(0, analytics.first_bullet_accuracy_pct))}%`,
                          backgroundColor: '#fbbf24',
                        }}
                      />
                    </div>
                    <div style={{ fontSize: '11px', color: '#64748b', marginTop: '6px' }}>
                      Попадание первой пулей при контакте
                    </div>
                  </div>

                  {/* Spray Control */}
                  <div style={{ backgroundColor: '#161922', border: '1px solid #232836', borderRadius: '12px', padding: '16px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8' }}>Spray Control</span>
                      <span style={{ fontSize: '14px' }}>🌊</span>
                    </div>
                    <div className="num" style={{ fontSize: '24px', fontWeight: 800, color: '#a78bfa', margin: '6px 0 8px 0' }}>
                      {analytics.spray_control_pct.toFixed(1)}%
                    </div>
                    <div style={{ height: '5px', backgroundColor: '#232836', borderRadius: '3px', overflow: 'hidden' }}>
                      <div
                        style={{
                          height: '100%',
                          width: `${Math.min(100, Math.max(0, analytics.spray_control_pct))}%`,
                          backgroundColor: '#a78bfa',
                        }}
                      />
                    </div>
                    <div style={{ fontSize: '11px', color: '#64748b', marginTop: '6px' }}>
                      Контроль зажима и удержание отдачи
                    </div>
                  </div>
                </div>
              </div>

              {/* DUELS, TRADES & CLUTCHES ROW */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '14px' }}>
                {/* Opening Duels */}
                <div style={{ backgroundColor: '#161922', border: '1px solid #232836', borderRadius: '12px', padding: '16px' }}>
                  <div style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8', marginBottom: '4px' }}>
                    ⚔️ ПЕРВЫЕ ДУЭЛИ (OPENING DUELS)
                  </div>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', margin: '8px 0' }}>
                    <span className="num" style={{ fontSize: '24px', fontWeight: 800, color: '#34d399' }}>
                      {analytics.opening_duels_won}W
                    </span>
                    <span style={{ color: '#64748b' }}>/</span>
                    <span className="num" style={{ fontSize: '24px', fontWeight: 800, color: '#f87171' }}>
                      {analytics.opening_duels_lost}L
                    </span>
                    <span style={{ marginLeft: 'auto', fontSize: '13px', fontWeight: 700, color: '#38bdf8' }}>
                      {analytics.opening_winrate_pct.toFixed(1)}% WR
                    </span>
                  </div>
                  <div style={{ fontSize: '11px', color: '#64748b' }}>
                    Первый килл или первая смерть в раунде
                  </div>
                </div>

                {/* Trade Efficiency */}
                <div style={{ backgroundColor: '#161922', border: '1px solid #232836', borderRadius: '12px', padding: '16px' }}>
                  <div style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8', marginBottom: '4px' }}>
                    🤝 РАЗМЕН ТИММЕЙТОВ (TRADE EFFICIENCY)
                  </div>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', margin: '8px 0' }}>
                    <span className="num" style={{ fontSize: '24px', fontWeight: 800, color: '#38bdf8' }}>
                      {analytics.trade_kills}
                    </span>
                    <span style={{ fontSize: '12px', color: '#94a3b8' }}>
                      киллов ({analytics.trade_kill_pct.toFixed(0)}%)
                    </span>
                    <span style={{ marginLeft: 'auto', fontSize: '11px', color: '#94a3b8' }}>
                      Разменяно: {analytics.traded_deaths} ({analytics.traded_death_pct.toFixed(0)}%)
                    </span>
                  </div>
                  <div style={{ fontSize: '11px', color: '#64748b' }}>
                    Ответный килл врага в течение 4 секунд
                  </div>
                </div>

                {/* Clutches */}
                <div style={{ backgroundColor: '#161922', border: '1px solid #232836', borderRadius: '12px', padding: '16px' }}>
                  <div style={{ fontSize: '12px', fontWeight: 600, color: '#94a3b8', marginBottom: '4px' }}>
                    🏆 КЛАТЧИ (1vX SITUATIONS)
                  </div>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', margin: '8px 0' }}>
                    <span className="num" style={{ fontSize: '24px', fontWeight: 800, color: '#fbbf24' }}>
                      {analytics.clutches_won}
                    </span>
                    <span style={{ fontSize: '12px', color: '#94a3b8' }}>
                      выиграно из {analytics.clutches_attempted}
                    </span>
                    <span style={{ marginLeft: 'auto', fontSize: '13px', fontWeight: 700, color: '#fbbf24' }}>
                      {analytics.clutch_winrate_pct.toFixed(0)}% WR
                    </span>
                  </div>
                  <div style={{ fontSize: '11px', color: '#64748b' }}>
                    Победы один против одного или нескольких врагов
                  </div>
                </div>
              </div>

              {/* TACTICAL ERROR AUDIT SECTION */}
              <div
                style={{
                  backgroundColor: '#161821',
                  border: '1px solid #232836',
                  borderRadius: '14px',
                  padding: '20px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                  <div>
                    <h3 style={{ fontSize: '15px', fontWeight: 800, color: '#f1f5f9', margin: 0 }}>
                      🚨 Аудит тактических ошибок в матче ({analytics.errors.length})
                    </h3>
                    <div style={{ fontSize: '12px', color: '#64748b' }}>
                      Автоматический разбор невынужденных смертей, оверпиков при большинстве и потерь позиций
                    </div>
                  </div>

                  {/* Filter tabs */}
                  <div style={{ display: 'flex', gap: '6px' }}>
                    {(['all', 'critical', 'warning', 'info'] as const).map((lvl) => {
                      const count = lvl === 'all'
                        ? analytics.errors.length
                        : analytics.errors.filter((e) => e.severity === lvl).length
                      return (
                        <button
                          key={lvl}
                          type="button"
                          className={errorFilter === lvl ? 'btn btn-primary' : 'btn btn-secondary'}
                          style={{
                            fontSize: '11px',
                            padding: '4px 10px',
                            textTransform: 'capitalize',
                          }}
                          onClick={() => setErrorFilter(lvl)}
                        >
                          {lvl === 'all' ? 'Все' : lvl === 'critical' ? 'Критические' : lvl === 'warning' ? 'Предупреждения' : 'Инфо'} ({count})
                        </button>
                      )
                    })}
                  </div>
                </div>

                {filteredErrors.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: '32px 0', color: '#34d399', fontSize: '13px' }}>
                    <div style={{ fontSize: '24px', marginBottom: '6px' }}>🛡️</div>
                    <div>В выбранной категории ошибок не зафиксировано! Отличная игровая дисциплина.</div>
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {filteredErrors.map((err, idx) => {
                      const isCrit = err.severity === 'critical'
                      const isWarn = err.severity === 'warning'
                      return (
                        <div
                          key={idx}
                          style={{
                            backgroundColor: '#12141a',
                            border: `1px solid ${isCrit ? 'rgba(239, 68, 68, 0.4)' : isWarn ? 'rgba(245, 158, 11, 0.3)' : '#232836'}`,
                            borderRadius: '10px',
                            padding: '12px 16px',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            gap: '16px',
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                            <span style={{ fontSize: '18px', marginTop: '2px' }}>
                              {isCrit ? '❌' : isWarn ? '⚠️' : 'ℹ️'}
                            </span>
                            <div>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <span style={{ fontWeight: 700, fontSize: '13px', color: '#f1f5f9' }}>
                                  {err.title}
                                </span>
                                <span
                                  style={{
                                    fontSize: '10px',
                                    fontWeight: 700,
                                    padding: '1px 6px',
                                    borderRadius: '4px',
                                    backgroundColor: isCrit ? 'rgba(239, 68, 68, 0.2)' : isWarn ? 'rgba(245, 158, 11, 0.2)' : 'rgba(56, 189, 248, 0.15)',
                                    color: isCrit ? '#f87171' : isWarn ? '#fbbf24' : '#38bdf8',
                                  }}
                                >
                                  {err.severity.toUpperCase()}
                                </span>
                              </div>
                              <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '3px' }}>
                                {err.description}
                              </div>
                            </div>
                          </div>

                          <div style={{ textAlign: 'right', minWidth: '100px' }}>
                            <div style={{ fontSize: '12px', fontWeight: 700, color: '#f1f5f9' }}>
                              Раунд {err.round_num}
                            </div>
                            <div className="num" style={{ fontSize: '11px', color: '#64748b' }}>
                              тик {err.tick}
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>

              {/* COACHING ADVICE & STRENGTHS */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                {/* Strengths */}
                <div style={{ backgroundColor: '#161922', border: '1px solid #232836', borderRadius: '12px', padding: '18px' }}>
                  <div style={{ fontSize: '13px', fontWeight: 700, color: '#34d399', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span>✅</span> Сильные стороны игрока в матче
                  </div>
                  {analytics.strengths.length === 0 ? (
                    <div style={{ fontSize: '12px', color: '#64748b' }}>Стабильная базовая игра без выраженных пиковых метрик.</div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      {analytics.strengths.map((str, i) => (
                        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: '#e2e8f0' }}>
                          <span style={{ color: '#34d399', fontWeight: 800 }}>•</span>
                          <span>{str}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Advice */}
                <div style={{ backgroundColor: '#161922', border: '1px solid #232836', borderRadius: '12px', padding: '18px' }}>
                  <div style={{ fontSize: '13px', fontWeight: 700, color: '#fbbf24', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span>💡</span> Советы тренера по улучшению
                  </div>
                  {analytics.advice.length === 0 ? (
                    <div style={{ fontSize: '12px', color: '#64748b' }}>Продолжайте придерживаться текущего темпа и позиционки.</div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      {analytics.advice.map((adv, i) => (
                        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: '#e2e8f0' }}>
                          <span style={{ color: '#fbbf24', fontWeight: 800 }}>•</span>
                          <span>{adv}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </>
          )}
        </div>

        {/* Modal Footer */}
        <div
          style={{
            padding: '16px 24px',
            borderTop: '1px solid #1f2430',
            backgroundColor: '#151821',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div style={{ fontSize: '12px', color: '#64748b' }}>
            Метрики рассчитываются на основе фактических событий демки CS2
          </div>
          <div style={{ display: 'flex', gap: '10px' }}>
            {onViewHighlights && (
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => {
                  onClose()
                  onViewHighlights(analytics?.steam_id || playerIdentifier)
                }}
                style={{ fontSize: '12px', padding: '8px 16px' }}
              >
                🎬 Посмотреть хайлайты игрока →
              </button>
            )}
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onClose}
              style={{ fontSize: '12px', padding: '8px 16px' }}
            >
              Закрыть
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
