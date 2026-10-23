export type Language = 'ru' | 'en'

export interface TranslationDictionary {
  // Brand & Header
  'brand.subtitle': string
  'brand.showcaseTooltip': string
  'nav.showcase': string
  'nav.library': string
  'nav.match': string
  'nav.replay': string
  'nav.studio': string
  'nav.clips': string
  'nav.settings': string
  'header.parameters': string
  'header.parametersTooltip': string
  'header.queue': string
  'header.telegramTooltip': string
  'header.youtubeTooltip': string

  // Language Switcher
  'lang.switcherLabel': string
  'lang.switcherTooltip': string
  'lang.autoDetected': string
  'lang.manualChoice': string
  'lang.ru': string
  'lang.en': string

  // Common UI
  'common.loading': string
  'common.save': string
  'common.saving': string
  'common.cancel': string
  'common.close': string
  'common.delete': string
  'common.clear': string
  'common.back': string
  'common.next': string
  'common.retry': string
  'common.error': string
  'common.success': string
  'common.explorer': string
  'common.all': string
  'common.rounds': string
  'common.match': string
  'common.demo': string
  'common.player': string
  'common.kills': string
  'common.deaths': string
  'common.assists': string

  // Library View
  'library.dragDropTitle': string
  'library.dragDropSubtitle': string
  'library.selectFileBtn': string
  'library.parsingDemo': string
  'library.uploading': string
  'library.parsedDemos': string
  'library.noDemos': string
  'library.noDemosSubtitle': string
  'library.colMap': string
  'library.colDuration': string
  'library.colRounds': string
  'library.colHighlights': string
  'library.colDate': string
  'library.colNote': string
  'library.colActions': string
  'library.openInStudio': string
  'library.notePlaceholder': string
  'library.invalidExtension': string

  // Showcase View
  'showcase.heroStatus': string
  'showcase.heroEyebrow': string
  'showcase.heroTitle1': string
  'showcase.heroTitle2': string
  'showcase.heroDesc': string
  'showcase.followDev': string
  'showcase.featuresBtn': string
  'showcase.openStudioBtn': string
  'showcase.archTitle': string
  'showcase.archValue': string
  'showcase.engineTitle': string
  'showcase.engineValue': string
  'showcase.featuresHeadline': string
  'showcase.featuresSubheadline': string
  'showcase.howItWorks': string
  'showcase.pipelineSubtitle': string
  'showcase.step1Title': string
  'showcase.step1Desc': string
  'showcase.step2Title': string
  'showcase.step2Desc': string
  'showcase.step3Title': string
  'showcase.step3Desc': string
  'showcase.philosophyTitle': string
  'showcase.philosophyDesc': string
  'showcase.creatorTitle': string
  'showcase.creatorSub': string
  'showcase.disclaimer': string

  // Match Overview View
  'match.title': string
  'match.subtitle': string
  'match.scoreboard': string
  'match.adr': string
  'match.hs': string
  'match.kd': string
  'match.rating': string
  'match.viewHighlights': string
  'match.playerAnalytics': string

  // Studio View
  'studio.step1': string
  'studio.step2': string
  'studio.step3': string
  'studio.step4': string
  'studio.selectPlayer': string
  'studio.allPlayers': string
  'studio.filterType': string
  'studio.filterRound': string
  'studio.filterWeapon': string
  'studio.renderSelected': string
  'studio.selectAll': string
  'studio.clearSelection': string
  'studio.noHighlights': string
  'studio.renderSettings': string
  'studio.singleLaunchNotice': string

  // 2D Replay View
  'replay.title': string
  'replay.subtitle': string
  'replay.round': string
  'replay.play': string
  'replay.pause': string
  'replay.speed': string
  'replay.grenades': string
  'replay.trails': string
  'replay.upperLevel': string
  'replay.lowerLevel': string

  // Clips & Montage View
  'clips.title': string
  'clips.subtitle': string
  'clips.openFolder': string
  'clips.createMontage': string
  'clips.noClips': string
  'clips.noClipsDesc': string
  'clips.playClip': string
  'clips.clipDuration': string

  // Settings View
  'settings.title': string
  'settings.subtitle': string
  'settings.outputDirTitle': string
  'settings.outputDirDesc': string
  'settings.writable': string
  'settings.writeError': string
  'settings.savePath': string
  'settings.savingPath': string
  'settings.shieldTitle': string
  'settings.shieldDesc': string
  'settings.restoreBtn': string
  'settings.restoring': string
  'settings.cleanupTitle': string
  'settings.cleanupDesc': string
  'settings.cleanupBtn': string
  'settings.cleaning': string

  // Clip Settings Modal
  'modal.settings.title': string
  'modal.settings.subtitle': string
  'modal.settings.tabScreen': string
  'modal.settings.tabRadar': string
  'modal.settings.tabHud': string
  'modal.settings.tabCamera': string
  'modal.settings.resolution': string
  'modal.settings.fps': string
  'modal.settings.aspectRatio': string
  'modal.settings.perspective': string
  'modal.settings.xray': string
  'modal.settings.watermark': string
  'modal.settings.save': string

  // Queue Modal
  'modal.queue.title': string
  'modal.queue.subtitle': string
  'modal.queue.startBatch': string
  'modal.queue.retryFailed': string
  'modal.queue.clearCompleted': string
  'modal.queue.statusPending': string
  'modal.queue.statusRunning': string
  'modal.queue.statusCompleted': string
  'modal.queue.statusFailed': string
}

export type TranslationKey = keyof TranslationDictionary

