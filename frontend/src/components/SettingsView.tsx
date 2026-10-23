import { useEffect, useState } from 'react'
import { api } from '../api'
import { useTranslation } from '../i18n'

export function SettingsView() {
  const { t } = useTranslation()
  const [outputDir, setOutputDir] = useState('')
  const [isWritable, setIsWritable] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [saveMessage, setSaveMessage] = useState<string | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const [isCleaning, setIsCleaning] = useState(false)
  const [cleanReport, setCleanReport] = useState<string | null>(null)

  const [isRestoringConfig, setIsRestoringConfig] = useState(false)
  const [configRestoreReport, setConfigRestoreReport] = useState<string | null>(null)
  const [configStatus, setConfigStatus] = useState<{
    csgo_cfg_dir: string
    csgo_cfg_exists: boolean
    has_autoexec: boolean
    has_restore_user: boolean
  } | null>(null)

  useEffect(() => {
    api
      .getStorageSettings()
      .then((data) => {
        setOutputDir(data.output_directory)
        setIsWritable(data.is_writable)
      })
      .catch((err) => {
        console.error('Failed to load storage settings:', err)
      })

    api
      .getCS2ConfigStatus()
      .then((status) => {
        setConfigStatus(status)
      })
      .catch((err) => {
        console.error('Failed to load CS2 config status:', err)
      })
  }, [])

  const handleSaveDirectory = async () => {
    if (!outputDir.trim()) return
    setIsSaving(true)
    setSaveMessage(null)
    setErrorMessage(null)

    try {
      const res = await api.setStorageSettings(outputDir.trim())
      setOutputDir(res.output_directory)
      setIsWritable(res.is_writable)
      setSaveMessage('✓ Путь успешно проверен и сохранен!')
    } catch (err: any) {
      setErrorMessage(err?.message || 'Ошибка сохранения пути')
    } finally {
      setIsSaving(false)
    }
  }

  const handleOpenExplorer = async () => {
    try {
      await api.openOutputFolder()
    } catch (err: any) {
      setErrorMessage(err?.message || 'Не удалось открыть проводник')
    }
  }

  const handleCleanupTemp = async () => {
    setIsCleaning(true)
    setCleanReport(null)
    try {
      const res = await api.cleanupTempArtifacts()
      const d = res.cleaned.directories || 0
      const w = res.cleaned.wav_files || 0
      const l = res.cleaned.log_files || 0
      setCleanReport(`✓ Очищено временных папок: ${d}, промежуточных звуков .wav: ${w}, логов: ${l}. Готовые MP4 сохранены.`)
    } catch (err: any) {
      setErrorMessage(err?.message || 'Ошибка очистки временных файлов')
    } finally {
      setIsCleaning(false)
    }
  }

  const handleRestoreCS2Config = async () => {
    setIsRestoringConfig(true)
    setConfigRestoreReport(null)
    setErrorMessage(null)
    try {
      const res = await api.restoreCS2Config()
      setConfigRestoreReport(`✓ ${res.message}`)
      const status = await api.getCS2ConfigStatus()
      setConfigStatus(status)
    } catch (err: any) {
      setErrorMessage(err?.message || 'Ошибка восстановления конфигурации CS2')
    } finally {
      setIsRestoringConfig(false)
    }
  }

  return (
    <div style={{ maxWidth: '960px', margin: '0 auto', padding: '32px 20px' }}>
      <h1 style={{ fontSize: '24px', fontWeight: 800, color: '#f1f5f9', letterSpacing: '-0.02em', marginBottom: '8px' }}>
        {t('settings.title')}
      </h1>
      <p style={{ fontSize: '13px', color: '#94a3b8', marginBottom: '28px' }}>
        {t('settings.subtitle')}
      </p>

      {saveMessage && (
        <div style={{ padding: '12px 16px', backgroundColor: 'rgba(34, 197, 94, 0.1)', border: '1px solid #22c55e', borderRadius: '8px', color: '#4ade80', fontSize: '13px', marginBottom: '20px' }}>
          {saveMessage}
        </div>
      )}

      {errorMessage && (
        <div style={{ padding: '12px 16px', backgroundColor: 'rgba(239, 68, 68, 0.1)', border: '1px solid #ef4444', borderRadius: '8px', color: '#f87171', fontSize: '13px', marginBottom: '20px' }}>
          {errorMessage}
        </div>
      )}

      {/* Section 1: Output Directory */}
      <div
        style={{
          backgroundColor: '#12141a',
          border: '1px solid #232734',
          borderRadius: '10px',
          padding: '24px',
          marginBottom: '24px',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ fontSize: '15px', fontWeight: 700, color: '#f1f5f9' }}>
              {t('settings.outputDirTitle')}
            </div>
            <div style={{ fontSize: '12px', color: '#64748b', marginTop: '2px' }}>
              {t('settings.outputDirDesc')}
            </div>
          </div>

          <span
            style={{
              padding: '3px 8px',
              borderRadius: '4px',
              fontSize: '11px',
              fontWeight: 700,
              backgroundColor: isWritable ? 'rgba(34, 197, 94, 0.15)' : 'rgba(239, 68, 68, 0.15)',
              color: isWritable ? '#4ade80' : '#ef4444',
              border: isWritable ? '1px solid rgba(34, 197, 94, 0.3)' : '1px solid rgba(239, 68, 68, 0.3)',
            }}
          >
            {isWritable ? t('settings.writable') : t('settings.writeError')}
          </span>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <input
            type="text"
            className="input"
            value={outputDir}
            onChange={(e) => setOutputDir(e.target.value)}
            placeholder="C:\Users\...\Videos\CS2_Highlights"
            style={{ flex: 1, fontFamily: 'monospace', fontSize: '13px' }}
          />

          <button
            type="button"
            className="btn btn-primary"
            onClick={handleSaveDirectory}
            disabled={isSaving}
          >
            {isSaving ? t('settings.savingPath') : t('settings.savePath')}
          </button>

          <button
            type="button"
            className="btn btn-secondary"
            onClick={handleOpenExplorer}
            title="Открыть папку в Проводнике Windows"
          >
            📁 {t('common.explorer')}
          </button>
        </div>
      </div>

      {/* Section 2: CS2 Configuration Shield & Restoration */}
      <div
        style={{
          backgroundColor: '#12141a',
          border: '1px solid #232734',
          borderRadius: '10px',
          padding: '24px',
          marginBottom: '24px',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ fontSize: '15px', fontWeight: 700, color: '#f1f5f9' }}>
              {t('settings.shieldTitle')}
            </div>
            <div style={{ fontSize: '12px', color: '#64748b', marginTop: '2px' }}>
              {t('settings.shieldDesc')}
            </div>
          </div>

          <span
            style={{
              padding: '3px 8px',
              borderRadius: '4px',
              fontSize: '11px',
              fontWeight: 700,
              backgroundColor: 'rgba(34, 197, 94, 0.15)',
              color: '#4ade80',
              border: '1px solid rgba(34, 197, 94, 0.3)',
            }}
          >
            ✓ Защита активна
          </span>
        </div>

        <div style={{ fontSize: '12px', color: '#94a3b8', lineHeight: '1.6', backgroundColor: '#0d0f14', padding: '14px 16px', borderRadius: '8px', border: '1px solid #1e2230' }}>
          <div style={{ color: '#cbd5e1', fontWeight: 600, marginBottom: '4px' }}>🛡️ 4 уровня защиты:</div>
          <ul style={{ margin: '0 0 0 16px', padding: 0 }}>
            <li><strong>Read-Only Lock:</strong> Конфиги Steam блокируются на уровне Windows перед рендером — CS2 не может перезаписать ваш конфиг при выходе.</li>
            <li><strong>In-Engine Auto-Revert:</strong> Перед выходом CS2 в игре автоматически откатываются радар, HUD и громкость в боевой режим.</li>
            <li><strong>Autoexec:</strong> Скрипт <code>autoexec.cfg</code> в папке CS2 гарантирует применение ваших настроек при каждом обычном запуске игры.</li>
            <li><strong>Ручное восстановление:</strong> В консоли CS2 в любой момент можно написать <code>exec restore_user</code>.</li>
          </ul>
        </div>

        {configRestoreReport && (
          <div style={{ padding: '10px 14px', backgroundColor: 'rgba(34, 197, 94, 0.1)', border: '1px solid rgba(34, 197, 94, 0.3)', borderRadius: '6px', color: '#4ade80', fontSize: '12px' }}>
            {configRestoreReport}
          </div>
        )}

        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <button
            type="button"
            className="btn btn-primary"
            onClick={handleRestoreCS2Config}
            disabled={isRestoringConfig}
            style={{ fontSize: '13px' }}
          >
            {isRestoringConfig ? t('settings.restoring') : `🛡️ ${t('settings.restoreBtn')}`}
          </button>
          <span style={{ fontSize: '12px', color: '#64748b' }}>
            Очистит демо-бинды, вернет вращающийся радар и синхронизирует профиль Steam.
          </span>
        </div>

        {configStatus && (
          <div style={{ display: 'flex', gap: '8px', fontSize: '11px', color: '#64748b', marginTop: '-4px' }}>
            <span>autoexec.cfg: {configStatus.has_autoexec ? '✓ активен' : '—'}</span>
            <span>•</span>
            <span>restore_user.cfg: {configStatus.has_restore_user ? '✓ готов' : '—'}</span>
          </div>
        )}
      </div>

      {/* Section 3: Temporary Cache & Disk Maintenance */}
      <div
        style={{
          backgroundColor: '#12141a',
          border: '1px solid #232734',
          borderRadius: '10px',
          padding: '24px',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
        }}
      >
        <div>
          <div style={{ fontSize: '15px', fontWeight: 700, color: '#f1f5f9' }}>
            {t('settings.cleanupTitle')}
          </div>
          <div style={{ fontSize: '12px', color: '#64748b', marginTop: '2px' }}>
            {t('settings.cleanupDesc')}
          </div>
        </div>

        {cleanReport && (
          <div style={{ padding: '10px 14px', backgroundColor: 'rgba(56, 189, 248, 0.1)', border: '1px solid rgba(56, 189, 248, 0.3)', borderRadius: '6px', color: '#38bdf8', fontSize: '12px' }}>
            {cleanReport}
          </div>
        )}

        <div>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={handleCleanupTemp}
            disabled={isCleaning}
            style={{ fontSize: '12px' }}
          >
            {isCleaning ? t('settings.cleaning') : `🧹 ${t('settings.cleanupBtn')}`}
          </button>
        </div>
      </div>
    </div>
  )
}

