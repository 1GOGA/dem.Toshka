export interface DemoSummary {
  id: number
  file_path: string
  fingerprint: string
  map_name: string | null
  tickrate: number
  duration_seconds: number | null
  schema_version: string
  created_at: string
  rounds_count: number
  players_count: number
  highlights_count: number
}

export interface PlayerStats {
  name: string
  steam_id: string | null
  team: string | null
  kills: number
  deaths: number
  assists: number
  suicides: number
  teamkills: number
  headshots: number
  headshot_pct: number
  kd_ratio: number
  kpr?: number
  dpr?: number
  differential?: number
  performance_rating?: number
  faceit_level?: number
  kast_pct?: number
  opening_kills?: number
  opening_deaths?: number
  multikills?: Record<string, number>
  clutches_won?: number
  adr: number | null
  weapon_kills: Record<string, number>
  kills_by_round: Record<number, number>
}

export interface MatchScoreboard {
  total_rounds: number
  score: Record<string, number>
  players: PlayerStats[]
  weapon_summary: Record<string, number>
}

export interface HighlightItem {
  id: string
  demo_id: number
  highlight_type: string
  round_num: number
  pov_steam_id: string | null
  pov_name: string | null
  kill_start_tick: number
  kill_end_tick: number
  clip_start_tick: number
  clip_end_tick: number
  kill_count: number
  tags: string[]
  is_heuristic: boolean
  detection_reason: string
  radar_x?: number | null
  radar_y?: number | null
  victim_radar_x?: number | null
  victim_radar_y?: number | null
  radar_level?: 'upper' | 'lower' | 'main' | null
}

export interface PlayerDTO {
  id: number
  demo_id: number
  name: string
  steam_id: string | null
  team: string | null
}

export interface RoundDTO {
  id: number
  round_num: number
  start_tick: number
  freeze_end_tick: number | null
  end_tick: number
  official_end_tick: number | null
  winner: string | null
  reason: string | null
  bomb_plant_tick: number | null
  bomb_site: string | null
}

export interface KillDTO {
  id: number
  demo_id: number
  tick: number
  round_num: number | null
  attacker_name: string | null
  attacker_steam_id: string | null
  attacker_team: string | null
  victim_name: string | null
  victim_steam_id: string | null
  victim_team: string | null
  weapon: string | null
  headshot: boolean | null
  noscope: boolean | null
  thru_smoke: boolean | null
  wallbang: boolean | null
  is_suicide: boolean
  is_teamkill: boolean
}

export interface RenderJobDTO {
  id: string
  demo_id: number
  highlight_id: string | null
  status: string
  progress: number
  output_path: string | null
  error_summary: string | null
  log_path: string | null
  settings_json?: string | null
  created_at: string
}

export interface ClipSettings {
  resolution: '1080p' | '720p' | '1280x960' | '1440x1080' | '1024x768' | string
  aspectRatio: '16:9' | '4:3'
  stretch43?: boolean
  fps: 60 | 30
  preRollSeconds: number
  postRollSeconds: number
  perspective: 'attacker' | 'victim' | 'specific_player' | 'dynamic_killcam'
  perspectiveSteamId?: string
  xray: boolean
  hudMode: 'huge_esports' | 'huge_killfeed' | 'full' | 'killfeed_only' | 'none'
  hudScale?: number // 0.95, 1.05, 1.15, 1.25
  customCrosshair: boolean
  fov?: number // 68, 90, 95, 100, 105
  viewmodelFov?: number // 60, 68
  crosshairPreset?: 'pro_cyan' | 'green_clean' | 'dot' | 'minimal_white' | 'hidden' | 'default'
  crosshairColor?: 'cyan' | 'green' | 'yellow' | 'white' | 'pink' | 'red' | 'blue'
  radarMode?: 'dynamic_large' | 'broadcast_giant' | 'broadcast' | 'player_focus' | 'compact' | 'hidden'
}

export interface MontageDTO {
  success: boolean
  output_path: string
  filename: string
  duration_seconds: number
  total_clips: number
  message?: string
}

export interface ReplayPlayerState {
  steam_id: string
  name: string
  side: 'ct' | 't'
  health: number
  x: number // 0..100 % on radar
  y: number // 0..100 % on radar
  world_z: number
  level: 'upper' | 'lower'
  place: string
  is_alive: boolean
}

export interface ReplayFrame {
  tick: number
  players: ReplayPlayerState[]
}

export interface ReplayKillItem {
  tick: number
  attacker_name: string
  attacker_steam_id: string
  attacker_side: string
  attacker_x: number
  attacker_y: number
  victim_name: string
  victim_steam_id: string
  victim_side: string
  victim_x: number
  victim_y: number
  weapon: string
  headshot: boolean
}

export interface RoundReplayData {
  round_num: number
  map_name: string
  tickrate: number
  start_tick: number
  end_tick: number
  radar_file?: string
  radar_file_lower?: string
  levels?: string[]
  frames: ReplayFrame[]
  kills: ReplayKillItem[]
  players: Record<string, { steam_id: string; name: string; side: string }>
}

export interface CompletedClipDTO {
  filename: string
  path: string
  size_bytes: number
  modified_at: number
  is_montage: boolean
  url: string
  demo_id?: number | null
  map_name?: string | null
  highlight_type?: string | null
  player_name?: string | null
  round_num?: number | null
  job_id?: string | null
}

export interface StorageSettingsDTO {
  output_directory: string
  is_writable: boolean
}

export interface PlayerErrorDTO {
  round_num: number
  tick: number
  error_type: string
  title: string
  description: string
  severity: 'critical' | 'warning' | 'info'
}

export interface PlayerAnalyticsDTO {
  name: string
  steam_id: string | null
  team: string | null
  total_rounds: number
  performance_rating: number
  kills: number
  deaths: number
  assists: number
  kd_ratio: number
  kpr: number
  dpr: number
  headshot_pct: number
  kast_pct: number
  swing_winrate_pct: number
  crosshair_placement_score: number
  first_bullet_accuracy_pct: number
  spray_control_pct: number
  opening_duels_won: number
  opening_duels_lost: number
  opening_winrate_pct: number
  trade_kills: number
  trade_kill_pct: number
  traded_deaths: number
  traded_death_pct: number
  clutches_won: number
  clutches_attempted: number
  clutch_winrate_pct: number
  multikill_rounds: Record<string, number>
  errors: PlayerErrorDTO[]
  strengths: string[]
  advice: string[]
  map_impact_score?: number
  fun_badges?: Array<{ badge: string; desc: string; rarity?: string }>
}



