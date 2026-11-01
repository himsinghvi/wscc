import { useEffect, useState } from 'react'

// Feature 10: browsers fire `beforeinstallprompt`; we capture it and offer a
// "Download app" button. Installing opens the same web app in a standalone
// window. On iOS (no event) we show a hint to use Share → Add to Home Screen.
export default function InstallPrompt({ compact = false }) {
  const [deferred, setDeferred] = useState(null)
  const [installed, setInstalled] = useState(
    window.matchMedia('(display-mode: standalone)').matches)

  useEffect(() => {
    const onPrompt = (e) => { e.preventDefault(); setDeferred(e) }
    const onInstalled = () => setInstalled(true)
    window.addEventListener('beforeinstallprompt', onPrompt)
    window.addEventListener('appinstalled', onInstalled)
    return () => {
      window.removeEventListener('beforeinstallprompt', onPrompt)
      window.removeEventListener('appinstalled', onInstalled)
    }
  }, [])

  if (installed) return null

  const install = async () => {
    if (!deferred) {
      alert('To install: use your browser menu → "Install app" / "Add to Home Screen".')
      return
    }
    deferred.prompt()
    await deferred.userChoice
    setDeferred(null)
  }

  if (compact) {
    return (
      <button className="btn btn-sm btn-primary" onClick={install} title="Install app">
        <i className="bi bi-download" />
      </button>
    )
  }

  return (
    <button className="btn btn-primary w-100 mt-2" onClick={install}>
      <i className="bi bi-download me-1" /> Download app
    </button>
  )
}
