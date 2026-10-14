import { useEffect, useState } from 'react'
import { api } from '../api'

export function SettingsView() {
  const [outputDir, setOutputDir] = useState('')
  const [isWritable, setIsWritable] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [saveMessage, setSaveMessage] = useState<string | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const [isCleaning, setIsCleaning] = useState(false)
  const [cleanReport, setCleanReport] = useState<string | null>(null)

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

  return (
    <div style={{ maxWidth: '960px', margin: '0 auto', padding: '32px 20px' }}>
      <h1 style={{ fontSize: '24px', fontWeight: 800, color: '#f1f5f9', letterSpacing: '-0.02em', marginBottom: '8px' }}>
        Настройки приложения и хранилища
      </h1>
      <p style={{ fontSize: '13px', color: '#94a3b8', marginBottom: '28px' }}>
        Управление каталогами сохранения, правами записи, очисткой временных файлов и профилями рендера.
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
              Папка для сохранения роликов и монтажей
            </div>
            <div style={{ fontSize: '12px', color: '#64748b', marginTop: '2px' }}>
              Сюда записываются все итоговые MP4 хайлайты и объединенные клипы.
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
            {isWritable ? '✓ Доступна для записи' : '✕ Ошибка записи'}
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
            {isSaving ? 'Сохранение...' : 'Сохранить путь'}
          </button>

          <button
            type="button"
            className="btn btn-secondary"
            onClick={handleOpenExplorer}
            title="Открыть папку в Проводнике Windows"
          >
            📁 Проводник
          </button>
        </div>
      </div>

      {/* Section 2: Temporary Cache & Disk Maintenance */}
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
            Очистка диска и временных файлов
          </div>
          <div style={{ fontSize: '12px', color: '#64748b', marginTop: '2px' }}>
            Удаляет промежуточные несжатые звуковые дорожки (.wav), вспомогательные тейки HLAE и временные конфиги, освобождая дисковое пространство. Готовые ролики (.mp4) никогда не удаляются.
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
            {isCleaning ? 'Очистка...' : '🧹 Очистить временные файлы захвата'}
          </button>
        </div>
      </div>
    </div>
  )
}

