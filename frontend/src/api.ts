import type {
  CompletedClipDTO,
  DemoSummary,
  HighlightItem,
  KillDTO,
  MatchScoreboard,
  MontageDTO,
  PlayerAnalyticsDTO,
  PlayerDTO,
  RenderJobDTO,
  RoundDTO,
  RoundReplayData,
  StorageSettingsDTO,
} from './types'

const BASE_URL = '/api'

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = res.statusText
    try {
      const data = await res.json()
      if (data && data.detail) {
        errorDetail = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail)
      }
    } catch {
      // Non-JSON error
    }
    throw new Error(errorDetail || `HTTP error ${res.status}`)
  }
  return res.json()
}

export const api = {
  async getHealth(): Promise<{ status: string; schema_version: string }> {
    const res = await fetch(`${BASE_URL}/health`)
    return handleResponse(res)
  },

  async listDemos(): Promise<DemoSummary[]> {
    const res = await fetch(`${BASE_URL}/demos`)
    return handleResponse(res)
  },

  async getDemo(demoId: number): Promise<DemoSummary> {
    const res = await fetch(`${BASE_URL}/demos/${demoId}`)
    return handleResponse(res)
  },

  async parseDemo(demoPath: string): Promise<DemoSummary> {
    const res = await fetch(`${BASE_URL}/demos/parse`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ demo_path: demoPath }),
    })
    return handleResponse(res)
  },

  async uploadDemo(file: File): Promise<DemoSummary> {
    const res = await fetch(`${BASE_URL}/demos/upload?filename=${encodeURIComponent(file.name)}`, {
      method: 'POST',
      body: file,
    })
    return handleResponse(res)
  },

  async getStats(demoId: number): Promise<MatchScoreboard> {
    const res = await fetch(`${BASE_URL}/demos/${demoId}/stats`)
    return handleResponse(res)
  },

  async getHighlights(
    demoId: number,
    params?: {
      pov_steam_id?: string
      highlight_type?: string
      round_num?: number
    }
  ): Promise<HighlightItem[]> {
    const query = new URLSearchParams()
    if (params?.pov_steam_id) query.append('pov_steam_id', params.pov_steam_id)
    if (params?.highlight_type) query.append('highlight_type', params.highlight_type)
    if (params?.round_num !== undefined) query.append('round_num', params.round_num.toString())

    const url = `${BASE_URL}/demos/${demoId}/highlights${query.toString() ? `?${query.toString()}` : ''}`
    const res = await fetch(url)
    return handleResponse(res)
  },

  async getPlayers(demoId: number): Promise<PlayerDTO[]> {
    const res = await fetch(`${BASE_URL}/demos/${demoId}/players`)
    return handleResponse(res)
  },

  async getPlayerAnalytics(demoId: number, playerIdentifier: string): Promise<PlayerAnalyticsDTO> {
    const res = await fetch(`${BASE_URL}/demos/${demoId}/players/${encodeURIComponent(playerIdentifier)}/analytics`)
    return handleResponse(res)
  },

  async getRounds(demoId: number): Promise<RoundDTO[]> {
    const res = await fetch(`${BASE_URL}/demos/${demoId}/rounds`)
    return handleResponse(res)
  },

  async getKills(demoId: number, roundNum?: number): Promise<KillDTO[]> {
    const url = roundNum !== undefined
      ? `${BASE_URL}/demos/${demoId}/kills?round_num=${roundNum}`
      : `${BASE_URL}/demos/${demoId}/kills`
    const res = await fetch(url)
    return handleResponse(res)
  },

  async createRenderJobs(data: {
    demo_id: number
    highlight_ids: string[]
    resolution: string
    aspect_ratio?: string
    stretch_4_3?: boolean
    fps: number
    pre_roll_seconds: number
    post_roll_seconds: number
    perspective?: string
    perspective_steam_id?: string | null
    xray?: boolean
    hud_mode?: string
    hud_scale?: number
    overhead_mode?: boolean
    killfeed_only?: boolean
    teamcounter_mode?: boolean
    custom_crosshair?: boolean
    fov?: number
    viewmodel_fov?: number
    crosshair_preset?: string
    crosshair_color?: string
    radar_mode?: string
    watermark?: boolean
    watermark_position?: 'top_left' | 'top_right' | 'bottom_left' | 'bottom_right'
    preview_recording?: boolean
  }): Promise<RenderJobDTO[]> {
    const res = await fetch(`${BASE_URL}/render-jobs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    return handleResponse(res)
  },

  async getRenderJob(jobId: string): Promise<RenderJobDTO> {
    const res = await fetch(`${BASE_URL}/render-jobs/${jobId}`)
    return handleResponse(res)
  },

  async listRenderJobs(demoId?: number): Promise<RenderJobDTO[]> {
    const url = demoId !== undefined
      ? `${BASE_URL}/render-jobs?demo_id=${demoId}`
      : `${BASE_URL}/render-jobs`
    const res = await fetch(url)
    return handleResponse(res)
  },

  async retryRenderJob(jobId: string): Promise<RenderJobDTO> {
    const res = await fetch(`${BASE_URL}/render-jobs/${jobId}/retry`, {
      method: 'POST',
    })
    return handleResponse(res)
  },

  async retryFailedJobs(demoId?: number): Promise<RenderJobDTO[]> {
    const url = demoId !== undefined
      ? `${BASE_URL}/render-jobs/retry-failed?demo_id=${demoId}`
      : `${BASE_URL}/render-jobs/retry-failed`
    const res = await fetch(url, {
      method: 'POST',
    })
    return handleResponse(res)
  },

  async deleteRenderJob(jobId: string): Promise<{ success: boolean; job_id: string }> {
    const res = await fetch(`${BASE_URL}/render-jobs/${jobId}`, {
      method: 'DELETE',
    })
    return handleResponse(res)
  },

  async clearCompletedRenderJobs(demoId?: number): Promise<{ success: boolean; cleared_count: number }> {
    const url = demoId !== undefined
      ? `${BASE_URL}/render-jobs/clear-completed?demo_id=${demoId}`
      : `${BASE_URL}/render-jobs/clear-completed`
    const res = await fetch(url, {
      method: 'POST',
    })
    return handleResponse(res)
  },

  async createMontage(data: {
    filenames?: string[]
    job_ids?: string[]
    demo_id?: number
    output_filename?: string
  }): Promise<MontageDTO> {
    const res = await fetch(`${BASE_URL}/montage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    return handleResponse(res)
  },

  async getRoundReplay(demoId: number, roundNum: number, stepTicks: number = 32): Promise<RoundReplayData> {
    const res = await fetch(`${BASE_URL}/demos/${demoId}/rounds/${roundNum}/replay?step_ticks=${stepTicks}`)
    return handleResponse(res)
  },

  async getStorageSettings(): Promise<StorageSettingsDTO> {
    const res = await fetch(`${BASE_URL}/settings/storage`)
    return handleResponse(res)
  },

  async setStorageSettings(directory: string): Promise<StorageSettingsDTO & { success: boolean; message: string }> {
    const res = await fetch(`${BASE_URL}/settings/storage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ directory }),
    })
    return handleResponse(res)
  },

  async openOutputFolder(): Promise<{ success: boolean; message: string }> {
    const res = await fetch(`${BASE_URL}/renders/open-folder`, { method: 'POST' })
    return handleResponse(res)
  },

  async cleanupTempArtifacts(): Promise<{ success: boolean; cleaned: Record<string, number> }> {
    const res = await fetch(`${BASE_URL}/renders/cleanup-temp`, { method: 'POST' })
    return handleResponse(res)
  },

  async deleteClips(filenames: string[]): Promise<{ success: boolean; deleted: string[] }> {
    const res = await fetch(`${BASE_URL}/renders/delete-clips`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filenames }),
    })
    return handleResponse(res)
  },

  async listCompletedClips(demoId?: number): Promise<CompletedClipDTO[]> {
    const url = demoId ? `${BASE_URL}/renders/clips?demo_id=${demoId}` : `${BASE_URL}/renders/clips`
    const res = await fetch(url)
    return handleResponse(res)
  },

  async cleanupAllClips(): Promise<{ success: boolean; deleted: string[]; count: number }> {
    const res = await fetch(`${BASE_URL}/renders/cleanup-all-clips`, { method: 'POST' })
    return handleResponse(res)
  },

  async cleanupRenderLogs(): Promise<{ success: boolean; deleted: string[]; count: number }> {
    const res = await fetch(`${BASE_URL}/renders/cleanup-logs`, { method: 'POST' })
    return handleResponse(res)
  },

  async listMontages(): Promise<MontageDTO[]> {
    const res = await fetch(`${BASE_URL}/montages`)
    return handleResponse(res)
  },

  async cleanupDemoClips(demoId: number): Promise<{ success: boolean; deleted: string[]; count: number }> {
    const res = await fetch(`${BASE_URL}/renders/cleanup-demo/${demoId}`, { method: 'POST' })
    return handleResponse(res)
  },

  async restoreCS2Config(): Promise<{ success: boolean; restored_files_count: number; message: string }> {
    const res = await fetch(`${BASE_URL}/settings/restore-cs2-config`, { method: 'POST' })
    return handleResponse(res)
  },

  async getCS2ConfigStatus(): Promise<{
    csgo_cfg_dir: string
    csgo_cfg_exists: boolean
    has_autoexec: boolean
    has_restore_user: boolean
    userdata_dir: string
    userdata_exists: boolean
  }> {
    const res = await fetch(`${BASE_URL}/settings/cs2-config-status`)
    return handleResponse(res)
  },

  // Cinematic Studio API
  async getCinematicHighlights(demoId: number): Promise<any[]> {
    const res = await fetch(`${BASE_URL}/cinematic/demos/${demoId}/highlights`)
    return handleResponse(res)
  },

  async planCinematicShots(demoId: number, highlightIds: string[], fps: number = 60): Promise<{ shots: any[] }> {
    const res = await fetch(`${BASE_URL}/cinematic/plan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ demo_id: demoId, highlight_ids: highlightIds, fps }),
    })
    return handleResponse(res)
  },

  async createProductionPackage(demoId: number, shots: any[], projectName?: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/cinematic/package`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ demo_id: demoId, shots, project_name: projectName }),
    })
    return handleResponse(res)
  },

  async getPackageManifests(packageId: string): Promise<Record<string, any>> {
    const res = await fetch(`${BASE_URL}/cinematic/package/${packageId}/manifests`)
    return handleResponse(res)
  },

  getPackageFcpxmlUrl(packageId: string): string {
    return `${BASE_URL}/cinematic/package/${packageId}/fcpxml`
  },

  async getCinematicProductionOverview(): Promise<any> {
    const res = await fetch(`${BASE_URL}/cinematic/production/overview`)
    return handleResponse(res)
  },

  async getSceneAnalysis(): Promise<any> {
    const res = await fetch(`${BASE_URL}/cinematic/scene-analysis`)
    return handleResponse(res)
  },

  // Phase 3.3 Production Workbench & Asset Library APIs
  async getSoundLibrary(params?: { category?: string; search?: string }): Promise<any> {
    const query = new URLSearchParams()
    if (params?.category) query.append('category', params.category)
    if (params?.search) query.append('search', params.search)
    const url = `${BASE_URL}/cinematic/sound-library${query.toString() ? `?${query.toString()}` : ''}`
    const res = await fetch(url)
    return handleResponse(res)
  },

  async getProductionWorkflowState(): Promise<any> {
    const res = await fetch(`${BASE_URL}/cinematic/production/workflow-state`)
    return handleResponse(res)
  },

  async setTimelineLock(action: 'lock' | 'unlock' | 'invalidate'): Promise<any> {
    const res = await fetch(`${BASE_URL}/cinematic/production/lock-timeline`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action }),
    })
    return handleResponse(res)
  },

  async setHudProfile(activeProfile?: string, hudToggles?: Record<string, boolean>): Promise<any> {
    const res = await fetch(`${BASE_URL}/cinematic/production/hud-profiles`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ active_profile: activeProfile, hud_toggles: hudToggles }),
    })
    return handleResponse(res)
  },

  async getTransitionsCatalog(): Promise<any> {
    const res = await fetch(`${BASE_URL}/cinematic/production/transitions`)
    return handleResponse(res)
  },

  // Phase 3.4 Fragmovie Reference Lab APIs
  async getReferenceInbox(): Promise<any> {
    const res = await fetch(`${BASE_URL}/cinematic/reference-lab/inbox`)
    return handleResponse(res)
  },

  async scanReferenceInbox(): Promise<any> {
    const res = await fetch(`${BASE_URL}/cinematic/reference-lab/scan`, {
      method: 'POST',
    })
    return handleResponse(res)
  },

  async analyzeReferenceVideo(filename: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/cinematic/reference-lab/analyze/${encodeURIComponent(filename)}`, {
      method: 'POST',
    })
    return handleResponse(res)
  },

  async getAnalyzedReferences(): Promise<any> {
    const res = await fetch(`${BASE_URL}/cinematic/reference-lab/references`)
    return handleResponse(res)
  },

  async getReferenceReport(refId: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/cinematic/reference-lab/references/${encodeURIComponent(refId)}`)
    return handleResponse(res)
  },

  async getEditingPatterns(params?: { profile?: string; category?: string }): Promise<any> {
    const query = new URLSearchParams()
    if (params?.profile) query.append('profile', params.profile)
    if (params?.category) query.append('category', params.category)
    const url = `${BASE_URL}/cinematic/reference-lab/patterns${query.toString() ? `?${query.toString()}` : ''}`
    const res = await fetch(url)
    return handleResponse(res)
  },

  async getStyleGuide(): Promise<{ content: string; path: string }> {
    const res = await fetch(`${BASE_URL}/cinematic/reference-lab/style-guide`)
    return handleResponse(res)
  },

  getContactSheetUrl(filename: string): string {
    return `${BASE_URL}/cinematic/reference-lab/contact-sheets/${filename}`
  },

  async voteReference(refId: string, vote: 'liked' | 'disliked' | null): Promise<any> {
    const res = await fetch(`${BASE_URL}/cinematic/reference-lab/references/${encodeURIComponent(refId)}/vote`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ vote }),
    })
    return handleResponse(res)
  },

  async votePattern(patternId: string, vote: 'liked' | 'disliked' | null): Promise<any> {
    const res = await fetch(`${BASE_URL}/cinematic/reference-lab/patterns/${encodeURIComponent(patternId)}/vote`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ vote }),
    })
    return handleResponse(res)
  },

  async getReferenceCard(refId: string): Promise<{ reference_id: string; content: string; path: string }> {
    const res = await fetch(`${BASE_URL}/cinematic/reference-lab/reference-cards/${encodeURIComponent(refId)}`)
    return handleResponse(res)
  },

  // Phase 3.5 AI VFX Intelligence & Decision Engine APIs
  async getVfxCatalog(category?: string): Promise<{ count: number; category_filter?: string; effects: any[] }> {
    const url = `${BASE_URL}/cinematic/vfx/catalog${category ? `?category=${encodeURIComponent(category)}` : ''}`
    const res = await fetch(url)
    return handleResponse(res)
  },

  async decideVfx(payload: any): Promise<any> {
    const res = await fetch(`${BASE_URL}/cinematic/vfx/decide`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    return handleResponse(res)
  },

  async compareVfxTiers(payload: any): Promise<{ clean: any; subtle: any; strong: any }> {
    const res = await fetch(`${BASE_URL}/cinematic/vfx/compare`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    return handleResponse(res)
  },

  async getVfxPresets(): Promise<{ count: number; presets: any[] }> {
    const res = await fetch(`${BASE_URL}/cinematic/vfx/presets`)
    return handleResponse(res)
  },

  async getVfxValidationTests(): Promise<{ count: number; tests: any[] }> {
    const res = await fetch(`${BASE_URL}/cinematic/vfx/tests`)
    return handleResponse(res)
  },

  async submitVfxFeedback(effectId: string, vote: 'like' | 'dislike' | null, note?: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/cinematic/vfx/feedback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ effect_id: effectId, vote, note }),
    })
    return handleResponse(res)
  },

  async getVfxPluginResearch(): Promise<{ content: string; path: string }> {
    const res = await fetch(`${BASE_URL}/cinematic/vfx/plugin-research`)
    return handleResponse(res)
  },
}



