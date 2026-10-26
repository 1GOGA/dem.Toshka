import { useEffect, useState } from 'react'
import { api } from './api'
import { CinematicShowcaseView } from './components/CinematicShowcaseView'
import { ClipSettingsModal } from './components/ClipSettingsModal'
import { ClipsMontageView } from './components/ClipsMontageView'
import { Header, type TabType } from './components/Header'
import { HighlightsStudioView } from './components/HighlightsStudioView'
import { LanguageSwitcher } from './components/LanguageSwitcher'
import { LibraryView } from './components/LibraryView'
import { MatchOverviewView } from './components/MatchOverviewView'
import { RenderQueueModal } from './components/RenderQueueModal'
import { Round2DReplayView } from './components/Round2DReplayView'
import { SettingsView } from './components/SettingsView'
import { ChartIcon, RadarIcon } from './components/Icons'
import { useTranslation } from './i18n'
import type {
  ClipSettings,
  DemoSummary,
  HighlightItem,
  KillDTO,
  MatchScoreboard,
  PlayerDTO,
  RenderJobDTO,
  RoundDTO,
} from './types'

export function App() {
  const { lang } = useTranslation()
  const [activeTab, setActiveTab] = useState<TabType>('showcase')
  const [demos, setDemos] = useState<DemoSummary[]>([])
  const [activeDemo, setActiveDemo] = useState<DemoSummary | null>(null)

  // Demo detail states
  const [highlights, setHighlights] = useState<HighlightItem[]>([])
  const [players, setPlayers] = useState<PlayerDTO[]>([])
  const [rounds, setRounds] = useState<RoundDTO[]>([])
  const [kills, setKills] = useState<KillDTO[]>([])
  const [stats, setStats] = useState<MatchScoreboard | null>(null)

  // Highlights Studio filter states
  const [activePlayerFilter, setActivePlayerFilter] = useState<string | null>(null)
  const [activeTypeFilter, setActiveTypeFilter] = useState<string | null>(null)
  const [activeRoundFilter, setActiveRoundFilter] = useState<number | null>(null)

  // Selection state (Must persist across filters & tab changes)
  const [selectedHighlightIds, setSelectedHighlightIds] = useState<Set<string>>(new Set())

  // Modal states
  const [isQueueOpen, setIsQueueOpen] = useState(false)
  const [isSettingsOpen, setIsSettingsOpen] = useState(false)

  // Settings
  const [clipSettings, setClipSettings] = useState<ClipSettings>({
    resolution: '1080p',
    aspectRatio: '16:9',
    fps: 60,
    preRollSeconds: 4.0,
    postRollSeconds: 2.5,
    perspective: 'attacker',
    xray: true,
    hudMode: 'full',
    customCrosshair: true,
    watermark: true,
    watermarkPosition: 'top_left',
    radarMode: 'player_focus',
    previewRecording: true,
  })

  // Loading & error
  const [isLoading, setIsLoading] = useState(false)
  const [parseError, setParseError] = useState<string | null>(null)

  // Load details when active demo changes
  const selectDemo = async (demo: DemoSummary) => {
    setActiveDemo(demo)
    setIsLoading(true)
    try {
      const [hlList, playerList, roundList, statData, killList] = await Promise.all([
        api.getHighlights(demo.id),
        api.getPlayers(demo.id),
        api.getRounds(demo.id),
        api.getStats(demo.id),
        api.getKills(demo.id).catch(() => []),
      ])
      setHighlights(hlList)
      setPlayers(playerList)
      setRounds(roundList)
      setStats(statData)
      setKills(killList || [])
      setActivePlayerFilter(null)
      setActiveTypeFilter(null)
      setActiveRoundFilter(null)
    } catch (e: any) {
      console.error('Failed to load demo details:', e)
    } finally {
      setIsLoading(false)
    }
  }

  // Refresh list of saved demos
  const refreshDemos = async () => {
    try {
      const list = await api.listDemos()
      setDemos(list)
      return list
    } catch (e: any) {
      console.error('Failed to load demos:', e)
      return []
    }
  }

  // Initial load: fetch saved demos
  useEffect(() => {
    let isMounted = true
    const init = async () => {
      const list = await refreshDemos()
      if (isMounted && list.length > 0) {
        selectDemo(list[0])
      }
    }
    init()
    return () => {
      isMounted = false
    }
  }, [])

  // Universal Tab Switcher with Smart Demo Auto-Selection
  const handleTabChange = (tab: TabType) => {
    // If navigating to studio, overview, or replay and no active demo is loaded yet,
    // automatically select the first demo if any exist
    if ((tab === 'studio' || tab === 'overview' || tab === 'replay') && !activeDemo && demos.length > 0) {
      selectDemo(demos[0])
    }
    setActiveTab(tab)
  }

  // Parse path
  const handleParsePath = async (path: string) => {
    setIsLoading(true)
    setParseError(null)
    try {
      const summary = await api.parseDemo(path)
      await refreshDemos()
      await selectDemo(summary)
      setActiveTab('studio') // Switch to Studio directly on new parse
    } catch (err: any) {
      setParseError(err?.message || 'Failed to parse demo')
    } finally {
      setIsLoading(false)
    }
  }

  // Upload and parse demo file
  const handleUploadDemo = async (file: File) => {
    setIsLoading(true)
    setParseError(null)
    try {
      const summary = await api.uploadDemo(file)
      await refreshDemos()
      await selectDemo(summary)
      setActiveTab('studio') // Switch to Studio directly on new parse
    } catch (err: any) {
      setParseError(err?.message || 'Failed to upload and parse demo')
    } finally {
      setIsLoading(false)
    }
  }

  // Highlight selection handlers
  const handleToggleHighlight = (id: string) => {
    setSelectedHighlightIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  const handleSelectAllFiltered = (ids: string[]) => {
    setSelectedHighlightIds((prev) => {
      const next = new Set(prev)
      ids.forEach((id) => next.add(id))
      return next
    })
  }

  const handleClearFiltered = (ids: string[]) => {
    setSelectedHighlightIds((prev) => {
      const next = new Set(prev)
      ids.forEach((id) => next.delete(id))
      return next
    })
  }

  const handleFilterPlayerHighlights = (steamId: string | null) => {
    setActivePlayerFilter(steamId)
    setActiveTypeFilter(null)
    setActiveRoundFilter(null)
    setActiveTab('studio')
  }

  const handleRenderSingle = (id: string) => {
    setSelectedHighlightIds(new Set([id]))
    setIsQueueOpen(true)
  }

  const handleSubmitRenderJobs = async (highlightIds: string[]): Promise<RenderJobDTO[]> => {
    if (!activeDemo) throw new Error('No active demo')
    return api.createRenderJobs({
      demo_id: activeDemo.id,
      highlight_ids: highlightIds,
      resolution: clipSettings.resolution,
      aspect_ratio: clipSettings.aspectRatio || '16:9',
      stretch_4_3: clipSettings.stretch43 || false,
      fps: clipSettings.fps,
      pre_roll_seconds: clipSettings.preRollSeconds,
      post_roll_seconds: clipSettings.postRollSeconds,
      perspective: clipSettings.perspective,
      perspective_steam_id: clipSettings.perspectiveSteamId,
      xray: clipSettings.xray,
      hud_mode: clipSettings.hudMode,
      hud_scale: clipSettings.hudScale,
      overhead_mode: clipSettings.overheadMode,
      killfeed_only: clipSettings.killfeedOnly,
      teamcounter_mode: clipSettings.teamcounterMode,
      custom_crosshair: clipSettings.customCrosshair,
      fov: clipSettings.fov,
      viewmodel_fov: clipSettings.viewmodelFov,
      crosshair_preset: clipSettings.crosshairPreset,
      crosshair_color: clipSettings.crosshairColor,
      radar_mode: clipSettings.radarMode || 'player_focus',
      watermark: clipSettings.watermark !== false,
      watermark_position: clipSettings.watermarkPosition || 'top_left',
      preview_recording: clipSettings.previewRecording !== false,
    })
  }

  // Map selected IDs to highlight items
  const selectedHighlights = highlights.filter((h) => selectedHighlightIds.has(h.id))

  return (
    <div className="app-root">
      <Header
        activeTab={activeTab}
        onTabChange={handleTabChange}
        selectedCount={selectedHighlightIds.size}
        onOpenQueue={() => setIsQueueOpen(true)}
        onOpenSettings={() => setIsSettingsOpen(true)}
        currentDemo={activeDemo}
      />

      <main style={{ minHeight: 'calc(100vh - 64px)', paddingBottom: activeTab === 'showcase' ? '0px' : '48px' }}>
        <div key={activeTab} className="scene-transition">
        {activeTab === 'showcase' && (
          <CinematicShowcaseView
            onOpenStudio={() => handleTabChange('library')}
            onOpenLibrary={() => handleTabChange('library')}
          />
        )}

        {/* 2. Highlights Studio: Flagship Workspace */}
        {activeTab === 'studio' && (
          <HighlightsStudioView
            highlights={highlights}
            players={players}
            selectedIds={selectedHighlightIds}
            onToggleHighlight={handleToggleHighlight}
            onSelectAllFiltered={handleSelectAllFiltered}
            onClearFiltered={handleClearFiltered}
            activePlayerFilter={activePlayerFilter}
            onSetPlayerFilter={setActivePlayerFilter}
            activeTypeFilter={activeTypeFilter}
            onSetTypeFilter={setActiveTypeFilter}
            activeRoundFilter={activeRoundFilter}
            onSetRoundFilter={setActiveRoundFilter}
            tickrate={activeDemo?.tickrate || 64}
            onRenderSingle={handleRenderSingle}
            onOpenQueue={() => setIsQueueOpen(true)}
            demos={demos}
            activeDemo={activeDemo}
            onSelectDemo={selectDemo}
            clipSettings={clipSettings}
            onUpdateSettings={setClipSettings}
            onSubmitRender={handleSubmitRenderJobs}
            kills={kills}
            demoRounds={rounds}
            onUploadDemo={handleUploadDemo}
            onParsePath={handleParsePath}
          />
        )}

        {/* 3. Library: Demos archive */}
        {activeTab === 'library' && (
          <LibraryView
            demos={demos}
            activeDemoId={activeDemo?.id ?? null}
            activeDemo={activeDemo}
            onSelectDemo={(demo) => {
              selectDemo(demo)
              setActiveTab('studio')
            }}
            onParsePath={handleParsePath}
            onUploadDemo={handleUploadDemo}
            isLoading={isLoading}
            error={parseError}
          />
        )}

        {/* 4. Match Overview & Analytics */}
        {activeTab === 'overview' && (
          activeDemo ? (
            <MatchOverviewView
              demo={activeDemo}
              stats={stats}
              rounds={rounds}
              isLoading={isLoading}
              onFilterPlayerHighlights={handleFilterPlayerHighlights}
            />
          ) : (
            <div className="empty-tab-container">
              <div className="empty-tab-icon">
                <ChartIcon size={38} color="#38bdf8" />
              </div>
              <h2 className="empty-tab-title">{lang === 'ru' ? 'Матч ещё не выбран' : 'No Match Selected'}</h2>
              <p className="empty-tab-desc">
                {lang === 'ru'
                  ? 'Для просмотра аналитики матча и таблицы счета выберите демку в Библиотеке или начните работу в Студии.'
                  : 'To view match analytics and scoreboard, select a demo from the Library or launch the Studio.'}
              </p>
              <div className="empty-tab-actions">
                <button type="button" className="btn btn-primary" onClick={() => handleTabChange('library')}>
                  📁 {lang === 'ru' ? 'Открыть Библиотеку' : 'Open Library'}
                </button>
                <button type="button" className="btn btn-secondary" onClick={() => handleTabChange('studio')}>
                  🎬 {lang === 'ru' ? 'В Студию Хайлайтов' : 'Launch Studio'}
                </button>
              </div>
            </div>
          )
        )}

        {/* 5. 2D Tactical Replay */}
        {activeTab === 'replay' && (
          activeDemo ? (
            <Round2DReplayView
              demo={activeDemo}
              rounds={rounds}
              highlights={highlights}
            />
          ) : (
            <div className="empty-tab-container">
              <div className="empty-tab-icon">
                <RadarIcon size={38} color="#10b981" />
              </div>
              <h2 className="empty-tab-title">{lang === 'ru' ? 'Тактический 2D Реплей' : 'Tactical 2D Replay'}</h2>
              <p className="empty-tab-desc">
                {lang === 'ru'
                  ? 'Для просмотра интерактивной 2D карты, перемещений игроков и таймеров гранат выберите матч в Библиотеке.'
                  : 'To inspect 2D radar, player paths, and smoke/fire timers, select a match from the Library.'}
              </p>
              <div className="empty-tab-actions">
                <button type="button" className="btn btn-primary" onClick={() => handleTabChange('library')}>
                  📁 {lang === 'ru' ? 'Открыть Библиотеку' : 'Open Library'}
                </button>
                <button type="button" className="btn btn-secondary" onClick={() => handleTabChange('studio')}>
                  🎬 {lang === 'ru' ? 'В Студию Хайлайтов' : 'Launch Studio'}
                </button>
              </div>
            </div>
          )
        )}

        {/* 6. Clips & Montage */}
        {activeTab === 'clips' && (
          <ClipsMontageView
            onOpenFolder={() => api.openOutputFolder()}
            currentDemoId={activeDemo?.id}
            currentMapName={activeDemo?.map_name}
          />
        )}

        {/* 7. Settings */}
        {activeTab === 'settings' && (
          <SettingsView />
        )}
        </div>
      </main>

      {/* Modals */}
      <ClipSettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        settings={clipSettings}
        onUpdateSettings={setClipSettings}
      />

      <RenderQueueModal
        isOpen={isQueueOpen}
        onClose={() => setIsQueueOpen(false)}
        selectedHighlights={selectedHighlights}
        onRemoveHighlight={(id) => handleToggleHighlight(id)}
        onClearAll={() => setSelectedHighlightIds(new Set())}
        settings={clipSettings}
        demoId={activeDemo?.id ?? null}
        onSubmitRender={handleSubmitRenderJobs}
        tickrate={activeDemo?.tickrate ?? 128}
      />

      {/* Floating Bottom-Right Language Switcher */}
      <LanguageSwitcher />
    </div>
  )
}

export default App
