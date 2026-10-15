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

  async cleanupDemoClips(demoId: number): Promise<{ success: boolean; deleted: string[]; count: number }> {
    const res = await fetch(`${BASE_URL}/renders/cleanup-demo/${demoId}`, { method: 'POST' })
    return handleResponse(res)
  },
}


