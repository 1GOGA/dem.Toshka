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
  fps: 120 | 60 | 30
  preRollSeconds: number
  postRollSeconds: number
  perspective: 'attacker' | 'victim' | 'specific_player' | 'dynamic_killcam'
  perspectiveSteamId?: string
  xray: boolean
  hudMode: 'real' | 'huge_esports' | 'huge_killfeed' | 'full' | 'killfeed_only' | 'none'
  hudScale?: number // 0.95, 1.0, 1.05, 1.15, 1.25
  overheadMode?: boolean // show/hide player name tags over heads
  killfeedOnly?: boolean // draw only death notices
  teamcounterMode?: boolean // numbers (5v3) vs avatar icons
  customCrosshair: boolean
  fov?: number // 68, 90, 95, 100, 105
  viewmodelFov?: number // 60, 68
  crosshairPreset?: 'pro_cyan' | 'green_clean' | 'dot' | 'minimal_white' | 'hidden' | 'default'
  crosshairColor?: 'cyan' | 'green' | 'yellow' | 'white' | 'pink' | 'red' | 'blue'
  radarMode?: 'dynamic_large' | 'broadcast_giant' | 'broadcast' | 'player_focus' | 'compact' | 'hidden'
  watermark?: boolean
  watermarkPosition?: 'top_left' | 'top_right' | 'bottom_left' | 'bottom_right'
  previewRecording?: boolean
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
  yaw?: number
  pitch?: number
  armor?: number
  has_helmet?: boolean
  has_defuser?: boolean
  weapon?: string
  is_flashed?: boolean
  flash_duration?: number
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

export interface ReplayGrenadeItem {
  id: number
  type: 'smoke' | 'molotov' | 'flash' | 'he' | 'decoy'
  raw_type?: string
  thrower_name: string
  thrower_steam_id: string
  start_tick: number
  detonate_tick: number
  end_tick: number
  duration_seconds: number
  x: number
  y: number
  trajectory?: Array<{ tick: number; x: number; y: number }>
}

export interface ReplayBombData {
  plant_tick: number
  site: string
  planter_name: string
  x: number
  y: number
  duration_seconds: number
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
  grenades?: ReplayGrenadeItem[]
  bomb?: ReplayBombData | null
}

export interface CompletedClipDTO {
  filename: string
  path: string
  size_bytes: number
  modified_at: number
  is_montage: boolean
  url: string
  thumbnail_url?: string | null
  demo_id?: number | null
  demo_filename?: string | null
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

export interface TacticalDrawingDTO {
  id: string
  project_id: string
  round_num: number
  tick?: number | null
  layer_type: 'pen' | 'arrow' | 'line' | 'circle' | 'box' | 'text'
  color: string
  stroke_width: number
  geometry_json: string
  text_label?: string | null
  created_at: string
}

export interface BookmarkDTO {
  id: string
  project_id: string
  round_num: number
  tick: number
  player_steamid?: string | null
  category: string
  title: string
  notes?: string | null
  created_at: string
}

export interface AnalysisProjectDTO {
  id: string
  demo_id: number
  title: string
  description?: string | null
  created_at: string
  updated_at: string
  drawings: TacticalDrawingDTO[]
  bookmarks: BookmarkDTO[]
}

export interface VoiceStatusDTO {
  has_voice: boolean
  total_packets: number
  unique_speakers: number
}

export interface VoiceSpeechSegmentDTO {
  start_tick: number
  end_tick: number
  start_sec: number
  end_sec: number
  packet_count: number
}

export interface PlayerVoiceTrackDTO {
  steamid: string
  player_name?: string
  team?: string
  packet_count: number
  duration_sec: number
  stream_url: string
  download_wav_url: string
  segments: VoiceSpeechSegmentDTO[]
}

export interface RoundVoiceTimelineDTO {
  round_num: number
  has_voice: boolean
  tracks: PlayerVoiceTrackDTO[]
}

export interface SkillRadarSchema {
  aim_duels: number
  positioning: number
  decision_making: number
  utility: number
  trading: number
  clutch: number
}

export interface PlayerProfileDTO {
  id: string
  steam_id: string
  nickname: string
  avatar_url?: string | null
  primary_role?: string | null
  created_at: string
}

export interface PlayerInsightDTO {
  id: string
  player_profile_id: string
  category: string
  severity: string
  title: string
  pattern_description: string
  sample_size_str: string
  objective_metric_str: string
  context_conditions_str: string
  alternative_strategy_str: string
  impact_estimate_str: string
  jump_demo_id?: number | null
  jump_round_num?: number | null
  jump_tick?: number | null
}

export interface MultiMatchAnalyticsDTO {
  profile_id: string
  steam_id: string
  nickname: string
  avatar_url?: string | null
  primary_role: string
  matches_count: number
  total_rounds: number
  radar: SkillRadarSchema
  overview: {
    kd_ratio: number
    rating: number
    adr: number
    headshot_pct: number
    kast_pct: number
    kills: number
    deaths: number
    assists: number
  }
  maps: Array<{
    map_name: string
    matches: number
    rating: number
    adr: number
    kd_ratio: number
    win_rate_pct: number
  }>
  side_split: {
    ct_rating: number
    t_rating: number
  }
  insights: PlayerInsightDTO[]
}

export interface TacticalSetupDTO {
  id: string
  strategy_book_id: string
  title: string
  side: string
  phase: string
  description?: string | null
  tokens_json: string
  drawings_json: string
  created_at: string
}

export interface UtilityLineupDTO {
  id: string
  strategy_book_id?: string | null
  map_name: string
  side: string
  utility_type: string
  title: string
  throw_type: string
  pos_x: number
  pos_y: number
  target_x: number
  target_y: number
  crosshair_desc?: string | null
  created_at: string
}

export interface StrategyBookDTO {
  id: string
  title: string
  map_name: string
  team_name?: string | null
  description?: string | null
  created_at: string
  updated_at: string
  setups: TacticalSetupDTO[]
  lineups: UtilityLineupDTO[]
}

export interface CreateStrategyBookRequest {
  title: string
  map_name: string
  team_name?: string
  description?: string
}

export interface CreateTacticalSetupRequest {
  title: string
  side: string
  phase?: string
  description?: string
  tokens_json?: string
  drawings_json?: string
}






