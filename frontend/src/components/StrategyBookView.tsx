import React, { useEffect, useState } from 'react'
import { api } from '../api'
import type { StrategyBookDTO, TacticalSetupDTO } from '../types'
import { useTranslation } from '../i18n'

interface StrategyBookViewProps {
  currentMapName?: string
  onJumpToDemoVision?: (target: { demoId?: number; roundNum: number; tick: number }) => void
}

export const StrategyBookView: React.FC<StrategyBookViewProps> = ({
  currentMapName = 'de_mirage',
}) => {
  const { lang } = useTranslation()
  const [books, setBooks] = useState<StrategyBookDTO[]>([])
  const [selectedBookId, setSelectedBookId] = useState<string>('')
  const [activeBook, setActiveBook] = useState<StrategyBookDTO | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [activeTab, setActiveTab] = useState<'setups' | 'lineups' | 'protocols'>('setups')

  // Modals state
  const [createBookModalOpen, setCreateBookModalOpen] = useState<boolean>(false)
  const [newBookTitle, setNewBookTitle] = useState<string>('')
  const [newBookMap, setNewBookMap] = useState<string>(currentMapName)
  const [newBookTeam, setNewBookTeam] = useState<string>('demToshka Team')
  const [newBookDesc, setNewBookDesc] = useState<string>('')

  const [createSetupModalOpen, setCreateSetupModalOpen] = useState<boolean>(false)
  const [newSetupTitle, setNewSetupTitle] = useState<string>('')
  const [newSetupSide, setNewSetupSide] = useState<string>('t')
  const [newSetupPhase, setNewSetupPhase] = useState<string>('default')
  const [newSetupDesc, setNewSetupDesc] = useState<string>('')

  // Load books list on mount
  useEffect(() => {
    loadBooks()
  }, [])

  const loadBooks = async () => {
    try {
      const list = await api.getStrategyBooks()
      setBooks(list)
      if (list.length > 0 && !selectedBookId) {
        setSelectedBookId(list[0].id)
      } else if (list.length === 0) {
        // Auto-create initial default book if none exists
        const defaultBook = await api.createStrategyBook({
          title: `${currentMapName.toUpperCase()} Tactical Playbook`,
          map_name: currentMapName,
          team_name: 'demToshka Squad',
          description: 'Official match tactical setups, default protocols and grenade execute lineups.',
        })
        setBooks([defaultBook])
        setSelectedBookId(defaultBook.id)
      }
    } catch (err) {
      console.error('Failed to load strategy books:', err)
    }
  }

  // Load active book details when selectedBookId changes
  useEffect(() => {
    if (!selectedBookId) return
    setIsLoading(true)
    api
      .getStrategyBook(selectedBookId)
      .then((data) => {
        setActiveBook(data)
        setIsLoading(false)
      })
      .catch((err) => {
        console.error('Failed to load book details:', err)
        setIsLoading(false)
      })
  }, [selectedBookId])

  const handleCreateBook = async () => {
    if (!newBookTitle.trim()) return
    try {
      const created = await api.createStrategyBook({
        title: newBookTitle.trim(),
        map_name: newBookMap,
        team_name: newBookTeam.trim() || undefined,
        description: newBookDesc.trim() || undefined,
      })
      setBooks((prev) => [created, ...prev])
      setSelectedBookId(created.id)
      setCreateBookModalOpen(false)
      setNewBookTitle('')
      setNewBookDesc('')
    } catch (err) {
      console.error('Failed to create strategy book:', err)
    }
  }

  const handleCreateSetup = async () => {
    if (!activeBook?.id || !newSetupTitle.trim()) return
    try {
      // Default sample token positions for the new setup
      const sampleTokens =
        newSetupSide === 'ct'
          ? [
              { x: 260, y: 320, side: 'ct', role: 'Anchor B', callout: 'Site B', yaw: 180 },
              { x: 740, y: 280, side: 'ct', role: 'Anchor A', callout: 'Site A', yaw: 45 },
              { x: 500, y: 480, side: 'ct', role: 'AWP Mid', callout: 'Window', yaw: 90 },
            ]
          : [
              { x: 420, y: 720, side: 't', role: 'Entry 1', callout: 'Ramp', yaw: 45 },
              { x: 480, y: 760, side: 't', role: 'Support', callout: 'T-Roof', yaw: 60 },
            ]

      const sampleDrawings = [
        {
          layer_type: 'arrow',
          color: newSetupSide === 'ct' ? '#38bdf8' : '#fb923c',
          geometry_json: JSON.stringify({ x1: 420, y1: 720, x2: 740, y2: 280 }),
        },
      ]

      const created = await api.addTacticalSetup(activeBook.id, {
        title: newSetupTitle.trim(),
        side: newSetupSide,
        phase: newSetupPhase,
        description: newSetupDesc.trim() || undefined,
        tokens_json: JSON.stringify(sampleTokens),
        drawings_json: JSON.stringify(sampleDrawings),
      })

      setActiveBook((prev) =>
        prev ? { ...prev, setups: [...prev.setups, created] } : null
      )
      setCreateSetupModalOpen(false)
      setNewSetupTitle('')
      setNewSetupDesc('')
    } catch (err) {
      console.error('Failed to create setup:', err)
    }
  }

  const handleDeleteSetup = async (setupId: string) => {
    if (!activeBook?.id) return
    try {
      await api.deleteTacticalSetup(activeBook.id, setupId)
      setActiveBook((prev) =>
        prev ? { ...prev, setups: prev.setups.filter((s) => s.id !== setupId) } : null
      )
    } catch (err) {
      console.error('Failed to delete setup:', err)
    }
  }

  // Helper to render mini SVG radar for each setup
  const renderSetupMiniRadar = (setup: TacticalSetupDTO) => {
    let tokens: any[] = []
    let drawings: any[] = []
    try {
      tokens = JSON.parse(setup.tokens_json || '[]')
    } catch (_) {}
    try {
      drawings = JSON.parse(setup.drawings_json || '[]')
    } catch (_) {}

    return (
      <svg
        viewBox="0 0 1000 1000"
        style={{
          width: '100%',
          height: '240px',
          backgroundColor: '#090d16',
          borderRadius: '8px',
          border: '1px solid #162030',
        }}
      >
        {/* Radar Base Grid */}
        <path
          d="M 0 250 H 1000 M 0 500 H 1000 M 0 750 H 1000 M 250 0 V 1000 M 500 0 V 1000 M 750 0 V 1000"
          stroke="#161f30"
          strokeWidth="1"
        />
        <circle cx="500" cy="500" r="420" fill="none" stroke="#1a253a" strokeWidth="2" />

        {/* Bombsites Outlines */}
        <rect x="680" y="220" width="160" height="140" fill="rgba(239, 68, 68, 0.08)" stroke="#ef4444" strokeWidth="1.5" strokeDasharray="5,5" rx="8"/>
        <text x="760" y="300" fill="#ef4444" fontSize="28" fontWeight="900" textAnchor="middle">A</text>
        <rect x="180" y="240" width="160" height="140" fill="rgba(239, 68, 68, 0.08)" stroke="#ef4444" strokeWidth="1.5" strokeDasharray="5,5" rx="8"/>
        <text x="260" y="320" fill="#ef4444" fontSize="28" fontWeight="900" textAnchor="middle">B</text>

        {/* Drawings */}
        {drawings.map((d, i) => {
          let geom: any = {}
          try { geom = JSON.parse(d.geometry_json || '{}') } catch (_) {}
          if (d.layer_type === 'arrow') {
            return (
              <g key={i}>
                <line x1={geom.x1} y1={geom.y1} x2={geom.x2} y2={geom.y2} stroke={d.color || '#00f2fe'} strokeWidth="4" strokeLinecap="round" />
                <circle cx={geom.x2} cy={geom.y2} r="6" fill={d.color || '#00f2fe'} />
              </g>
            )
          }
          return null
        })}

        {/* Tokens */}
        {tokens.map((tok, i) => {
          const isCT = tok.side === 'ct'
          const col = isCT ? '#38bdf8' : '#fb923c'
          return (
            <g key={i}>
              <circle cx={tok.x} cy={tok.y} r="18" fill="#0f172a" stroke={col} strokeWidth="3" />
              <circle cx={tok.x} cy={tok.y} r="12" fill={col} />
              <text x={tok.x} y={tok.y + 4} fill="#000000" fontSize="10" fontWeight="900" textAnchor="middle">
                {tok.side.toUpperCase()}
              </text>
              <rect x={tok.x - 45} y={tok.y + 22} width="90" height="18" fill="rgba(11, 15, 23, 0.9)" stroke={col} strokeWidth="1" rx="4"/>
              <text x={tok.x} y={tok.y + 35} fill="#f1f5f9" fontSize="10" fontWeight="800" textAnchor="middle">
                {tok.role}
              </text>
            </g>
          )
        })}
      </svg>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Top Header Bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          backgroundColor: '#0c1017',
          padding: '16px 20px',
          borderRadius: '12px',
          border: '1px solid #1a2233',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div
            style={{
              width: '44px',
              height: '44px',
              borderRadius: '8px',
              backgroundColor: '#131926',
              border: '2px solid #facc15',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '22px',
            }}
          >
            📖
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '18px', fontWeight: 900, color: '#f8fafc' }}>
                {activeBook?.title || 'Tactical Strategy Book'}
              </span>
              <span
                style={{
                  backgroundColor: 'rgba(250, 204, 21, 0.15)',
                  color: '#facc15',
                  border: '1px solid rgba(250, 204, 21, 0.4)',
                  padding: '2px 8px',
                  borderRadius: '12px',
                  fontSize: '11px',
                  fontWeight: 700,
                }}
              >
                {activeBook?.map_name.toUpperCase()}
              </span>
            </div>
            <span style={{ fontSize: '12px', color: '#64748b' }}>
              {activeBook?.description || 'Tactical playbooks, site takes and utility lineups.'}
            </span>
          </div>
        </div>

        {/* Top Actions: Playbook Switcher, Add Setup, Offline HTML Export */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {books.length > 0 && (
            <select
              value={selectedBookId}
              onChange={(e) => setSelectedBookId(e.target.value)}
              style={{
                backgroundColor: '#131926',
                color: '#f8fafc',
                border: '1px solid #334155',
                borderRadius: '8px',
                padding: '6px 12px',
                fontSize: '12px',
                fontWeight: 600,
                outline: 'none',
              }}
            >
              {books.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.title} ({b.map_name})
                </option>
              ))}
            </select>
          )}

          <button
            type="button"
            onClick={() => setCreateBookModalOpen(true)}
            style={{
              backgroundColor: '#1e293b',
              color: '#f1f5f9',
              border: '1px solid #334155',
              borderRadius: '8px',
              padding: '6px 12px',
              fontSize: '12px',
              fontWeight: 700,
              cursor: 'pointer',
            }}
          >
            + {lang === 'ru' ? 'Плейбук' : 'Playbook'}
          </button>

          <button
            type="button"
            onClick={() => setCreateSetupModalOpen(true)}
            style={{
              backgroundColor: '#00f2fe',
              color: '#000000',
              border: 'none',
              borderRadius: '8px',
              padding: '6px 14px',
              fontSize: '12px',
              fontWeight: 800,
              cursor: 'pointer',
            }}
          >
            + {lang === 'ru' ? 'Новый сетап' : 'Add Setup'}
          </button>

          {activeBook && (
            <a
              href={api.getStrategyBookExportUrl(activeBook.id)}
              download
              target="_blank"
              rel="noreferrer"
              style={{
                backgroundColor: '#facc15',
                color: '#000000',
                border: 'none',
                borderRadius: '8px',
                padding: '6px 14px',
                fontSize: '12px',
                fontWeight: 800,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                textDecoration: 'none',
                boxShadow: '0 4px 14px rgba(250, 204, 21, 0.3)',
              }}
            >
              <span>🖨️</span>
              <span>{lang === 'ru' ? 'Экспорт в HTML / PDF' : 'Export to HTML / PDF'}</span>
            </a>
          )}
        </div>
      </div>

      {/* Tabs Switcher */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid #1e293b', paddingBottom: '8px' }}>
        <button
          type="button"
          onClick={() => setActiveTab('setups')}
          style={{
            background: activeTab === 'setups' ? '#1e293b' : 'transparent',
            color: activeTab === 'setups' ? '#00f2fe' : '#94a3b8',
            border: activeTab === 'setups' ? '1px solid #334155' : '1px solid transparent',
            padding: '6px 16px',
            borderRadius: '6px',
            fontSize: '13px',
            fontWeight: 700,
            cursor: 'pointer',
          }}
        >
          📋 {lang === 'ru' ? 'Тактические сетапы' : 'Tactical Setups'} ({activeBook?.setups.length || 0})
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('protocols')}
          style={{
            background: activeTab === 'protocols' ? '#1e293b' : 'transparent',
            color: activeTab === 'protocols' ? '#00f2fe' : '#94a3b8',
            border: activeTab === 'protocols' ? '1px solid #334155' : '1px solid transparent',
            padding: '6px 16px',
            borderRadius: '6px',
            fontSize: '13px',
            fontWeight: 700,
            cursor: 'pointer',
          }}
        >
          📖 {lang === 'ru' ? '11 Протоколов команды' : '11 Team Protocols'}
        </button>
      </div>

      {isLoading && (
        <div style={{ textAlign: 'center', padding: '40px', color: '#94a3b8', fontSize: '13px' }}>
          ⏳ {lang === 'ru' ? 'Загрузка плейбука...' : 'Loading playbook...'}
        </div>
      )}

      {/* Tab Content: Setups Grid */}
      {activeTab === 'setups' && activeBook && !isLoading && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(480px, 1fr))',
            gap: '20px',
          }}
        >
          {activeBook.setups.length === 0 ? (
            <div
              style={{
                gridColumn: '1 / -1',
                padding: '40px',
                textAlign: 'center',
                color: '#64748b',
                backgroundColor: '#0c1017',
                borderRadius: '12px',
                border: '1px solid #1a2233',
              }}
            >
              {lang === 'ru'
                ? 'Сетапы ещё не добавлены. Нажмите "+ Новый сетап", чтобы добавить расстановку игроков на карте.'
                : 'No setups yet. Click "+ Add Setup" to create player positioning schemes on the map.'}
            </div>
          ) : (
            activeBook.setups.map((s) => {
              const isCT = s.side.toLowerCase() === 'ct'
              const sideColor = isCT ? '#38bdf8' : '#fb923c'
              return (
                <div
                  key={s.id}
                  style={{
                    backgroundColor: '#0c1017',
                    border: '1px solid #1a2233',
                    borderRadius: '12px',
                    padding: '16px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '12px',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span
                        style={{
                          fontSize: '10px',
                          fontWeight: 800,
                          padding: '2px 7px',
                          borderRadius: '4px',
                          backgroundColor: `${sideColor}20`,
                          color: sideColor,
                          border: `1px solid ${sideColor}50`,
                        }}
                      >
                        {s.side.toUpperCase()}
                      </span>
                      <span style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase' }}>
                        {s.phase}
                      </span>
                      <span style={{ fontSize: '14px', fontWeight: 800, color: '#f8fafc' }}>
                        {s.title}
                      </span>
                    </div>

                    <button
                      type="button"
                      onClick={() => handleDeleteSetup(s.id)}
                      title={lang === 'ru' ? 'Удалить сетап' : 'Delete setup'}
                      style={{
                        background: 'none',
                        border: 'none',
                        color: '#64748b',
                        cursor: 'pointer',
                        fontSize: '14px',
                      }}
                    >
                      ✕
                    </button>
                  </div>

                  {renderSetupMiniRadar(s)}

                  {s.description && (
                    <p style={{ fontSize: '12px', color: '#94a3b8', lineHeight: 1.4 }}>
                      {s.description}
                    </p>
                  )}
                </div>
              )
            })
          )}
        </div>
      )}

      {/* Tab Content: 11 Playbook Protocols */}
      {activeTab === 'protocols' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {[
            { id: 1, title: 'Default Map Control (Базовый дефолт)', desc: 'Распределение 3-1-1 или 2-1-2 без спешки. Контроль таймингов поджима и сбор информации.' },
            { id: 2, title: 'Exec Protocols (Синхронные выходы)', desc: 'Тайминг одновременного падения гранат (0:52 / 0:38). Первый контакт открывает энтри с поддержкой моментальных флешек.' },
            { id: 3, title: 'Post-Plant Formations (Удержание плента)', desc: 'Отказ от открытых дуэлей в большинстве. Занятие взаимно прикрывающих кроссфайров и игра на затягивание времени дефьюза.' },
            { id: 4, title: 'Retake Protocols (Скоординированный ретейк)', desc: 'Ожидание полного сбора тиммейтов. Заход строго в 2–3 направления одновременно под отбрасываемые ретейк-флешки.' },
            { id: 5, title: 'Anti-Eco & Anti-Force (Защита от форсов)', desc: 'Держать дальние дистанции с винтовками, исключая ближний бой против пистолетов и шотганов.' },
            { id: 6, title: 'Mid-Round Rotations (Перетяжки)', desc: 'Условные сигналы IGL о фейках и быстрых сменах вектора атаки.' },
          ].map((item) => (
            <div
              key={item.id}
              style={{
                backgroundColor: '#0c1017',
                border: '1px solid #1a2233',
                borderRadius: '8px',
                padding: '14px 18px',
                display: 'flex',
                flexDirection: 'column',
                gap: '4px',
              }}
            >
              <span style={{ fontSize: '13px', fontWeight: 800, color: '#00f2fe' }}>
                {item.title}
              </span>
              <span style={{ fontSize: '12px', color: '#94a3b8', lineHeight: 1.4 }}>
                {item.desc}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Create Playbook Modal */}
      {createBookModalOpen && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 100,
            backgroundColor: 'rgba(0, 0, 0, 0.75)',
            backdropFilter: 'blur(6px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
          onClick={(e) => {
            if (e.target === e.currentTarget) setCreateBookModalOpen(false)
          }}
        >
          <div
            style={{
              backgroundColor: '#0c1017',
              border: '1px solid #facc15',
              borderRadius: '12px',
              padding: '20px',
              width: '380px',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px',
            }}
          >
            <span style={{ fontSize: '15px', fontWeight: 800, color: '#facc15' }}>
              📖 {lang === 'ru' ? 'Новый стратегический плейбук' : 'New Tactical Playbook'}
            </span>

            <div>
              <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>
                {lang === 'ru' ? 'Название плейбука' : 'Playbook Title'}
              </label>
              <input
                type="text"
                autoFocus
                value={newBookTitle}
                onChange={(e) => setNewBookTitle(e.target.value)}
                placeholder="de_mirage Default Protocols 2026..."
                style={{
                  width: '100%',
                  boxSizing: 'border-box',
                  backgroundColor: '#131926',
                  border: '1px solid #334155',
                  borderRadius: '6px',
                  padding: '7px 10px',
                  color: '#ffffff',
                  fontSize: '12px',
                  outline: 'none',
                }}
              />
            </div>

            <div>
              <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>
                {lang === 'ru' ? 'Команда / Состав' : 'Team / Roster'}
              </label>
              <input
                type="text"
                value={newBookTeam}
                onChange={(e) => setNewBookTeam(e.target.value)}
                placeholder="demToshka Squad..."
                style={{
                  width: '100%',
                  boxSizing: 'border-box',
                  backgroundColor: '#131926',
                  border: '1px solid #334155',
                  borderRadius: '6px',
                  padding: '7px 10px',
                  color: '#ffffff',
                  fontSize: '12px',
                  outline: 'none',
                }}
              />
            </div>

            <div>
              <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>
                {lang === 'ru' ? 'Карта соревновательного пула' : 'Competitive Map'}
              </label>
              <select
                value={newBookMap}
                onChange={(e) => setNewBookMap(e.target.value)}
                style={{
                  width: '100%',
                  boxSizing: 'border-box',
                  backgroundColor: '#131926',
                  border: '1px solid #334155',
                  borderRadius: '6px',
                  padding: '7px 10px',
                  color: '#ffffff',
                  fontSize: '12px',
                  outline: 'none',
                }}
              >
                {['de_mirage', 'de_inferno', 'de_nuke', 'de_anubis', 'de_ancient', 'de_dust2', 'de_vertigo'].map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '6px' }}>
              <button
                type="button"
                onClick={() => setCreateBookModalOpen(false)}
                style={{
                  padding: '6px 12px',
                  borderRadius: '6px',
                  backgroundColor: 'transparent',
                  border: '1px solid #334155',
                  color: '#94a3b8',
                  fontSize: '12px',
                  cursor: 'pointer',
                }}
              >
                {lang === 'ru' ? 'Отмена' : 'Cancel'}
              </button>
              <button
                type="button"
                onClick={handleCreateBook}
                disabled={!newBookTitle.trim()}
                style={{
                  padding: '6px 16px',
                  borderRadius: '6px',
                  backgroundColor: newBookTitle.trim() ? '#facc15' : '#475569',
                  border: 'none',
                  color: '#000000',
                  fontSize: '12px',
                  fontWeight: 800,
                  cursor: newBookTitle.trim() ? 'pointer' : 'not-allowed',
                }}
              >
                {lang === 'ru' ? 'Создать' : 'Create'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Setup Modal */}
      {createSetupModalOpen && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 100,
            backgroundColor: 'rgba(0, 0, 0, 0.75)',
            backdropFilter: 'blur(6px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
          onClick={(e) => {
            if (e.target === e.currentTarget) setCreateSetupModalOpen(false)
          }}
        >
          <div
            style={{
              backgroundColor: '#0c1017',
              border: '1px solid #00f2fe',
              borderRadius: '12px',
              padding: '20px',
              width: '380px',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px',
            }}
          >
            <span style={{ fontSize: '15px', fontWeight: 800, color: '#00f2fe' }}>
              🎯 {lang === 'ru' ? 'Новый тактический сетап' : 'Add Tactical Setup'}
            </span>

            <div>
              <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>
                {lang === 'ru' ? 'Название схемы' : 'Setup Title'}
              </label>
              <input
                type="text"
                autoFocus
                value={newSetupTitle}
                onChange={(e) => setNewSetupTitle(e.target.value)}
                placeholder="A Site Fast Execute / Split..."
                style={{
                  width: '100%',
                  boxSizing: 'border-box',
                  backgroundColor: '#131926',
                  border: '1px solid #334155',
                  borderRadius: '6px',
                  padding: '7px 10px',
                  color: '#ffffff',
                  fontSize: '12px',
                  outline: 'none',
                }}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
              <div>
                <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>
                  {lang === 'ru' ? 'Сторона' : 'Side'}
                </label>
                <select
                  value={newSetupSide}
                  onChange={(e) => setNewSetupSide(e.target.value)}
                  style={{
                    width: '100%',
                    boxSizing: 'border-box',
                    backgroundColor: '#131926',
                    border: '1px solid #334155',
                    borderRadius: '6px',
                    padding: '6px 8px',
                    color: '#ffffff',
                    fontSize: '12px',
                    outline: 'none',
                  }}
                >
                  <option value="t">T (Атака)</option>
                  <option value="ct">CT (Защита)</option>
                </select>
              </div>

              <div>
                <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>
                  {lang === 'ru' ? 'Фаза' : 'Phase'}
                </label>
                <select
                  value={newSetupPhase}
                  onChange={(e) => setNewSetupPhase(e.target.value)}
                  style={{
                    width: '100%',
                    boxSizing: 'border-box',
                    backgroundColor: '#131926',
                    border: '1px solid #334155',
                    borderRadius: '6px',
                    padding: '6px 8px',
                    color: '#ffffff',
                    fontSize: '12px',
                    outline: 'none',
                  }}
                >
                  <option value="default">Default</option>
                  <option value="execute">Execute</option>
                  <option value="post_plant">Post-Plant</option>
                  <option value="retake">Retake</option>
                  <option value="mid_round">Mid-Round</option>
                </select>
              </div>
            </div>

            <div>
              <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>
                {lang === 'ru' ? 'Описание тактики' : 'Description'}
              </label>
              <textarea
                value={newSetupDesc}
                onChange={(e) => setNewSetupDesc(e.target.value)}
                rows={3}
                placeholder="Распределение ролей, ключевые смоки и тайминги выхода..."
                style={{
                  width: '100%',
                  boxSizing: 'border-box',
                  backgroundColor: '#131926',
                  border: '1px solid #334155',
                  borderRadius: '6px',
                  padding: '6px 8px',
                  color: '#ffffff',
                  fontSize: '12px',
                  outline: 'none',
                  resize: 'none',
                }}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '6px' }}>
              <button
                type="button"
                onClick={() => setCreateSetupModalOpen(false)}
                style={{
                  padding: '6px 12px',
                  borderRadius: '6px',
                  backgroundColor: 'transparent',
                  border: '1px solid #334155',
                  color: '#94a3b8',
                  fontSize: '12px',
                  cursor: 'pointer',
                }}
              >
                {lang === 'ru' ? 'Отмена' : 'Cancel'}
              </button>
              <button
                type="button"
                onClick={handleCreateSetup}
                disabled={!newSetupTitle.trim()}
                style={{
                  padding: '6px 16px',
                  borderRadius: '6px',
                  backgroundColor: newSetupTitle.trim() ? '#00f2fe' : '#475569',
                  border: 'none',
                  color: '#000000',
                  fontSize: '12px',
                  fontWeight: 800,
                  cursor: newSetupTitle.trim() ? 'pointer' : 'not-allowed',
                }}
              >
                {lang === 'ru' ? 'Добавить' : 'Add'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
