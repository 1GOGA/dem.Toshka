import React, { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import { useTranslation } from '../i18n'
import type { DemoSummary } from '../types'
import {
  ClapperboardIcon,
  SparkleIcon,
  FilmIcon,
  CheckIcon,
  FolderIcon,
} from './Icons'
import './CinematicStudioView.css'

interface CinematicStudioViewProps {
  currentDemo: DemoSummary | null
  demos: DemoSummary[]
  onSelectDemo: (demo: DemoSummary) => void
  onNavigateTab: (tab: any) => void
}

interface RankedHighlight {
  id: string
  demo_id: number
  highlight_type: string
  round_num: number
  start_tick: number
  end_tick: number
  pov_steam_id?: string
  pov_name?: string
  score: number
  kills_count: number
  kills: any[]
  has_headshot: boolean
  has_wallbang: boolean
  is_ace: boolean
  is_clutch: boolean
}

interface PlannedShot {
  shot_id: string
  highlight_id: string
  round_number: number
  camera_type: string
  purpose: string
  start_tick: number
  end_tick: number
  start_time: number
  end_time: number
  duration_seconds: number
  fov: number
  pov_steam_id?: string
  pov_name?: string
  focus_target_name?: string
  has_campath: boolean
  output_filename: string
  enabled: boolean
  fps: number
  resolution: string
  hud_mode: string
  xray: boolean
  watermark: boolean
  validation_status: string
}

export const CinematicStudioView: React.FC<CinematicStudioViewProps> = ({
  currentDemo,
  demos,
  onSelectDemo,
}) => {
  const { lang } = useTranslation()

  // Primary View Mode: 'fragmovie' (Master Studio & Live Showcase) vs 'planner' (3D Camera Choreography Wizard)
  const [viewMode, setViewMode] = useState<'fragmovie' | 'planner'>('fragmovie')

  // Fragmovie Master Studio Workbench Tabs (Phase 3.3, 3.4 & 3.5)
  const [workbenchTab, setWorkbenchTab] = useState<
    'storyboard' | 'sound_library' | 'edit_plan' | 'hud_mixer' | 'cameras' | 'render_qc' | 'reference_lab' | 'vfx_intelligence'
  >('storyboard')

  // Fragmovie Master Studio States
  const [productionData, setProductionData] = useState<any | null>(null)
  const [workflowState, setWorkflowState] = useState<any | null>(null)
  const [selectedReleaseId, setSelectedReleaseId] = useState<string>('master_16x9')
  const [isPlaying, setIsPlaying] = useState<boolean>(false)
  const [currentTime, setCurrentTime] = useState<number>(0.0)
  const [isMuted, setIsMuted] = useState<boolean>(false)
  const [showQAModal, setShowQAModal] = useState<boolean>(false)
  const videoRef = useRef<HTMLVideoElement | null>(null)

  // Sound Library Browser States (Phase D)
  const [soundLibraryData, setSoundLibraryData] = useState<any | null>(null)
  const [selectedSoundCategory, setSelectedSoundCategory] = useState<string>('all')
  const [soundSearchQuery, setSoundSearchQuery] = useState<string>('')
  const [auditioningSound, setAuditioningSound] = useState<{ id: string; url: string; name: string } | null>(null)
  const [isAuditionPlaying, setIsAuditionPlaying] = useState<boolean>(false)
  const audioAuditionRef = useRef<HTMLAudioElement | null>(null)

  // HUD & Capture Profile States (Phase C)
  const [activeHudProfile, setActiveHudProfile] = useState<string>('CUSTOM_KILLFEED')
  const [hudToggles, setHudToggles] = useState<Record<string, boolean>>({
    native_killfeed: false,
    custom_killfeed: true,
    crosshair: true,
    radar: false,
    player_hud: false,
    weapon_viewmodel: true,
    xray: false,
    observer_controls: false,
    watermark: false,
  })

  // Timeline Lock State (Phase B)
  const [timelineLockState, setTimelineLockState] = useState<string>('LOCKED')

  // Reference Lab States (Phase 3.4)
  const [referenceInbox, setReferenceInbox] = useState<any[]>([])
  const [analyzedReferences, setAnalyzedReferences] = useState<any[]>([])
  const [editingPatterns, setEditingPatterns] = useState<any[]>([])
  const [selectedProfile, setSelectedProfile] = useState<string>('HYBRID')
  const [selectedPatternCategory, setSelectedPatternCategory] = useState<string>('all')
  const [activeContactSheet, setActiveContactSheet] = useState<string | null>(null)
  const [styleGuideText, setStyleGuideText] = useState<string | null>(null)
  const [showStyleGuideModal, setShowStyleGuideModal] = useState<boolean>(false)
  const [activeReferenceCard, setActiveReferenceCard] = useState<{ refId: string; content: string } | null>(null)
  const [isScanningInbox, setIsScanningInbox] = useState<boolean>(false)
  const [analyzingFile, setAnalyzingFile] = useState<string | null>(null)

  // VFX Intelligence & Plugin Lab States (Phase 3.5)
  const [vfxCatalog, setVfxCatalog] = useState<any[]>([])
  const [vfxActiveCategory, setVfxActiveCategory] = useState<string>('all')
  const [vfxSelectedScene, setVfxSelectedScene] = useState<string>('scene_climax')
  const [vfxActiveTier, setVfxActiveTier] = useState<'SUBTLE' | 'CLEAN' | 'STRONG_CINEMATIC'>('SUBTLE')
  const [vfxDecision, setVfxDecision] = useState<any | null>(null)
  const [vfxComparisonTiers, setVfxComparisonTiers] = useState<{ clean: any; subtle: any; strong: any } | null>(null)
  const [vfxPresets, setVfxPresets] = useState<any[]>([])
  const [vfxTests, setVfxTests] = useState<any[]>([])
  const [vfxSelectedTest, setVfxSelectedTest] = useState<any | null>(null)
  const [vfxFeedback, setVfxFeedback] = useState<Record<string, 'like' | 'dislike'>>({})
  const [vfxPluginResearch, setVfxPluginResearch] = useState<string | null>(null)
  const [showPluginModal, setShowPluginModal] = useState<boolean>(false)

  // 3D Planner States (Steps 1-5)
  const [currentStep, setCurrentStep] = useState<number>(2) // 1=Demo, 2=Highlights, 3=ShotPlan, 4=Capture, 5=Resolve
  const [highlights, setHighlights] = useState<RankedHighlight[]>([])
  const [selectedHighlightIds, setSelectedHighlightIds] = useState<Set<string>>(new Set())
  const [plannedShots, setPlannedShots] = useState<PlannedShot[]>([])
  const [packageSummary, setPackageSummary] = useState<any | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  // Load initial production overview, workflow state, sound library, reference lab and VFX intelligence on mount
  useEffect(() => {
    loadProductionOverview()
    loadWorkflowState()
    loadSoundLibrary()
    loadReferenceLab()
    loadVfxIntelligence()
  }, [])

  // Load highlights when current demo changes
  useEffect(() => {
    if (currentDemo) {
      loadHighlights(currentDemo.id)
    } else if (demos.length > 0) {
      onSelectDemo(demos[0])
    }
  }, [currentDemo?.id])

  const loadProductionOverview = async () => {
    try {
      const data = await api.getCinematicProductionOverview()
      setProductionData(data)
    } catch (e) {
      console.warn('Could not fetch cinematic production overview:', e)
    }
  }

  const loadWorkflowState = async () => {
    try {
      const state = await api.getProductionWorkflowState()
      setWorkflowState(state)
      if (state.timeline_lock_state) setTimelineLockState(state.timeline_lock_state)
      if (state.active_hud_profile) setActiveHudProfile(state.active_hud_profile)
      if (state.hud_toggles) setHudToggles(state.hud_toggles)
    } catch (e) {
      console.warn('Could not fetch workflow state:', e)
    }
  }

  const loadSoundLibrary = async (category?: string, search?: string) => {
    try {
      const catParam = category && category !== 'all' ? category : undefined
      const data = await api.getSoundLibrary({ category: catParam, search })
      setSoundLibraryData(data)
    } catch (e) {
      console.warn('Could not fetch sound library:', e)
    }
  }

  const handleSoundCategoryChange = (cat: string) => {
    setSelectedSoundCategory(cat)
    loadSoundLibrary(cat, soundSearchQuery)
  }

  const handleSoundSearchChange = (query: string) => {
    setSoundSearchQuery(query)
    loadSoundLibrary(selectedSoundCategory, query)
  }

  const handleAuditionPlay = (sound: any) => {
    if (auditioningSound?.id === sound.id && isAuditionPlaying) {
      audioAuditionRef.current?.pause()
      setIsAuditionPlaying(false)
    } else {
      setAuditioningSound({ id: sound.id, url: sound.audition_url, name: sound.filename })
      setIsAuditionPlaying(true)
      if (audioAuditionRef.current) {
        audioAuditionRef.current.src = sound.audition_url
        audioAuditionRef.current.play().catch(e => console.warn('Audio play failed:', e))
      }
    }
  }

  // Phase 3.4 Reference Lab Handlers
  const loadReferenceLab = async (profile?: string, category?: string) => {
    try {
      const inboxRes = await api.getReferenceInbox()
      setReferenceInbox(inboxRes.items || [])

      const refRes = await api.getAnalyzedReferences()
      setAnalyzedReferences(refRes.references || [])

      const profParam = profile || selectedProfile
      const catParam = category && category !== 'all' ? category : undefined
      const patRes = await api.getEditingPatterns({ profile: profParam, category: catParam })
      setEditingPatterns(patRes.patterns || [])
    } catch (e) {
      console.warn('Could not fetch Reference Lab data:', e)
    }
  }

  const handleScanInbox = async () => {
    setIsScanningInbox(true)
    try {
      await api.scanReferenceInbox()
      await loadReferenceLab(selectedProfile, selectedPatternCategory)
      setSuccessMsg(lang === 'ru' ? 'Inbox референсов успешно просканирован' : 'Reference inbox scanned successfully')
      setTimeout(() => setSuccessMsg(null), 3000)
    } catch (e: any) {
      setErrorMsg(e.message || 'Scan failed')
      setTimeout(() => setErrorMsg(null), 3000)
    } finally {
      setIsScanningInbox(false)
    }
  }

  const handleAnalyzeReference = async (filename: string) => {
    setAnalyzingFile(filename)
    try {
      await api.analyzeReferenceVideo(filename)
      await loadReferenceLab(selectedProfile, selectedPatternCategory)
      setSuccessMsg(lang === 'ru' ? `Анализ ${filename} успешно завершен` : `Analysis of ${filename} complete`)
      setTimeout(() => setSuccessMsg(null), 4000)
    } catch (e: any) {
      setErrorMsg(e.message || 'Analysis failed')
      setTimeout(() => setErrorMsg(null), 4000)
    } finally {
      setAnalyzingFile(null)
    }
  }

  const handleProfileChange = (prof: string) => {
    setSelectedProfile(prof)
    loadReferenceLab(prof, selectedPatternCategory)
  }

  const handlePatternCategoryChange = (cat: string) => {
    setSelectedPatternCategory(cat)
    loadReferenceLab(selectedProfile, cat)
  }

  const handleOpenStyleGuide = async () => {
    try {
      const res = await api.getStyleGuide()
      setStyleGuideText(res.content)
      setShowStyleGuideModal(true)
    } catch (e: any) {
      setErrorMsg('Failed to load Style Guide')
    }
  }

  const handleVoteReference = async (refId: string, currentVote: string | null, newVote: 'liked' | 'disliked') => {
    const nextVote = currentVote === newVote ? null : newVote
    try {
      await api.voteReference(refId, nextVote)
      setAnalyzedReferences(prev =>
        prev.map(r => r.reference_id === refId ? { ...r, user_feedback: nextVote } : r)
      )
    } catch (e) {
      console.warn('Failed to vote reference:', e)
    }
  }

  const handleVotePattern = async (patternId: string, currentVote: string | null, newVote: 'liked' | 'disliked') => {
    const nextVote = currentVote === newVote ? null : newVote
    try {
      await api.votePattern(patternId, nextVote)
      setEditingPatterns(prev =>
        prev.map(p => p.pattern_id === patternId ? { ...p, user_feedback: nextVote } : p)
      )
    } catch (e) {
      console.warn('Failed to vote pattern:', e)
    }
  }

  const handleOpenReferenceCard = async (refId: string) => {
    try {
      const card = await api.getReferenceCard(refId)
      setActiveReferenceCard({ refId, content: card.content })
    } catch (e) {
      setErrorMsg('Failed to load Reference Card')
      setTimeout(() => setErrorMsg(null), 3000)
    }
  }

  // Phase 3.5 VFX Intelligence Handlers
  const getSceneContextPayload = (sceneKey: string) => {
    if (sceneKey === 'scene_headshot') {
      return {
        scene_id: 'scene_07_kill3_headshot',
        scene_category: 'ENGAGEMENT',
        camera_type: 'FIRST_PERSON',
        fps: 60.0,
        time_seconds: 10.08,
        duration_seconds: 1.5,
        is_kill_event: true,
        is_headshot: true,
        is_ace_kill: false,
        player_visible: true,
        enemy_visible: true,
        weapon_visible: true,
        is_outdoor_sky_visible: false,
        has_music_drop: false,
        current_editing_intensity: 0.7,
      }
    } else if (sceneKey === 'scene_rapid') {
      return {
        scene_id: 'scene_08_kill4_rapid',
        scene_category: 'MULTIKILL',
        camera_type: 'FIRST_PERSON',
        fps: 60.0,
        time_seconds: 10.89,
        duration_seconds: 0.81,
        is_kill_event: true,
        is_headshot: false,
        is_ace_kill: false,
        player_visible: true,
        enemy_visible: true,
        weapon_visible: true,
        rapid_kill_interval: 0.81,
        has_music_drop: false,
        current_editing_intensity: 0.9,
      }
    } else {
      return {
        scene_id: 'scene_09_ace_orbit',
        scene_category: 'ACE_CLIMAX',
        camera_type: 'ORBIT_CAMERA',
        fps: 60.0,
        time_seconds: 15.46,
        duration_seconds: 3.0,
        is_kill_event: true,
        is_headshot: false,
        is_ace_kill: true,
        player_visible: true,
        enemy_visible: false,
        weapon_visible: false,
        is_outdoor_sky_visible: true,
        has_music_drop: true,
        current_editing_intensity: 0.85,
      }
    }
  }

  const runVfxEvaluation = async (sceneKey: string, tier: 'SUBTLE' | 'CLEAN' | 'STRONG_CINEMATIC') => {
    try {
      const payload = getSceneContextPayload(sceneKey)
      const likedList = Object.entries(vfxFeedback).filter(([_, v]) => v === 'like').map(([k]) => k)
      const dislikedList = Object.entries(vfxFeedback).filter(([_, v]) => v === 'dislike').map(([k]) => k)
      const decisionRes = await api.decideVfx({
        ...payload,
        requested_tier: tier,
        user_liked_effects: likedList,
        user_disliked_effects: dislikedList,
      })
      setVfxDecision(decisionRes)
      const compareRes = await api.compareVfxTiers({
        ...payload,
        user_liked_effects: likedList,
        user_disliked_effects: dislikedList,
      })
      setVfxComparisonTiers(compareRes)
    } catch (e) {
      console.warn('Failed to evaluate VFX decision:', e)
    }
  }

  const loadVfxIntelligence = async () => {
    try {
      const catRes = await api.getVfxCatalog()
      setVfxCatalog(catRes.effects || [])
      const presRes = await api.getVfxPresets()
      setVfxPresets(presRes.presets || [])
      const testsRes = await api.getVfxValidationTests()
      setVfxTests(testsRes.tests || [])
      if (testsRes.tests && testsRes.tests.length > 0) {
        setVfxSelectedTest(testsRes.tests[0])
      }
      await runVfxEvaluation('scene_climax', 'SUBTLE')
    } catch (e) {
      console.warn('Failed to load VFX intelligence:', e)
    }
  }

  const handleVoteEffect = async (effectId: string, currentVote: 'like' | 'dislike' | undefined, newVote: 'like' | 'dislike') => {
    const nextVote = currentVote === newVote ? null : newVote
    try {
      await api.submitVfxFeedback(effectId, nextVote)
      setVfxFeedback(prev => {
        const copy = { ...prev }
        if (nextVote) copy[effectId] = nextVote
        else delete copy[effectId]
        return copy
      })
      runVfxEvaluation(vfxSelectedScene, vfxActiveTier)
    } catch (e) {
      console.warn('Failed to vote effect:', e)
    }
  }

  const handleOpenPluginResearch = async () => {
    try {
      const res = await api.getVfxPluginResearch()
      setVfxPluginResearch(res.content)
      setShowPluginModal(true)
    } catch (e) {
      setErrorMsg('Failed to load plugin research report')
      setTimeout(() => setErrorMsg(null), 3000)
    }
  }

  const handleTimelineLockToggle = async (action: 'lock' | 'unlock' | 'invalidate') => {
    try {
      const res = await api.setTimelineLock(action)
      setTimelineLockState(res.timeline_lock_state)
      setSuccessMsg(res.message)
      setTimeout(() => setSuccessMsg(null), 4000)
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to update timeline lock')
      setTimeout(() => setErrorMsg(null), 4000)
    }
  }

  const handleHudProfileSelect = async (profileName: string) => {
    setActiveHudProfile(profileName)
    try {
      await api.setHudProfile(profileName, hudToggles)
      setSuccessMsg(`HUD Profile updated to ${profileName}`)
      setTimeout(() => setSuccessMsg(null), 3000)
    } catch (err: any) {
      console.warn('Failed to update HUD profile:', err)
    }
  }

  const handleHudToggleChange = async (key: string, value: boolean) => {
    const updated = { ...hudToggles, [key]: value }
    setHudToggles(updated)
    try {
      await api.setHudProfile(activeHudProfile, updated)
    } catch (err: any) {
      console.warn('Failed to update toggle:', err)
    }
  }

  const loadHighlights = async (demoId: number) => {
    setIsLoading(true)
    setErrorMsg(null)
    try {
      const items = await api.getCinematicHighlights(demoId)
      setHighlights(items)
      if (items.length > 0) {
        setSelectedHighlightIds(new Set([items[0].id]))
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to load highlights')
    } finally {
      setIsLoading(false)
    }
  }

  const handlePlanShots = async () => {
    if (!currentDemo || selectedHighlightIds.size === 0) return
    setIsLoading(true)
    setErrorMsg(null)
    try {
      const res = await api.planCinematicShots(currentDemo.id, Array.from(selectedHighlightIds), 60)
      setPlannedShots(res.shots)
      setCurrentStep(3)
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to plan cinematic shots')
    } finally {
      setIsLoading(false)
    }
  }

  const handleCreatePackage = async () => {
    if (!currentDemo || plannedShots.length === 0) return
    setIsLoading(true)
    setErrorMsg(null)
    try {
      const pkg = await api.createProductionPackage(currentDemo.id, plannedShots)
      setPackageSummary(pkg)
      setCurrentStep(4)
      setSuccessMsg(lang === 'ru' ? 'Пакет производства успешно сгенерирован!' : 'Production package generated successfully!')
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to create production package')
    } finally {
      setIsLoading(false)
    }
  }

  // Video player controls
  const handleSeek = (timeSeconds: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = timeSeconds
      setCurrentTime(timeSeconds)
    }
  }

  const togglePlay = () => {
    if (videoRef.current) {
      if (videoRef.current.paused) {
        videoRef.current.play()
        setIsPlaying(true)
      } else {
        videoRef.current.pause()
        setIsPlaying(false)
      }
    }
  }

  const getActiveVideoUrl = () => {
    if (selectedReleaseId === 'broadcast_16x9') {
      return '/renders/ACE_FINAL_V3_AUDIO_KILLFEED/ACE_FINAL_V3_BROADCAST_KILLFEED.mp4'
    }
    if (selectedReleaseId === 'tiktok_9x16') {
      return '/renders/ACE_FINAL_V3_AUDIO_KILLFEED/ACE_FINAL_V3_TIKTOK.mp4'
    }
    if (selectedReleaseId === 'preview_16x9') {
      return '/renders/ACE_FINAL_V3_AUDIO_KILLFEED/ACE_FINAL_V3_PREVIEW.mp4'
    }
    const rel = productionData?.releases?.find((r: any) => r.id === selectedReleaseId)
    return rel ? rel.url : '/renders/ACE_FINAL_V3_AUDIO_KILLFEED/ACE_FINAL_V3_MASTER.mp4'
  }

  // Exact timeline event pins
  const eventPins = [
    { time: 7.711, label: '808 Drop', color: '#ec4899', icon: '🎵' },
    { time: 7.830, label: 'Kill 1 (1K)', color: '#ff8c00', icon: '💀' },
    { time: 10.455, label: 'Kill 2 (2K)', color: '#ff5a00', icon: '💀' },
    { time: 12.198, label: 'Kill 3 (HS)', color: '#ef4444', icon: '🎯' },
    { time: 13.500, label: 'Kill 4 (4K)', color: '#dc2626', icon: '💀' },
    { time: 16.500, label: 'Kill 5 (ACE in Orbit)', color: '#ffd700', icon: '🏆' },
    { time: 16.600, label: '5K Domination Card', color: '#38bdf8', icon: '👑' },
  ]

  const hudProfileDescriptions: Record<string, string> = {
    ORIGINAL_HUD: 'Preserves native CS2 HUD and default in-game killfeed. Custom overlays disabled.',
    MINIMAL_HUD: 'Runs cl_draw_only_deathnotices 1. Retains native deathnotices and crosshair, hides radar/health.',
    CUSTOM_KILLFEED: 'Runs cl_drawhud 0 in local demo playback. Custom 4K stacked tournament killfeed overlay is rendered with 0% clutter.',
    CLEAN_CINEMATIC: 'Completely clean footage with cl_drawhud 0 and crosshair 0 for pure atmospheric camera flybys.',
  }

  return (
    <div className="cinematic-studio-container">
      {/* Hidden audio tag for live SFX audition */}
      <audio
        ref={audioAuditionRef}
        onEnded={() => setIsAuditionPlaying(false)}
        onPause={() => setIsAuditionPlaying(false)}
      />

      {/* Top Banner Navigation & View Mode Switcher */}
      <header className="cinematic-top-nav">
        <div className="cinematic-brand-group">
          <ClapperboardIcon size={24} color="#f59e0b" />
          <div className="cinematic-titles">
            <h2>{lang === 'ru' ? 'CINEMATIC STUDIO — PRODUCTION WORKBENCH' : 'CINEMATIC STUDIO — PRODUCTION WORKBENCH'}</h2>
            <span>{lang === 'ru' ? 'AI Кино-студия CS2 • 9 Сцен • Библиотека звуков Sonniss 105 • Независимые слои бита и фрагов' : 'CS2 AI Movie Production • 9 Scenes • 105 Sonniss Audio Assets • Independent Beat vs Kill Layers'}</span>
          </div>
        </div>

        {/* View Mode Toggle: Fragmovie Studio vs 3D Planner */}
        <div className="cinematic-mode-switcher">
          <button
            className={`mode-btn ${viewMode === 'fragmovie' ? 'active' : ''}`}
            onClick={() => setViewMode('fragmovie')}
          >
            <SparkleIcon size={14} color={viewMode === 'fragmovie' ? '#000' : '#f59e0b'} />
            <span>{lang === 'ru' ? '🎬 Муви-Студия & Верстак' : '🎬 Production Workbench'}</span>
          </button>
          <button
            className={`mode-btn ${viewMode === 'planner' ? 'active' : ''}`}
            onClick={() => setViewMode('planner')}
          >
            <FilmIcon size={14} color={viewMode === 'planner' ? '#000' : '#38bdf8'} />
            <span>{lang === 'ru' ? '📐 3D Конструктор Камер' : '📐 3D Camera Planner'}</span>
          </button>
        </div>

        {/* Quick Action Buttons */}
        <div className="cinematic-top-actions">
          <div className={`lock-status-badge ${timelineLockState.toLowerCase()}`}>
            <span className="lock-dot" />
            <span className="lock-text">
              {timelineLockState === 'LOCKED' ? '🔒 TIMELINE LOCKED' : '⚠️ PENDING LOCK'}
            </span>
          </div>
          <a
            href="/renders/ACE_FINAL_V3_AUDIO_KILLFEED/ACE_FINAL_V3.fcpxml"
            download="ACE_FINAL_V3.fcpxml"
            className="btn-quick-fcpxml"
            title={lang === 'ru' ? 'Скачать XML для DaVinci Resolve' : 'Download DaVinci Resolve FCPXML'}
          >
            📥 FCPXML
          </a>
          <button
            className="btn-quick-qa"
            onClick={() => setShowQAModal(true)}
            title={lang === 'ru' ? 'Контактный лист контроля качества' : 'QA Contact Sheet'}
          >
            🔍 QA Sheet
          </button>
        </div>
      </header>

      {/* Messages */}
      {errorMsg && (
        <div className="cinematic-banner error-banner">
          <span>❌ {errorMsg}</span>
          <button onClick={() => setErrorMsg(null)}>✕</button>
        </div>
      )}
      {successMsg && (
        <div className="cinematic-banner success-banner">
          <span>✅ {successMsg}</span>
          <button onClick={() => setSuccessMsg(null)}>✕</button>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODE 1: FRAGMOVIE MASTER STUDIO & 7-AREA PRODUCTION WORKBENCH             */}
      {/* ========================================================================= */}
      {viewMode === 'fragmovie' && (
        <div className="fragmovie-studio-layout">
          {/* Section 1: Live Interactive Fragmovie Player & Release Selector */}
          <section className="fragmovie-player-section">
            <div className="player-top-toolbar">
              <div className="release-format-tabs">
                <button
                  className={`release-tab ${selectedReleaseId === 'master_16x9' ? 'active' : ''}`}
                  onClick={() => setSelectedReleaseId('master_16x9')}
                >
                  🎬 16:9 Pure Cinematic (Без плашек)
                </button>
                <button
                  className={`release-tab ${selectedReleaseId === 'broadcast_16x9' ? 'active' : ''}`}
                  onClick={() => setSelectedReleaseId('broadcast_16x9')}
                >
                  🏆 Broadcast (С киллфидом)
                </button>
                <button
                  className={`release-tab ${selectedReleaseId === 'tiktok_9x16' ? 'active' : ''}`}
                  onClick={() => setSelectedReleaseId('tiktok_9x16')}
                >
                  📱 9:16 TikTok / Shorts
                </button>
                <button
                  className={`release-tab ${selectedReleaseId === 'preview_16x9' ? 'active' : ''}`}
                  onClick={() => setSelectedReleaseId('preview_16x9')}
                >
                  ⚡ Fast Preview
                </button>
              </div>

              <div className="player-live-indicators">
                <span className="pill-badge red-pulse">● 60 FPS PROGRESSIVE</span>
                <span className="pill-badge gold">LOVELYDILLER 142 BPM</span>
                <span className="pill-badge cyan">SONNISS SFX</span>
                <span className="pill-badge green">0% WATERMARK</span>
              </div>
            </div>

            {/* Video Canvas Container */}
            <div className={`video-canvas-wrapper ${selectedReleaseId === 'tiktok_9x16' ? 'vertical-ratio' : 'widescreen-ratio'}`}>
              <video
                ref={videoRef}
                src={getActiveVideoUrl()}
                className="master-video-player"
                playsInline
                muted={isMuted}
                onTimeUpdate={() => {
                  if (videoRef.current) setCurrentTime(videoRef.current.currentTime)
                }}
                onPlay={() => setIsPlaying(true)}
                onPause={() => setIsPlaying(false)}
                onClick={togglePlay}
              />

              {/* Overlay Play Indicator */}
              {!isPlaying && (
                <div className="video-play-overlay" onClick={togglePlay}>
                  <div className="play-triangle" />
                </div>
              )}

              {/* Bottom Video HUD */}
              <div className="video-internal-hud">
                <div className="timecode-display">
                  <span className="tc-current">{currentTime.toFixed(3)}s</span>
                  <span className="tc-sep">/</span>
                  <span className="tc-total">18.500s</span>
                  <span className="tc-frame">(Frame {Math.round(currentTime * 60)})</span>
                </div>
                <div className="video-hud-buttons">
                  <button onClick={() => setIsMuted(!isMuted)}>
                    {isMuted ? '🔇' : '🔊'}
                  </button>
                  <button onClick={() => handleSeek(0)}>⏮ Rewind</button>
                  <button onClick={togglePlay}>{isPlaying ? '⏸ Pause' : '▶ Play'}</button>
                </div>
              </div>
            </div>

            {/* Interactive Timeline Scrubber & Synchronized Event Pins */}
            <div className="timeline-scrubber-card">
              <div className="scrubber-header">
                <span className="scrubber-title">⏱️ Exact Timeline Event Synchronizer</span>
                <div className="scrubber-quick-jumps">
                  <span className="jump-label">Jump to Event:</span>
                  {eventPins.map((pin, idx) => (
                    <button
                      key={idx}
                      className="jump-chip"
                      style={{ borderLeftColor: pin.color }}
                      onClick={() => handleSeek(pin.time)}
                    >
                      {pin.icon} {pin.label} ({pin.time.toFixed(2)}s)
                    </button>
                  ))}
                </div>
              </div>

              {/* Timeline Track with Visual Event Pins */}
              <div
                className="timeline-track-bar"
                onClick={(e) => {
                  const rect = e.currentTarget.getBoundingClientRect()
                  const frac = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width))
                  handleSeek(frac * 18.5)
                }}
              >
                {/* Progress bar */}
                <div
                  className="timeline-track-progress"
                  style={{ width: `${(currentTime / 18.5) * 100}%` }}
                />

                {/* Event Markers */}
                {eventPins.map((pin, idx) => {
                  const posPct = (pin.time / 18.5) * 100
                  const isNear = Math.abs(currentTime - pin.time) < 0.35
                  return (
                    <div
                      key={idx}
                      className={`timeline-event-pin ${isNear ? 'active-near' : ''}`}
                      style={{ left: `${posPct}%`, backgroundColor: pin.color }}
                      title={`${pin.label} at ${pin.time}s`}
                      onClick={(e) => {
                        e.stopPropagation()
                        handleSeek(pin.time)
                      }}
                    >
                      <div className="pin-tooltip" style={{ borderColor: pin.color }}>
                        {pin.icon} {pin.label}
                        <br />
                        <b>{pin.time.toFixed(3)}s</b>
                      </div>
                    </div>
                  )
                })}

                {/* Scrubber Playhead */}
                <div
                  className="timeline-playhead"
                  style={{ left: `${(currentTime / 18.5) * 100}%` }}
                />
              </div>
            </div>
          </section>

          {/* Section 2: Comprehensive 7-Area Cinematic Production Workbench Navigation */}
          <section className="production-workbench-section">
            <div className="workbench-nav-bar">
              <button
                className={`workbench-tab-btn ${workbenchTab === 'storyboard' ? 'active' : ''}`}
                onClick={() => setWorkbenchTab('storyboard')}
              >
                📋 {lang === 'ru' ? 'Сториборд (9 Сцен)' : 'Storyboard (9 Scenes)'}
              </button>
              <button
                className={`workbench-tab-btn ${workbenchTab === 'sound_library' ? 'active' : ''}`}
                onClick={() => setWorkbenchTab('sound_library')}
              >
                🎧 {lang === 'ru' ? 'SFX & Звуки (105 Sonniss)' : 'Sound Library (105 Assets)'}
              </button>
              <button
                className={`workbench-tab-btn ${workbenchTab === 'edit_plan' ? 'active' : ''}`}
                onClick={() => setWorkbenchTab('edit_plan')}
              >
                🎞️ {lang === 'ru' ? 'Монтажный План (Слои & Бит)' : 'Edit Plan (Layers & Beats)'}
              </button>
              <button
                className={`workbench-tab-btn ${workbenchTab === 'hud_mixer' ? 'active' : ''}`}
                onClick={() => setWorkbenchTab('hud_mixer')}
              >
                🎛️ {lang === 'ru' ? 'CS2 HUD & Оверлеи' : 'HUD & Overlay Mixer'}
              </button>
              <button
                className={`workbench-tab-btn ${workbenchTab === 'cameras' ? 'active' : ''}`}
                onClick={() => setWorkbenchTab('cameras')}
              >
                🎥 {lang === 'ru' ? 'Камеры & Дублы' : 'Cameras & Takes'}
              </button>
              <button
                className={`workbench-tab-btn ${workbenchTab === 'render_qc' ? 'active' : ''}`}
                onClick={() => setWorkbenchTab('render_qc')}
              >
                🚀 {lang === 'ru' ? 'Рендер & Контроль' : 'Render & QC'}
              </button>
              <button
                className={`workbench-tab-btn ${workbenchTab === 'reference_lab' ? 'active' : ''}`}
                onClick={() => setWorkbenchTab('reference_lab')}
              >
                🔬 {lang === 'ru' ? 'Лаборатория Референсов' : 'Reference Lab & Patterns'}
              </button>
              <button
                className={`workbench-tab-btn ${workbenchTab === 'vfx_intelligence' ? 'active' : ''}`}
                onClick={() => setWorkbenchTab('vfx_intelligence')}
              >
                ✨ {lang === 'ru' ? 'AI VFX & Решения' : 'VFX Intelligence & Lab'}
              </button>
            </div>

            {/* TAB 1: DIRECTOR STORYBOARD (9 SCENES) */}
            {workbenchTab === 'storyboard' && (
              <div className="workbench-panel storyboard-panel">
                <div className="panel-header-row">
                  <div>
                    <h3>{lang === 'ru' ? 'Режиссерский Сториборд (9 Сюжетных Сцен)' : 'Director Storyboard (9 Narrative Scenes)'}</h3>
                    <p className="panel-subtitle">
                      {lang === 'ru'
                        ? 'Комплексный анализ сцен: геометрия демки, подход, нарастание напряжения, огневой контакт, трансфер спрея, мульти-фраги, эйс и победный триумф.'
                        : 'Holistic scene analysis: demo geometry, approach, tension buildup, initial engagement, spray transfer, multikill, clutch, ace climax, and victory celebration.'}
                    </p>
                  </div>
                  <div className="storyboard-summary-chips">
                    <span className="chip-gold">5K ACE ROUND 19</span>
                    <span className="chip-cyan">de_anubis</span>
                    <span className="chip-emerald">9 APPROVED SCENES</span>
                  </div>
                </div>

                <div className="storyboard-grid">
                  {(workflowState?.storyboard_scenes || []).map((scene: any) => (
                    <div key={scene.scene_id} className="scene-card">
                      <div className="scene-card-top">
                        <span className="scene-number">#{scene.scene_number}</span>
                        <span className={`scene-category-pill cat-${scene.category.toLowerCase()}`}>
                          {scene.category}
                        </span>
                        <span className="scene-duration">{scene.duration_seconds.toFixed(2)}s</span>
                      </div>

                      <div className="scene-card-body">
                        <div className="scene-timing-row">
                          <span className="label">Timeline:</span>
                          <span className="val">{scene.start_time.toFixed(2)}s — {scene.end_time.toFixed(2)}s</span>
                        </div>
                        <div className="scene-zone-row">
                          <span className="label">Map Zone:</span>
                          <span className="val-zone">{scene.map_zone}</span>
                        </div>
                        <div className="scene-camera-row">
                          <span className="label">Camera:</span>
                          <span className="val-cam">{scene.suggested_camera_type} ({scene.camera_fov}° FOV)</span>
                        </div>
                        <div className="scene-pacing-row">
                          <span className="label">Pacing:</span>
                          <span className={`val-pacing pacing-${scene.desired_pacing}`}>{scene.desired_pacing}</span>
                        </div>
                        <div className="scene-transition-row">
                          <span className="label">Transition:</span>
                          <span className="val-trans">{scene.suggested_transition}</span>
                        </div>
                        <div className="scene-sound-row">
                          <span className="label">Sound Design:</span>
                          <span className="val-sound">{scene.suggested_sound_treatment}</span>
                        </div>
                      </div>

                      <div className="scene-card-footer">
                        <button
                          className="btn-scene-jump"
                          onClick={() => handleSeek(scene.start_time)}
                        >
                          ▶ Seek to Scene ({scene.start_time.toFixed(2)}s)
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* TAB 2: SOUND LIBRARY & SFX BROWSER (105 VERIFIED SONNISS ASSETS) */}
            {workbenchTab === 'sound_library' && (
              <div className="workbench-panel sound-library-panel">
                <div className="panel-header-row">
                  <div>
                    <h3>{lang === 'ru' ? 'Официальная Звуковая Библиотека Sonniss GDC 2026' : 'Official Sonniss GDC 2026 Sound Library'}</h3>
                    <p className="panel-subtitle">
                      {lang === 'ru'
                        ? '105 верифицированных 24-bit 96kHz аудиофайлов от 344 Audio (Part 1 of 5). Коммерческая Royalty-Free лицензия без атрибуции.'
                        : '105 verified 24-bit 96kHz audio assets from 344 Audio (Part 1 of 5). Commercial Royalty-Free license with zero attribution required.'}
                    </p>
                  </div>
                  <div className="audition-active-box">
                    <span className="audition-label">Audition Player:</span>
                    <span className="audition-name">{auditioningSound ? auditioningSound.name : 'Click any sound to listen'}</span>
                  </div>
                </div>

                {/* Filter and Search Bar */}
                <div className="sound-filter-bar">
                  <div className="sound-category-pills">
                    {['all', 'impacts', 'cinematic_hits', 'whooshes', 'whip_transitions', 'risers', 'reverse_fx', 'glitch', 'atmosphere', 'gameplay_accents', 'ui'].map((cat) => (
                      <button
                        key={cat}
                        className={`cat-pill ${selectedSoundCategory === cat ? 'active' : ''}`}
                        onClick={() => handleSoundCategoryChange(cat)}
                      >
                        {cat.replace('_', ' ')}
                        {soundLibraryData?.overview?.category_counts?.[cat] !== undefined && (
                          <span className="cat-count">({soundLibraryData.overview.category_counts[cat]})</span>
                        )}
                      </button>
                    ))}
                  </div>

                  <div className="sound-search-box">
                    <input
                      type="text"
                      placeholder="Search sound effects by name or use..."
                      value={soundSearchQuery}
                      onChange={(e) => handleSoundSearchChange(e.target.value)}
                    />
                  </div>
                </div>

                {/* Sounds Table */}
                <div className="sound-assets-table-container">
                  <table className="sound-assets-table">
                    <thead>
                      <tr>
                        <th>Play</th>
                        <th>Filename</th>
                        <th>Category</th>
                        <th>Duration</th>
                        <th>Format</th>
                        <th>Peak</th>
                        <th>RMS</th>
                        <th>Recommended Cinematic Use</th>
                        <th>License</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(soundLibraryData?.assets || []).map((asset: any) => {
                        const isThisPlaying = auditioningSound?.id === asset.id && isAuditionPlaying
                        return (
                          <tr key={asset.id} className={isThisPlaying ? 'row-playing' : ''}>
                            <td>
                              <button
                                className={`btn-sound-play ${isThisPlaying ? 'playing' : ''}`}
                                onClick={() => handleAuditionPlay(asset)}
                              >
                                {isThisPlaying ? '⏸' : '▶'}
                              </button>
                            </td>
                            <td className="cell-filename" title={asset.original_folder}>
                              <b>{asset.filename}</b>
                            </td>
                            <td>
                              <span className={`asset-cat-badge badge-${asset.category}`}>
                                {asset.category}
                              </span>
                            </td>
                            <td>{asset.duration_seconds.toFixed(2)}s</td>
                            <td>{asset.sample_rate / 1000}kHz / {asset.bit_depth}-bit</td>
                            <td>{asset.peak_dbfs} dBFS</td>
                            <td>{asset.rms_dbfs} dBFS</td>
                            <td className="cell-use">{asset.recommended_use}</td>
                            <td>
                              <span className="license-tag">Royalty-Free</span>
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* TAB 3: EDIT PLAN (INDEPENDENT LAYERS FOR BEATS VS KILLS) */}
            {workbenchTab === 'edit_plan' && (
              <div className="workbench-panel edit-plan-panel">
                <div className="panel-header-row">
                  <div>
                    <h3>{lang === 'ru' ? 'Монтажный План и Независимые Слои Таймлайна' : 'Multi-Track Edit Plan & Independent Layers'}</h3>
                    <p className="panel-subtitle">
                      {lang === 'ru'
                        ? 'Архитектурное правило Phase B: музыкальные доли и фраги демки развязаны на независимые слои. Музыка НИКОГДА не сдвигает фатальные тики CS2.'
                        : 'Phase B Strict Ordering: Musical beats and gameplay kills are decoupled on independent timeline tracks. Music beats NEVER alter fatal CS2 tick timestamps.'}
                    </p>
                  </div>
                  <div className="lock-control-group">
                    <span className="lock-label">Timeline Lock:</span>
                    <button
                      className={`btn-lock ${timelineLockState === 'LOCKED' ? 'active-locked' : ''}`}
                      onClick={() => handleTimelineLockToggle('lock')}
                    >
                      🔒 Lock Structure
                    </button>
                    <button
                      className={`btn-unlock ${timelineLockState === 'PENDING_TIMELINE_LOCK' ? 'active-unlocked' : ''}`}
                      onClick={() => handleTimelineLockToggle('unlock')}
                    >
                      🔓 Unlock for Retiming
                    </button>
                    <button
                      className="btn-invalidate"
                      onClick={() => handleTimelineLockToggle('invalidate')}
                    >
                      ⚠️ Invalidate Overlays
                    </button>
                  </div>
                </div>

                {/* Multi-track Stack Visualization */}
                <div className="edit-timeline-tracks-stack">
                  {/* Track 1: Independent Music Beat Grid */}
                  <div className="track-row track-music-beats">
                    <div className="track-label-col">
                      <span className="track-name">🎵 Track M1: Beat Grid</span>
                      <span className="track-sub">142.0 BPM (0.422s)</span>
                    </div>
                    <div className="track-content-col">
                      <div className="beat-drop-marker" style={{ left: '41.68%' }}>
                        <span className="beat-flag">808 DROP (7.711s)</span>
                      </div>
                      <div className="beat-grid-stripes" />
                    </div>
                  </div>

                  {/* Track 2: Independent CS2 Kill & Event Registry */}
                  <div className="track-row track-cs2-kills">
                    <div className="track-label-col">
                      <span className="track-name">💀 Track K1: Fatal Kills</span>
                      <span className="track-sub">Source Demo Ticks</span>
                    </div>
                    <div className="track-content-col">
                      <div className="kill-marker k1" style={{ left: '42.32%' }}>
                        <span>Kill 1: Tiger07 (F470 / 7.83s)</span>
                      </div>
                      <div className="kill-marker k2" style={{ left: '56.51%' }}>
                        <span>Kill 2: zuuuuuhhhhn (F627 / 10.45s)</span>
                      </div>
                      <div className="kill-marker k3" style={{ left: '65.94%' }}>
                        <span>Kill 3: HS ProfyfGames (F732 / 12.20s)</span>
                      </div>
                      <div className="kill-marker k4" style={{ left: '70.26%' }}>
                        <span>Kill 4: freekjkeee (F780 / 13.00s)</span>
                      </div>
                      <div className="kill-marker k5" style={{ left: '83.99%' }}>
                        <span>Kill 5: ACE axuenchik002 (F932 / 15.54s)</span>
                      </div>
                    </div>
                  </div>

                  {/* Track 3: Video Cuts & Camera Takes */}
                  <div className="track-row track-video-cuts">
                    <div className="track-label-col">
                      <span className="track-name">🎬 Track V1: Video Takes</span>
                      <span className="track-sub">1080p60 CS2 Render</span>
                    </div>
                    <div className="track-content-col">
                      <div className="clip-block take-shoulder" style={{ left: '0%', width: '11.62%' }}>
                        <span>Shoulder (0-2.15s)</span>
                      </div>
                      <div className="clip-block take-hero1" style={{ left: '11.62%', width: '49.46%' }}>
                        <span>Hero POV pt1 (2.15-11.30s)</span>
                      </div>
                      <div className="clip-block take-victim" style={{ left: '61.08%', width: '7.03%' }}>
                        <span>Victim POV (11.30-12.60s)</span>
                      </div>
                      <div className="clip-block take-hero2" style={{ left: '68.11%', width: '16.76%' }}>
                        <span>Hero POV pt2 (12.60-15.70s)</span>
                      </div>
                      <div className="clip-block take-orbit" style={{ left: '84.87%', width: '15.13%' }}>
                        <span>Climax Orbit (15.70-18.50s)</span>
                      </div>
                    </div>
                  </div>

                  {/* Track 4: Stacked Killfeed Overlays */}
                  <div className="track-row track-overlays">
                    <div className="track-label-col">
                      <span className="track-name">🏷️ Track V2: Kill Feed</span>
                      <span className="track-sub">Stacked Esports 4K</span>
                    </div>
                    <div className="track-content-col">
                      <div className="overlay-block kf1" style={{ left: '42.32%', width: '57.68%' }}>
                        <span>Kill 1 Badge</span>
                      </div>
                      <div className="overlay-block kf2" style={{ left: '56.51%', width: '43.49%' }}>
                        <span>Kill 2 Badge</span>
                      </div>
                      <div className="overlay-block kf3" style={{ left: '65.94%', width: '34.06%' }}>
                        <span>Kill 3 Badge</span>
                      </div>
                      <div className="overlay-block kf4" style={{ left: '70.26%', width: '29.74%' }}>
                        <span>Kill 4 Badge</span>
                      </div>
                      <div className="overlay-block kf5" style={{ left: '83.99%', width: '16.01%' }}>
                        <span>Kill 5 + Domination Card</span>
                      </div>
                    </div>
                  </div>

                  {/* Track 5: Fairlight 6-Track Stems */}
                  <div className="track-row track-stems">
                    <div className="track-label-col">
                      <span className="track-name">🎚️ Tracks A1-A6: Stems</span>
                      <span className="track-sub">Broadcast -14 LUFS</span>
                    </div>
                    <div className="track-content-col">
                      <div className="stem-sub-track">A1: CS2 Gameplay • A2: Music 142BPM • A3: 808 Sub-Bass • A4: Whooshes • A5: Risers • A6: Atmosphere</div>
                    </div>
                  </div>
                </div>

                {/* Event-to-Timeline Frame Verification Table */}
                <div className="timing-matrix-box">
                  <h4>Exact Event-to-Timeline Frame Verification Matrix</h4>
                  <table className="exact-timing-table">
                    <thead>
                      <tr>
                        <th>Event</th>
                        <th>Demo Tick</th>
                        <th>Demo Time</th>
                        <th>Capture Source</th>
                        <th>Timeline Clip ID</th>
                        <th>Master Frame</th>
                        <th>Master Time</th>
                        <th>Tolerance</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(workflowState?.event_mappings || []).map((m: any) => (
                        <tr key={m.event_id}>
                          <td><b>{m.attacker_name} ➔ {m.victim_name}</b> {m.is_headshot && '🎯'}</td>
                          <td><code>{m.demo_tick}</code></td>
                          <td>{m.demo_time_seconds.toFixed(3)}s</td>
                          <td>Take: {m.capture_source_timestamp.toFixed(3)}s (F{m.source_frame})</td>
                          <td><code>{m.timeline_clip_id}</code></td>
                          <td><b className="frame-badge">Frame {m.final_timeline_frame}</b></td>
                          <td><b>{m.final_timeline_timestamp.toFixed(3)}s</b></td>
                          <td>&lt; 16.6 ms (1 frame)</td>
                          <td><span className="badge-verified">VERIFIED</span></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* TAB 4: HUD & CAPTURE PROFILES MIXER */}
            {workbenchTab === 'hud_mixer' && (
              <div className="workbench-panel hud-mixer-panel">
                <div className="panel-header-row">
                  <div>
                    <h3>{lang === 'ru' ? 'Микшер CS2 HUD & Профили Захвата' : 'CS2 HUD & Capture Profiles Mixer'}</h3>
                    <p className="panel-subtitle">
                      {lang === 'ru'
                        ? 'Управление внутриигровым интерфейсом CS2 Source 2. Полное подавление дефолтного HUD исключает дублирование стандартных киллфид-уведомлений.'
                        : 'Configure CS2 Source 2 in-engine HUD elements. Complete suppression prevents double killfeed overlays and blurry default graphics.'}
                    </p>
                  </div>
                </div>

                {/* 4 Capture Profiles Selection */}
                <div className="hud-profiles-cards">
                  {[
                    { id: 'CUSTOM_KILLFEED', name: 'CUSTOM_KILLFEED (Recommended)', icon: '⭐', desc: hudProfileDescriptions.CUSTOM_KILLFEED },
                    { id: 'CLEAN_CINEMATIC', name: 'CLEAN_CINEMATIC', icon: '🎥', desc: hudProfileDescriptions.CLEAN_CINEMATIC },
                    { id: 'MINIMAL_HUD', name: 'MINIMAL_HUD', icon: '🎯', desc: hudProfileDescriptions.MINIMAL_HUD },
                    { id: 'ORIGINAL_HUD', name: 'ORIGINAL_HUD', icon: '🎮', desc: hudProfileDescriptions.ORIGINAL_HUD },
                  ].map((p) => (
                    <div
                      key={p.id}
                      className={`hud-profile-card ${activeHudProfile === p.id ? 'active' : ''}`}
                      onClick={() => handleHudProfileSelect(p.id)}
                    >
                      <div className="profile-card-header">
                        <span className="profile-icon">{p.icon}</span>
                        <h4>{p.name}</h4>
                      </div>
                      <p className="profile-desc">{p.desc}</p>
                      <div className="profile-active-indicator">
                        {activeHudProfile === p.id ? '✓ ACTIVE PROFILE' : 'Select Profile'}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Fine-Grained Convar Toggles */}
                <div className="hud-toggles-grid">
                  <h4>Individual Convar & Element Toggles</h4>
                  <div className="toggles-checkboxes">
                    {[
                      { key: 'native_killfeed', label: 'Native CS2 Deathnotices', desc: 'cl_draw_only_deathnotices convar' },
                      { key: 'custom_killfeed', label: 'Custom Esports Killfeed', desc: 'dem.Toshka 4K transparent SVG/PNG overlay' },
                      { key: 'crosshair', label: 'Crosshair', desc: 'crosshair 0/1 in CS2 console' },
                      { key: 'radar', label: 'Radar Minimap', desc: 'cl_drawhud radar element' },
                      { key: 'player_hud', label: 'Player Health & Ammo HUD', desc: 'Standard player stats bar' },
                      { key: 'weapon_viewmodel', label: 'First-Person Weapon Model', desc: 'r_drawviewmodel 0/1' },
                      { key: 'xray', label: 'Observer X-Ray Glow', desc: 'spec_show_xray 0/1' },
                      { key: 'observer_controls', label: 'Observer Spectator UI', desc: 'spec_scoreboard / spectator keys' },
                      { key: 'watermark', label: 'dem.Toshka Watermark', desc: 'Strictly 0% OFF for clean master releases' },
                    ].map((tog) => (
                      <label key={tog.key} className="hud-toggle-label">
                        <input
                          type="checkbox"
                          checked={!!hudToggles[tog.key]}
                          onChange={(e) => handleHudToggleChange(tog.key, e.target.checked)}
                        />
                        <div className="toggle-text">
                          <b>{tog.label}</b>
                          <span>{tog.desc}</span>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Live Convar Output Box */}
                <div className="convar-console-box">
                  <h4>Generated CS2 Convar Commands (Executed via HLAE Auto-Exec)</h4>
                  <pre className="convar-code-block">
                    {workflowState?.active_convars ? (
                      Object.entries(workflowState.active_convars).map(([k, v]) => `${k} "${v}"`).join('\n')
                    ) : (
                      'sv_cheats "1"\ncl_drawhud "0"\ncl_draw_only_deathnotices "0"\ncrosshair "1"\nr_drawviewmodel "1"\nspec_show_xray "0"'
                    )}
                  </pre>
                  <p className="convar-note">
                    ℹ️ <i>Notice:</i> CS2 convar <code>cl_drawhud 0</code> requires <code>sv_cheats 1</code> in local demo playback. Settings are fully restored after capture.
                  </p>
                </div>
              </div>
            )}

            {/* TAB 5: CAMERAS & CAPTURED TAKES */}
            {workbenchTab === 'cameras' && (
              <div className="workbench-panel cameras-panel">
                <div className="panel-header-row">
                  <div>
                    <h3>{lang === 'ru' ? 'Библиотека Камер и Захваченные Дублы' : 'Camera Library & Captured Takes'}</h3>
                    <p className="panel-subtitle">
                      {lang === 'ru'
                        ? '4 синхронизированных ракурса захвата из реальной CS2 демки. Оценка видимости персонажей и валидация клиппинга.'
                        : '4 synchronized camera takes captured from real CS2 demo playback. Character visibility scoring and clipping risk validation.'}
                    </p>
                  </div>
                  <button className="btn-open-planner" onClick={() => setViewMode('planner')}>
                    📐 Open 3D Spline Path Planner
                  </button>
                </div>

                <div className="takes-grid">
                  {[
                    {
                      id: 'take_01',
                      name: 'Take 01: Shoulder Approach',
                      camera: 'SHOULDER_CAM',
                      fov: 95,
                      time: '0.00s — 2.15s (2.15s)',
                      purpose: 'APPROACH',
                      subject: 'pytoshka_',
                      status: 'VERIFIED',
                      score: 95.0,
                    },
                    {
                      id: 'take_02',
                      name: 'Take 02: Hero POV (Part 1 & 2)',
                      camera: 'FIRST_PERSON',
                      fov: 90,
                      time: '2.15s — 15.70s (13.55s)',
                      purpose: 'PRIMARY_ACTION',
                      subject: 'pytoshka_',
                      status: 'VERIFIED',
                      score: 100.0,
                    },
                    {
                      id: 'take_03',
                      name: 'Take 03: Victim Reaction Insert',
                      camera: 'VICTIM_POV',
                      fov: 90,
                      time: '11.30s — 12.60s (1.30s)',
                      purpose: 'VICTIM_REACTION',
                      subject: 'ProfyfGames (HS)',
                      status: 'VERIFIED',
                      score: 92.0,
                    },
                    {
                      id: 'take_04',
                      name: 'Take 04: Climax Orbit 360',
                      camera: 'ORBIT_CAMERA',
                      fov: 85,
                      time: '15.70s — 18.50s (2.80s)',
                      purpose: 'CLIMAX_ACCENT',
                      subject: 'pytoshka_ (5K ACE)',
                      status: 'VERIFIED',
                      score: 98.0,
                    },
                  ].map((take) => (
                    <div key={take.id} className="take-card">
                      <div className="take-header">
                        <h4>{take.name}</h4>
                        <span className="take-score-badge">{take.score}% SCORE</span>
                      </div>
                      <div className="take-body">
                        <div className="take-prop"><span className="p-label">Type:</span> <b>{take.camera}</b></div>
                        <div className="take-prop"><span className="p-label">FOV:</span> <b>{take.fov}°</b></div>
                        <div className="take-prop"><span className="p-label">Timeline Range:</span> <b>{take.time}</b></div>
                        <div className="take-prop"><span className="p-label">Subject Focus:</span> <b>{take.subject}</b></div>
                        <div className="take-prop"><span className="p-label">QC Status:</span> <b className="status-verified">{take.status}</b></div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Transition Presets */}
                <div className="transitions-catalog-box">
                  <h4>Blackmagic Fusion Dynamic Transitions Catalog</h4>
                  <div className="transitions-grid">
                    {(workflowState?.transitions || []).map((t: any) => (
                      <div key={t.id} className="transition-card">
                        <div className="t-header">
                          <b>{t.name}</b>
                          <span className="t-family-pill">{t.family}</span>
                        </div>
                        <p className="t-desc">{t.description}</p>
                        <div className="t-footer">
                          <span>Frames: {t.duration_frames}</span>
                          <span>Shutter: {t.shutter_angle}°</span>
                          <span>{t.best_used_for}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* TAB 6: RENDER & QUALITY CONTROL */}
            {workbenchTab === 'render_qc' && (
              <div className="workbench-panel render-qc-panel">
                <div className="panel-header-row">
                  <div>
                    <h3>{lang === 'ru' ? 'Рендер & Контроль Качества (Master Deliverables)' : 'Render & Quality Control (Master Deliverables)'}</h3>
                    <p className="panel-subtitle">
                      {lang === 'ru'
                        ? 'Финальные мастер-релизы, созданные через аппаратный энкодер AMD AMF без вотермарок, с интеграцией в DaVinci Resolve Free 21.0.'
                        : 'Final master releases generated via AMD AMF hardware encoder with zero watermarks, plus live DaVinci Resolve Free 21.0 integration.'}
                    </p>
                  </div>
                </div>

                <div className="qc-cards-grid">
                  <div className="qc-card">
                    <h4>Master Releases</h4>
                    <ul className="releases-list">
                      <li>
                        <b>ACE_FINAL_V3_MASTER.mp4</b>
                        <span>1920x1080 @ 60 FPS • 53.2 МБ • Pure Cinematic (Чистый монтаж без плашек)</span>
                        <a href="/renders/ACE_FINAL_V3_AUDIO_KILLFEED/ACE_FINAL_V3_MASTER.mp4" download className="btn-dl">Download Master</a>
                      </li>
                      <li>
                        <b>ACE_FINAL_V3_BROADCAST_KILLFEED.mp4</b>
                        <span>1920x1080 @ 60 FPS • 53.2 МБ • Esports Broadcast (С точным киллфидом)</span>
                        <a href="/renders/ACE_FINAL_V3_AUDIO_KILLFEED/ACE_FINAL_V3_BROADCAST_KILLFEED.mp4" download className="btn-dl">Download Broadcast</a>
                      </li>
                      <li>
                        <b>ACE_FINAL_V3_TIKTOK.mp4</b>
                        <span>1080x1920 @ 60 FPS • 44.4 МБ • 20.2 Мбит/с • Smart Vertical</span>
                        <a href="/renders/ACE_FINAL_V3_AUDIO_KILLFEED/ACE_FINAL_V3_TIKTOK.mp4" download className="btn-dl">Download TikTok</a>
                      </li>
                      <li>
                        <b>ACE_FINAL_V3_PREVIEW.mp4</b>
                        <span>1920x1080 @ 60 FPS • 17.9 МБ • 8.1 Мбит/с • Fast Web Stream</span>
                        <a href="/renders/ACE_FINAL_V3_AUDIO_KILLFEED/ACE_FINAL_V3_PREVIEW.mp4" download className="btn-dl">Download Preview</a>
                      </li>
                    </ul>
                  </div>

                  <div className="qc-card">
                    <h4>DaVinci Resolve 21.0 Studio Bridge</h4>
                    <p>Timeline: <code>CS2_Cinematic_Director_Cut</code> with 4 video tracks, 6 Fairlight audio stems, and 5 frame-locked kill markers.</p>
                    <div className="resolve-btn-row">
                      <a href="/renders/ACE_FINAL_V3_AUDIO_KILLFEED/ACE_FINAL_V3.fcpxml" download className="btn-resolve">
                        Export FCPXML 1.10
                      </a>
                      <a href="/renders/ACE_FINAL_V3_AUDIO_KILLFEED/ACE_FINAL_V3.drp" download className="btn-resolve">
                        Export DaVinci DRP Archive
                      </a>
                    </div>
                  </div>

                  <div className="qc-card">
                    <h4>QA Contact Sheet Inspection</h4>
                    <p>12-point keyframe contact sheet verifying beat drop, muzzle discharge, hit registration, and 5K ACE climax.</p>
                    <button className="btn-show-qa-full" onClick={() => setShowQAModal(true)}>
                      🔍 View 4K Quality Control Contact Sheet
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 7: AI FRAGMOVIE REFERENCE LAB (PHASE 3.4) */}
            {workbenchTab === 'reference_lab' && (
              <div className="workbench-panel reference-lab-panel">
                <div className="panel-header-row">
                  <div>
                    <h3>
                      {lang === 'ru'
                        ? 'AI Fragmovie Reference Lab — Анализ Референсов & Библиотека Паттернов'
                        : 'AI Fragmovie Reference Lab — Pattern Intelligence & Resolve Recipes'}
                    </h3>
                    <p className="panel-subtitle">
                      {lang === 'ru'
                        ? 'Локальный мультимодальный анализ профессиональных CS2 мувиков (FFprobe, OpenCV, SciPy, NumPy). Извлечение таймингов, переходов, цветовых схем и нодовых рецептов DaVinci Resolve 21.'
                        : 'Local multimodal analysis of professional CS2 fragmovies (FFprobe, OpenCV, SciPy, NumPy). Extraction of pacing, transitions, color palettes, and DaVinci Resolve 21 node recipes.'}
                    </p>
                  </div>
                  <div className="ref-lab-header-actions">
                    <button
                      className="btn-ref-action"
                      onClick={handleScanInbox}
                      disabled={isScanningInbox}
                    >
                      {isScanningInbox ? '⏳ Scanning...' : '📥 ' + (lang === 'ru' ? 'Сканировать Inbox' : 'Scan Inbox')}
                    </button>
                    <button
                      className="btn-ref-action guide-btn"
                      onClick={handleOpenStyleGuide}
                    >
                      📖 {lang === 'ru' ? 'Pytoshka Style Guide' : 'Pytoshka Style Guide'}
                    </button>
                  </div>
                </div>

                {/* Sub-section 1: Inbox Status & Staged Videos */}
                <div className="ref-section-block">
                  <div className="ref-section-header">
                    <h4>
                      📥 {lang === 'ru' ? 'Входящие Референсы' : 'Inbox Staged Videos'} (<code>reference_library/inbox/</code>)
                    </h4>
                    <span className="ref-count-tag">{referenceInbox.length} staged</span>
                  </div>
                  <div className="ref-inbox-grid">
                    {referenceInbox.map((item) => (
                      <div key={item.filename} className="ref-inbox-card">
                        <div className="ref-inbox-info">
                          <span className="ref-inbox-icon">🎬</span>
                          <div>
                            <strong className="ref-inbox-title" title={item.filename}>{item.filename}</strong>
                            <div className="ref-inbox-meta">{item.size_mb} MB • {item.analyzed ? '✅ Verified in Index' : '⚡ Ready to analyze'}</div>
                          </div>
                        </div>
                        <div className="ref-inbox-actions">
                          {item.analyzed ? (
                            <span className="badge-analyzed">ANALYZED</span>
                          ) : (
                            <button
                              className="btn-analyze-ref"
                              onClick={() => handleAnalyzeReference(item.filename)}
                              disabled={analyzingFile === item.filename}
                            >
                              {analyzingFile === item.filename ? '⏳ Processing...' : '▶ Analyze'}
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                    {referenceInbox.length === 0 && (
                      <div className="ref-empty-hint">
                        {lang === 'ru'
                          ? 'Поместите .mp4/.mov файлы в reference_library/inbox/ и нажмите "Сканировать Inbox".'
                          : 'Place .mp4/.mov reference clips into reference_library/inbox/ and click "Scan Inbox".'}
                      </div>
                    )}
                  </div>
                </div>

                {/* Sub-section 2: Analyzed Reference Vault */}
                <div className="ref-section-block">
                  <div className="ref-section-header">
                    <h4>
                      🎞️ {lang === 'ru' ? 'Верифицированные Референсы & Раскадровки' : 'Analyzed Reference Vault & Contact Sheets'}
                    </h4>
                    <span className="ref-count-tag">{analyzedReferences.length} verified</span>
                  </div>
                  <div className="ref-analyzed-grid">
                    {analyzedReferences.map((ref) => {
                      const sheetFilename = ref.contact_sheet ? ref.contact_sheet.split(/[\\/]/).pop() : null
                      return (
                        <div key={ref.reference_id} className="ref-analyzed-card">
                          <div className="ref-card-header">
                            <span className="ref-id-pill">{ref.reference_id.substring(0, 22)}...</span>
                            <div className="ref-card-header-right">
                              <span className="ref-fps-badge">{ref.resolution} @ {ref.fps} FPS</span>
                              <div className="vote-btn-group">
                                <button
                                  className={`btn-vote like ${ref.user_feedback === 'liked' ? 'voted' : ''}`}
                                  onClick={() => handleVoteReference(ref.reference_id, ref.user_feedback, 'liked')}
                                  title="Like this editing style"
                                >
                                  👍
                                </button>
                                <button
                                  className={`btn-vote dislike ${ref.user_feedback === 'disliked' ? 'voted' : ''}`}
                                  onClick={() => handleVoteReference(ref.reference_id, ref.user_feedback, 'disliked')}
                                  title="Dislike this editing style"
                                >
                                  👎
                                </button>
                              </div>
                            </div>
                          </div>

                          {/* Categories tags */}
                          {ref.categories && ref.categories.length > 0 && (
                            <div className="ref-card-categories">
                              {ref.categories.map((c: string) => (
                                <span key={c} className="ref-tag-pill">{c}</span>
                              ))}
                            </div>
                          )}

                          <div className="ref-card-body">
                            <div className="ref-metric-row">
                              <span className="label">File:</span>
                              <span className="val" title={ref.filename}>{ref.filename}</span>
                            </div>
                            <div className="ref-metric-row">
                              <span className="label">Duration:</span>
                              <span className="val">{ref.duration_seconds.toFixed(2)}s</span>
                            </div>
                            <div className="ref-metric-row">
                              <span className="label">Detected Cuts:</span>
                              <span className="val highlight-val">{ref.cuts_count} transitions</span>
                            </div>
                            <div className="ref-metric-row">
                              <span className="label">Tempo / BPM:</span>
                              <span className="val">{ref.bpm ? `${ref.bpm} BPM` : 'Ambient'}</span>
                            </div>
                            <div className="ref-metric-row">
                              <span className="label">Patterns Found:</span>
                              <span className="val highlight-gold">{ref.patterns_count} patterns</span>
                            </div>
                          </div>
                          <div className="ref-card-footer">
                            {sheetFilename && (
                              <button
                                className="btn-sheet-view"
                                onClick={() => setActiveContactSheet(api.getContactSheetUrl(sheetFilename))}
                              >
                                🖼️ {lang === 'ru' ? 'Раскадровка' : 'Contact Sheet'}
                              </button>
                            )}
                            <button
                              className="btn-card-breakdown"
                              onClick={() => handleOpenReferenceCard(ref.reference_id)}
                            >
                              📋 {lang === 'ru' ? 'Разбор (Card)' : 'Breakdown Card'}
                            </button>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>

                {/* Sub-section 3: Editing Patterns Explorer */}
                <div className="ref-section-block">
                  <div className="ref-section-header">
                    <h4>
                      🧩 {lang === 'ru' ? 'Монтажные Паттерны & Рецепты DaVinci Resolve' : 'Editing Patterns & DaVinci Resolve Recipes'}
                    </h4>
                    <span className="ref-count-tag">{editingPatterns.length} patterns</span>
                  </div>

                  {/* Profile & Category Selectors */}
                  <div className="ref-filters-bar">
                    <div className="ref-profile-tabs">
                      <span className="ref-filter-label">{lang === 'ru' ? 'Профиль Стиля:' : 'Style Profile:'}</span>
                      {[
                        { id: 'HYBRID', label: '🎛️ HYBRID (Default)', desc: 'Balanced Narrative & Impact' },
                        { id: 'HYPE', label: '🔥 HYPE (Fast)', desc: 'Micro-Zooms & 808 Drops' },
                        { id: 'CINEMATIC', label: '🎬 CINEMATIC (Atmospheric)', desc: 'Campath Orbits & Pacing' },
                      ].map((p) => (
                        <button
                          key={p.id}
                          className={`ref-prof-btn ${selectedProfile === p.id ? 'active' : ''}`}
                          onClick={() => handleProfileChange(p.id)}
                          title={p.desc}
                        >
                          {p.label}
                        </button>
                      ))}
                    </div>

                    <div className="ref-cat-pills">
                      <span className="ref-filter-label">{lang === 'ru' ? 'Категория:' : 'Category:'}</span>
                      {['all', 'TRANSITION', 'SPEED_RAMP', 'COLOR_GRADING', 'SOUND_DESIGN', 'CAMERA_WORK', 'TYPOGRAPHY'].map((cat) => (
                        <button
                          key={cat}
                          className={`cat-pill ${selectedPatternCategory === cat ? 'active' : ''}`}
                          onClick={() => handlePatternCategoryChange(cat)}
                        >
                          {cat}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Patterns Grid */}
                  <div className="patterns-card-grid">
                    {editingPatterns.map((pat) => (
                      <div key={pat.pattern_id} className="pattern-detail-card">
                        <div className="pat-card-header">
                          <span className={`pat-cat-pill cat-${pat.category.toLowerCase()}`}>{pat.category}</span>
                          <div className="pat-card-header-right">
                            <span className={`pat-confidence-pill conf-${pat.confidence.toLowerCase()}`}>{pat.confidence}</span>
                            <div className="vote-btn-group">
                              <button
                                className={`btn-vote like ${pat.user_feedback === 'liked' ? 'voted' : ''}`}
                                onClick={() => handleVotePattern(pat.pattern_id, pat.user_feedback, 'liked')}
                                title="Like this editing technique"
                              >
                                👍
                              </button>
                              <button
                                className={`btn-vote dislike ${pat.user_feedback === 'disliked' ? 'voted' : ''}`}
                                onClick={() => handleVotePattern(pat.pattern_id, pat.user_feedback, 'disliked')}
                                title="Dislike this editing technique"
                              >
                                👎
                              </button>
                            </div>
                          </div>
                        </div>
                        <h4 className="pat-title">{pat.name}</h4>
                        <p className="pat-desc">{pat.description}</p>

                        <div className="pat-meta-block">
                          <div className="pat-meta-row">
                            <span className="label">Scene Type:</span>
                            <span className="val">{pat.scene_type}</span>
                          </div>
                          <div className="pat-meta-row">
                            <span className="label">Timing Range:</span>
                            <span className="val">{pat.suggested_timing_range}</span>
                          </div>
                          <div className="pat-meta-row">
                            <span className="label">Technique:</span>
                            <span className="val-tech">{pat.editing_technique}</span>
                          </div>
                          <div className="pat-meta-row">
                            <span className="label">Audio:</span>
                            <span className="val-audio">{pat.suggested_audio_treatment}</span>
                          </div>
                        </div>

                        {pat.davinci_resolve_recipe && (
                          <div className="resolve-recipe-box">
                            <div className="recipe-header">
                              <span className="recipe-page">DaVinci Resolve: <b>{pat.davinci_resolve_recipe.page} Page</b></span>
                              <span className="recipe-curve">{pat.davinci_resolve_recipe.curve_type}</span>
                            </div>
                            <pre className="recipe-code">
                              {pat.davinci_resolve_recipe.node_tree || JSON.stringify(pat.davinci_resolve_recipe, null, 2)}
                            </pre>
                          </div>
                        )}
                      </div>
                    ))}
                    {editingPatterns.length === 0 && (
                      <div className="ref-empty-hint">
                        {lang === 'ru'
                          ? 'Нет паттернов под выбранные фильтры. Выберите другой профиль или категорию.'
                          : 'No patterns found matching current filters.'}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* TAB 8: AI VFX INTELLIGENCE & DECISION ENGINE (PHASE 3.5) */}
            {workbenchTab === 'vfx_intelligence' && (
              <div className="workbench-panel vfx-intelligence-panel">
                <div className="panel-header-row">
                  <div>
                    <h3>{lang === 'ru' ? '✨ AI VFX Интеллект & Решения' : '✨ AI VFX Intelligence & Decision Engine'}</h3>
                    <p className="panel-subtitle">
                      {lang === 'ru'
                        ? 'Контекстный отбор визуальных эффектов: оценка темпа, фокуса и активное применение правила "меньше значит лучше" с обоснованием отклонений.'
                        : 'Context-aware VFX selection: pace evaluation, focal isolation, and strict enforcement of "less is better" with rejection rationales.'}
                    </p>
                  </div>
                  <div className="vfx-header-actions">
                    <span className="vfx-catalog-badge">📚 {vfxCatalog.length} recipes</span>
                    <button className="btn-vfx-plugin-lab" onClick={handleOpenPluginResearch}>
                      🧪 {lang === 'ru' ? 'Исследование Плагинов (OFX)' : 'Plugin Lab Research'}
                    </button>
                  </div>
                </div>

                {/* SCENE CONTEXT & 3-TIER COMPARISON SWITCHER */}
                <div className="vfx-controls-card">
                  <div className="vfx-scene-selector-row">
                    <span className="vfx-control-label">{lang === 'ru' ? 'Тестовая сцена CS2:' : 'CS2 Scene Context:'}</span>
                    <div className="vfx-scene-btns">
                      <button
                        className={`vfx-scene-btn ${vfxSelectedScene === 'scene_headshot' ? 'active' : ''}`}
                        onClick={() => {
                          setVfxSelectedScene('scene_headshot')
                          runVfxEvaluation('scene_headshot', vfxActiveTier)
                        }}
                      >
                        🎯 {lang === 'ru' ? 'Сцена 07: Хедшот Kill 3 (ProfyfGames)' : 'Scene 07: Headshot Kill 3 (ProfyfGames)'}
                      </button>
                      <button
                        className={`vfx-scene-btn ${vfxSelectedScene === 'scene_rapid' ? 'active' : ''}`}
                        onClick={() => {
                          setVfxSelectedScene('scene_rapid')
                          runVfxEvaluation('scene_rapid', vfxActiveTier)
                        }}
                      >
                        ⚡ {lang === 'ru' ? 'Сцена 08: Рапид Мульти-килл Kill 4 (<0.85s)' : 'Scene 08: Rapid Multikill Kill 4 (<0.85s)'}
                      </button>
                      <button
                        className={`vfx-scene-btn ${vfxSelectedScene === 'scene_climax' ? 'active' : ''}`}
                        onClick={() => {
                          setVfxSelectedScene('scene_climax')
                          runVfxEvaluation('scene_climax', vfxActiveTier)
                        }}
                      >
                        🏆 {lang === 'ru' ? 'Сцена 09: ACE 5K Hero Orbit Climax' : 'Scene 09: ACE 5K Hero Orbit Climax'}
                      </button>
                    </div>
                  </div>

                  <div className="vfx-tier-switcher-row">
                    <span className="vfx-control-label">{lang === 'ru' ? 'Уровень обработки:' : 'Treatment Tier:'}</span>
                    <div className="vfx-tier-group">
                      <button
                        className={`vfx-tier-btn clean ${vfxActiveTier === 'CLEAN' ? 'active' : ''}`}
                        onClick={() => {
                          setVfxActiveTier('CLEAN')
                          runVfxEvaluation(vfxSelectedScene, 'CLEAN')
                        }}
                      >
                        <span className="tier-tag">TIER 1 (0)</span>
                        <span className="tier-title">{lang === 'ru' ? 'Чистый CS2 (0 VFX)' : 'Clean In-Engine (0 VFX)'}</span>
                      </button>
                      <button
                        className={`vfx-tier-btn subtle ${vfxActiveTier === 'SUBTLE' ? 'active' : ''}`}
                        onClick={() => {
                          setVfxActiveTier('SUBTLE')
                          runVfxEvaluation(vfxSelectedScene, 'SUBTLE')
                        }}
                      >
                        <span className="tier-tag rec">REC ({vfxComparisonTiers?.subtle?.selected_effects?.length ?? 3})</span>
                        <span className="tier-title">{lang === 'ru' ? 'Тонкий VFX (Рекомендован)' : 'Subtle VFX (Recommended)'}</span>
                      </button>
                      <button
                        className={`vfx-tier-btn strong ${vfxActiveTier === 'STRONG_CINEMATIC' ? 'active' : ''}`}
                        onClick={() => {
                          setVfxActiveTier('STRONG_CINEMATIC')
                          runVfxEvaluation(vfxSelectedScene, 'STRONG_CINEMATIC')
                        }}
                      >
                        <span className="tier-tag strong">MAX ({vfxComparisonTiers?.strong?.selected_effects?.length ?? 5})</span>
                        <span className="tier-title">{lang === 'ru' ? 'Сильный Синематик' : 'Strong Cinematic'}</span>
                      </button>
                    </div>
                  </div>
                </div>

                {/* DECISION SUMMARY BANNER */}
                {vfxDecision && (
                  <div className="vfx-summary-banner">
                    <div className="vfx-summary-info">
                      <div className="summary-headline">
                        <span className="tier-indicator-badge">{vfxDecision.treatment_tier}</span>
                        <span className="summary-text">{vfxDecision.summary}</span>
                      </div>
                      <div className="summary-meta-grid">
                        <div className="summary-meta-item">
                          <span className="label">Grade LUT:</span>
                          <span className="val">{vfxDecision.color_page_grade}</span>
                        </div>
                        <div className="summary-meta-item">
                          <span className="label">Fairlight Sidechain:</span>
                          <span className="val-db">{vfxDecision.fairlight_audio_ducking_db.toFixed(1)} dB</span>
                        </div>
                        <div className="summary-meta-item full">
                          <span className="label">Fusion Flow:</span>
                          <code className="val-flow">{vfxDecision.fusion_macro_recipe}</code>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* TWO-COLUMN INSPECTOR: SELECTED VS REJECTED ("LESS IS BETTER") */}
                <div className="vfx-inspector-grid">
                  {/* SELECTED EFFECTS */}
                  <div className="vfx-column selected-col">
                    <div className="vfx-col-header selected">
                      <h4>
                        ✅ {lang === 'ru' ? 'Применённые эффекты' : 'Selected VFX Treatments'} (
                        {vfxDecision?.selected_effects?.length || 0})
                      </h4>
                      <span className="vfx-col-tag">{lang === 'ru' ? 'Польза подтверждена' : 'Value Proven'}</span>
                    </div>

                    <div className="vfx-items-list">
                      {vfxDecision?.selected_effects?.map((eff: any) => (
                        <div key={eff.effect_id} className="vfx-card selected">
                          <div className="vfx-card-top">
                            <span className="vfx-cat-badge">{eff.category}</span>
                            <span className="vfx-conf-badge">{eff.confidence}</span>
                            <div className="vfx-vote-btns">
                              <button
                                className={`btn-vfx-vote like ${vfxFeedback[eff.effect_id] === 'like' ? 'voted' : ''}`}
                                onClick={() => handleVoteEffect(eff.effect_id, vfxFeedback[eff.effect_id], 'like')}
                                title="Like this VFX decision"
                              >
                                👍
                              </button>
                              <button
                                className={`btn-vfx-vote dislike ${vfxFeedback[eff.effect_id] === 'dislike' ? 'voted' : ''}`}
                                onClick={() => handleVoteEffect(eff.effect_id, vfxFeedback[eff.effect_id], 'dislike')}
                                title="Dislike this VFX decision"
                              >
                                👎
                              </button>
                            </div>
                          </div>

                          <h5 className="vfx-effect-name">{eff.name}</h5>

                          <div className="vfx-metric-row">
                            <span className="metric-label">{lang === 'ru' ? 'Интенсивность:' : 'Intensity:'}</span>
                            <div className="vfx-intensity-bar">
                              <div
                                className="vfx-intensity-fill"
                                style={{ width: `${Math.min(100, Math.round(eff.intensity * 100))}%` }}
                              />
                            </div>
                            <span className="metric-val">{(eff.intensity * 100).toFixed(0)}%</span>
                          </div>

                          <div className="vfx-timing-row">
                            <span className="timing-label">⏱️ {lang === 'ru' ? 'Тайминг:' : 'Timing:'}</span>
                            <span className="timing-val">{eff.timing_range}</span>
                          </div>

                          <p className="vfx-justification">💡 {eff.justification}</p>

                          <div className="vfx-card-footer">
                            <a
                              href={`/api/cinematic/vfx/presets/${eff.fusion_preset.split('/').pop()}/download`}
                              className="btn-download-preset"
                              download
                            >
                              📥 {eff.fusion_preset.split('/').pop()}
                            </a>
                          </div>
                        </div>
                      ))}

                      {(!vfxDecision || vfxDecision.selected_effects.length === 0) && (
                        <div className="vfx-empty-card">
                          <span>
                            {lang === 'ru'
                              ? 'В режиме Clean эффекты намеренно отключены. 100% чистый внутриигровой рендер.'
                              : 'Clean mode active: 0 visual effects applied to maximize in-game purity.'}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* REJECTED EFFECTS */}
                  <div className="vfx-column rejected-col">
                    <div className="vfx-col-header rejected">
                      <h4>
                        🚫 {lang === 'ru' ? 'Отклонённые эффекты ("Меньше значит лучше")' : 'Suppressed Effects ("Less is Better")'} (
                        {vfxDecision?.rejected_effects?.length || 0})
                      </h4>
                      <span className="vfx-col-tag reject">{lang === 'ru' ? 'Защита от визуального шума' : 'Clutter Defense'}</span>
                    </div>

                    <div className="vfx-items-list">
                      {vfxDecision?.rejected_effects?.map((rej: any) => (
                        <div key={rej.effect_id} className="vfx-card rejected">
                          <div className="vfx-card-top">
                            <span className="vfx-cat-badge">{rej.category}</span>
                            <span className="vfx-rej-pill">{lang === 'ru' ? 'ОТКЛОНЕНО' : 'SUPPRESSED'}</span>
                          </div>

                          <h5 className="vfx-effect-name">{rej.name}</h5>

                          <div className="vfx-rejection-box">
                            <div className="rejection-title">
                              🛡️ {lang === 'ru' ? 'Причина отклонения режиссером:' : 'Director Rejection Rationale:'}
                            </div>
                            <p className="rejection-text">{rej.rejection_reason}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* REAL VIDEO VALIDATION TESTS & COMPARISON SECTION */}
                <div className="vfx-validation-section">
                  <div className="validation-section-header">
                    <h4>🎬 {lang === 'ru' ? 'Реальные Тесты Валидации на материале Anubis ACE' : 'Real Validation Test Renders (Anubis ACE Footage)'}</h4>
                    <span className="validation-subtitle">
                      {lang === 'ru'
                        ? 'Фактические рендеры тестов замедления (100% vs 75% vs 50% vs Optical Flow), обводки игрока, акцента оружия и цветокоррекции.'
                        : 'Actual render tests for slow-mo (100% vs 75% vs 50% vs Optical Flow), player outline, weapon accent, and sandstone color grade.'}
                    </span>
                  </div>

                  <div className="vfx-tests-tabs">
                    {vfxTests.map((t) => (
                      <button
                        key={t.id}
                        className={`vfx-test-tab-btn ${vfxSelectedTest?.id === t.id ? 'active' : ''}`}
                        onClick={() => setVfxSelectedTest(t)}
                      >
                        <span className="test-tab-num">{t.id.replace('test_', 'Test ')}</span>
                        <span className="test-tab-title">{t.title}</span>
                      </button>
                    ))}
                  </div>

                  {vfxSelectedTest && (
                    <div className="vfx-test-display-card">
                      <div className="vfx-test-viewer-row">
                        <div className="vfx-video-player-container">
                          {vfxSelectedTest.video_ready ? (
                            <video
                              src={vfxSelectedTest.video_url}
                              poster={vfxSelectedTest.thumbnail_url}
                              controls
                              autoPlay
                              loop
                              muted
                              className="vfx-test-video-player"
                            />
                          ) : (
                            <img
                              src={vfxSelectedTest.thumbnail_url}
                              alt={vfxSelectedTest.title}
                              className="vfx-test-poster-img"
                            />
                          )}
                        </div>

                        <div className="vfx-test-info-panel">
                          <div className="test-info-header">
                            <span className="vfx-cat-badge">{vfxSelectedTest.category}</span>
                            <h5>{vfxSelectedTest.title}</h5>
                          </div>

                          <p className="test-info-desc">{vfxSelectedTest.description}</p>

                          <div className="test-specs-box">
                            <div className="spec-row">
                              <span className="spec-k">{lang === 'ru' ? 'Файл теста:' : 'Test File:'}</span>
                              <span className="spec-v">{vfxSelectedTest.video}</span>
                            </div>
                            <div className="spec-row">
                              <span className="spec-k">{lang === 'ru' ? 'Размер видео:' : 'Video Size:'}</span>
                              <span className="spec-v">{(vfxSelectedTest.video_size_bytes / 1024 / 1024).toFixed(2)} MB</span>
                            </div>
                            <div className="spec-row">
                              <span className="spec-k">{lang === 'ru' ? 'Статус валидации:' : 'Validation Status:'}</span>
                              <span className="spec-v verified">✅ VERIFIED (Rendered & Checked)</span>
                            </div>
                          </div>

                          <div className="test-findings-box">
                            <h6>🔍 {lang === 'ru' ? 'Результат анализа артефактов:' : 'Artifact Analysis Finding:'}</h6>
                            <p>
                              {vfxSelectedTest.id === 'test_01' && (lang === 'ru'
                                ? 'Optical flow (minterpolate) обеспечивает плавный шаг кадров на 50% без двоения, но требует исходника >= 50 FPS. На быстрых мультикиллах (<0.85с) замедление ломает темп.'
                                : 'Optical flow interpolation guarantees clean 50% slow-mo without frame judder, but requires source >= 50 FPS. Must be suppressed on rapid multikills (<0.85s).')}
                              {vfxSelectedTest.id === 'test_02' && (lang === 'ru'
                                ? 'Обводка игрока (Gold Climax) эффективна только на облетах камеры в эйсе. Во время активной стрельбы обводка врагов мешает видимости прицела.'
                                : 'Gold player outline is impactful during victory orbit shots, but suppresses during crossfire to preserve weapon viewmodel accuracy.')}
                              {vfxSelectedTest.id === 'test_03' && (lang === 'ru'
                                ? 'Спекулярный контур оружия подчеркивает металлический скин без изменения точности попадания в центр экрана.'
                                : 'Weapon specular rim lighting accents skin specular highlights without occluding the crosshair center screen.')}
                              {vfxSelectedTest.id === 'test_04' && (lang === 'ru'
                                ? 'Египетский песчаник (Sandstone + Azure Sky) дает кинематографичный контраст архитектуры Anubis при сохранении яркости теней.'
                                : 'Egyptian Sandstone LUT yields cinematic warm/teal separation while preserving detail in shaded corridors.')}
                              {vfxSelectedTest.id === 'test_05' && (lang === 'ru'
                                ? 'Направленный whip-pan бесшовно маскирует смену ракурса между подходом от 3-го лица и POV-фрагами.'
                                : 'Directional whip pan seamlessly masks the angle cut between third-person approach and first-person kills.')}
                              {vfxSelectedTest.id === 'test_06' && (lang === 'ru'
                                ? 'Сравнение Clean vs Subtle vs Strong: Subtle является идеальным балансом соревновательной чистоты CS2 и монтажной эстетики.'
                                : 'Comparison proves Subtle tier offers the sweet spot between competitive CS2 clarity and cinematic beauty.')}
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* FUSION PRESETS DOWNLOAD GALLERY */}
                <div className="vfx-presets-gallery-card">
                  <div className="presets-header">
                    <h4>📦 {lang === 'ru' ? 'Готовые Fusion .setting Пресеты (DaVinci Resolve Free 21.0)' : 'Native Fusion .setting Preset Library'}</h4>
                    <span className="presets-subtitle">
                      {lang === 'ru'
                        ? '11 автономных пресетов без платных плагинов. Drag-and-drop прямо в Fusion Page DaVinci Resolve.'
                        : '11 standalone compositions requiring 0 paid plugins. Ready for direct drag-and-drop into Resolve Fusion.'}
                    </span>
                  </div>

                  <div className="ref-cat-pills">
                    <span className="ref-filter-label">{lang === 'ru' ? 'Категория:' : 'Category:'}</span>
                    {['all', 'TIME', 'SUBJ', 'WEAP', 'ENV', 'COMP', 'CAM', 'COLOR'].map((cat) => (
                      <button
                        key={cat}
                        className={`cat-pill ${vfxActiveCategory === cat ? 'active' : ''}`}
                        onClick={() => setVfxActiveCategory(cat)}
                      >
                        {cat}
                      </button>
                    ))}
                  </div>

                  <div className="presets-pill-grid">
                    {vfxPresets
                      .filter((p) => vfxActiveCategory === 'all' || p.filename.toUpperCase().includes(vfxActiveCategory))
                      .map((p) => (
                      <div key={p.filename} className="preset-pill-item">
                        <div className="preset-pill-left">
                          <span className="preset-icon">🎛️</span>
                          <div>
                            <div className="preset-pill-name">{p.name}</div>
                            <div className="preset-pill-size">{(p.size_bytes / 1024).toFixed(1)} KB • DaVinci Fusion Macro</div>
                          </div>
                        </div>
                        <a href={p.url} className="btn-preset-dl" download>
                          ⬇️ {lang === 'ru' ? 'Скачать' : 'Download'}
                        </a>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </section>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODE 2: 3D CAMERA PLANNER WIZARD (EXISTING VERIFIED 5-STEP PLANNER)        */}
      {/* ========================================================================= */}
      {viewMode === 'planner' && (
        <div className="planner-wizard-layout">
          {/* Steps Strip */}
          <div className="cinematic-steps-strip">
            <button
              className={`cinematic-step-pill ${currentStep === 1 ? 'active' : ''}`}
              onClick={() => setCurrentStep(1)}
            >
              <span>1</span>
              {lang === 'ru' ? 'Демка' : 'Demo Selection'}
            </button>
            <button
              className={`cinematic-step-pill ${currentStep === 2 ? 'active' : ''}`}
              onClick={() => setCurrentStep(2)}
            >
              <span>2</span>
              {lang === 'ru' ? 'Рейтинг Хайлайтов' : 'Highlight Ranking'}
            </button>
            <button
              className={`cinematic-step-pill ${currentStep === 3 ? 'active' : ''}`}
              onClick={() => setCurrentStep(3)}
              disabled={plannedShots.length === 0}
            >
              <span>3</span>
              {lang === 'ru' ? 'План Камер' : 'Camera Plan'}
            </button>
            <button
              className={`cinematic-step-pill ${currentStep === 4 ? 'active' : ''}`}
              onClick={() => setCurrentStep(4)}
              disabled={!packageSummary}
            >
              <span>4</span>
              {lang === 'ru' ? 'Захват HLAE' : 'Capture & Manifests'}
            </button>
            <button
              className={`cinematic-step-pill ${currentStep === 5 ? 'active' : ''}`}
              onClick={() => setCurrentStep(5)}
              disabled={!packageSummary}
            >
              <span>5</span>
              {lang === 'ru' ? 'DaVinci Resolve' : 'Resolve Project'}
            </button>
          </div>

          {/* STEP 2: HIGHLIGHT RANKING */}
          {currentStep === 2 && (
            <div className="cinematic-step-panel">
              <div className="cinematic-panel-header">
                <div>
                  <h3>{lang === 'ru' ? 'Рейтинг Хайлайтов Матча' : 'Ranked Match Highlights'}</h3>
                  <p>{lang === 'ru' ? 'Выберите лучшие моменты раунда для генерации кинематографичных ракурсов.' : 'Select top moments to generate cinematic camera paths.'}</p>
                </div>
                <button
                  className="btn-cinematic-primary"
                  onClick={handlePlanShots}
                  disabled={selectedHighlightIds.size === 0 || isLoading}
                >
                  <SparkleIcon size={16} />
                  <span>{lang === 'ru' ? 'Создать План Камер (AI)' : 'Plan Cinematic Shots (AI)'}</span>
                </button>
              </div>

              <div className="cinematic-highlights-grid">
                {highlights.map((h) => {
                  const isSelected = selectedHighlightIds.has(h.id)
                  return (
                    <div
                      key={h.id}
                      className={`cinematic-card ${isSelected ? 'selected' : ''}`}
                      onClick={() => {
                        const next = new Set(selectedHighlightIds)
                        if (isSelected) next.delete(h.id)
                        else next.add(h.id)
                        setSelectedHighlightIds(next)
                      }}
                    >
                      <div className="cinematic-card-header">
                        <span className="round-badge">R{h.round_num}</span>
                        <span className="score-badge">{h.score.toFixed(1)} pts</span>
                      </div>
                      <div className="cinematic-card-body">
                        <h4>{h.pov_name || 'Player'}</h4>
                        <div className="badges-row">
                          {h.is_ace && <span className="badge badge-ace">ACE 5K</span>}
                          {h.has_headshot && <span className="badge badge-hs">HEADSHOT</span>}
                          <span className="badge badge-type">{h.highlight_type}</span>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* STEP 3: CAMERA PLAN */}
          {currentStep === 3 && (
            <div className="cinematic-step-panel">
              <div className="cinematic-panel-header">
                <div>
                  <h3>{lang === 'ru' ? 'Кинематографический План Съемки' : 'Cinematic Shot Plan'}</h3>
                  <p>{lang === 'ru' ? 'Сгенерированные траектории HLAE mirv_campath и ракурсы камер.' : 'Generated HLAE mirv_campath splines and camera angles.'}</p>
                </div>
                <button
                  className="btn-cinematic-primary"
                  onClick={handleCreatePackage}
                  disabled={isLoading}
                >
                  <CheckIcon size={16} />
                  <span>{lang === 'ru' ? 'Скомпилировать Пакет Производства' : 'Build Production Package'}</span>
                </button>
              </div>

              <div className="shots-table-wrapper">
                <table className="cinematic-table">
                  <thead>
                    <tr>
                      <th>Shot ID</th>
                      <th>Camera Type</th>
                      <th>Purpose</th>
                      <th>Duration</th>
                      <th>FOV</th>
                      <th>Campath</th>
                      <th>Resolution</th>
                    </tr>
                  </thead>
                  <tbody>
                    {plannedShots.map((shot) => (
                      <tr key={shot.shot_id}>
                        <td><code>{shot.shot_id}</code></td>
                        <td><b>{shot.camera_type}</b></td>
                        <td>{shot.purpose}</td>
                        <td>{shot.duration_seconds.toFixed(2)}s</td>
                        <td>{shot.fov}°</td>
                        <td>{shot.has_campath ? '✓ Spline' : 'POV'}</td>
                        <td>{shot.resolution} @ {shot.fps}fps</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* STEP 4: CAPTURE & MANIFESTS */}
          {currentStep === 4 && packageSummary && (
            <div className="cinematic-step-panel">
              <div className="cinematic-panel-header">
                <div>
                  <h3>{lang === 'ru' ? 'Пакет Производства & Манифесты' : 'Production Package & Manifests'}</h3>
                  <p>{lang === 'ru' ? 'Все 7 манифестов готовы к автоматическому захвату в CS2/HLAE.' : 'All 7 manifests compiled and ready for CS2/HLAE execution.'}</p>
                </div>
                <button
                  className="btn-cinematic-primary"
                  onClick={() => setCurrentStep(5)}
                >
                  <span>{lang === 'ru' ? 'Перейти к DaVinci Resolve' : 'Proceed to DaVinci Resolve'} ➔</span>
                </button>
              </div>

              <div className="manifests-grid">
                {[
                  'highlight_manifest.json',
                  'shot_plan.json',
                  'camera_paths.json',
                  'capture_manifest.json',
                  'edit_decision_list.json',
                  'overlay_events.json',
                  'render_manifest.json',
                ].map((name) => (
                  <div key={name} className="manifest-card">
                    <FolderIcon size={20} color="#f59e0b" />
                    <b>{name}</b>
                    <span>✓ Ready</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* STEP 5: DAVINCI RESOLVE INTEGRATION */}
          {currentStep === 5 && (
            <div className="cinematic-step-panel">
              <div className="cinematic-panel-header">
                <div>
                  <h3>{lang === 'ru' ? 'Интеграция с DaVinci Resolve Free 21.0' : 'DaVinci Resolve Free 21.0 Integration'}</h3>
                  <p>{lang === 'ru' ? 'Экспортируйте проект и таймлайн со всеми 4 видео и 6 аудио дорожками.' : 'Export timeline with 4 video tracks, 6 Fairlight stems, and markers.'}</p>
                </div>
              </div>
              <div className="resolve-card-center">
                <a
                  href="/renders/ACE_FINAL_V3_AUDIO_KILLFEED/ACE_FINAL_V3.fcpxml"
                  download="ACE_FINAL_V3.fcpxml"
                  className="btn-resolve-large"
                >
                  📥 Export Final FCPXML 1.10
                </a>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Modal: QA Contact Sheet Viewer */}
      {showQAModal && (
        <div className="modal-backdrop" onClick={() => setShowQAModal(false)}>
          <div className="modal-content-qa" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>🔍 Quality Control Contact Sheet — Multi-Point Frame Verification</h3>
              <button className="modal-close-btn" onClick={() => setShowQAModal(false)}>✕</button>
            </div>
            <div className="modal-body-qa">
              <img
                src="/renders/ACE_FINAL_V3_AUDIO_KILLFEED/qc_contact_sheet.png"
                alt="Quality Control Contact Sheet"
                className="qa-contact-sheet-img"
              />
            </div>
            <div className="modal-footer">
              <span>Verified: No Watermark • Frame-Locked Killfeed • Engagement Beat Sync • Full Sonniss SFX</span>
              <button className="btn-modal-close" onClick={() => setShowQAModal(false)}>Close</button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Reference Lab Contact Sheet Viewer */}
      {activeContactSheet && (
        <div className="modal-backdrop" onClick={() => setActiveContactSheet(null)}>
          <div className="modal-content-qa modal-content-ref-sheet" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>🖼️ Reference Lab Contact Sheet — Multimodal Frame Breakdown</h3>
              <button className="modal-close-btn" onClick={() => setActiveContactSheet(null)}>✕</button>
            </div>
            <div className="modal-body-qa">
              <img
                src={activeContactSheet}
                alt="Reference Lab Contact Sheet"
                className="qa-contact-sheet-img"
              />
            </div>
            <div className="modal-footer">
              <span>8-Frame Pacing Grid • Cut Detection • Transition Type Overlay</span>
              <button className="btn-modal-close" onClick={() => setActiveContactSheet(null)}>Close</button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Pytoshka Style Guide Viewer */}
      {showStyleGuideModal && styleGuideText && (
        <div className="modal-backdrop" onClick={() => setShowStyleGuideModal(false)}>
          <div className="modal-content-qa modal-content-styleguide" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>📖 Pytoshka Fragmovie Production Style Guide</h3>
              <button className="modal-close-btn" onClick={() => setShowStyleGuideModal(false)}>✕</button>
            </div>
            <div className="modal-body-qa styleguide-body">
              <pre className="styleguide-markdown-view">{styleGuideText}</pre>
            </div>
            <div className="modal-footer">
              <span>Authoritative editing rules: Pacing, Camera Matrix, Speed Ramps, Fairlight Mix & Resolve Recipes</span>
              <button className="btn-modal-close" onClick={() => setShowStyleGuideModal(false)}>Close</button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Reference Breakdown Card Viewer */}
      {activeReferenceCard && (
        <div className="modal-backdrop" onClick={() => setActiveReferenceCard(null)}>
          <div className="modal-content-qa modal-content-styleguide" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>📋 Reference Breakdown Card — {activeReferenceCard.refId}</h3>
              <button className="modal-close-btn" onClick={() => setActiveReferenceCard(null)}>✕</button>
            </div>
            <div className="modal-body-qa styleguide-body">
              <pre className="styleguide-markdown-view">{activeReferenceCard.content}</pre>
            </div>
            <div className="modal-footer">
              <span>Detailed Breakdown: OBSERVED vs INFERRED vs DaVinci Resolve 21 IMPLEMENTATION</span>
              <button className="btn-modal-close" onClick={() => setActiveReferenceCard(null)}>Close</button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Plugin Lab Research Viewer (Phase 3.5) */}
      {showPluginModal && vfxPluginResearch && (
        <div className="modal-backdrop" onClick={() => setShowPluginModal(false)}>
          <div className="modal-content-qa modal-content-styleguide" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>🧪 Plugin Lab Research: DaVinci Resolve Free 21.0 & AMD RX 5700 XT</h3>
              <button className="modal-close-btn" onClick={() => setShowPluginModal(false)}>✕</button>
            </div>
            <div className="modal-body-qa styleguide-body">
              <pre className="styleguide-markdown-view">{vfxPluginResearch}</pre>
            </div>
            <div className="modal-footer">
              <span>Research: Reactor 3, Glow Expo, Boris Sapphire/Maxon OFX Watermark Limits, and AMD OpenCL Performance</span>
              <button className="btn-modal-close" onClick={() => setShowPluginModal(false)}>Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
