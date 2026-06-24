type BeforeInstallPromptEvent = Event & {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed'; platform: string }>
}

let deferredInstallPrompt: BeforeInstallPromptEvent | null = null
let installButton: HTMLButtonElement | null = null

function removeInstallButton() {
  installButton?.remove()
  installButton = null
}

function createInstallButton() {
  if (installButton) return

  installButton = document.createElement('button')
  installButton.type = 'button'
  installButton.textContent = 'Install app'
  installButton.setAttribute('aria-label', 'Install SoberanIA Labs Local RAG')
  installButton.style.position = 'fixed'
  installButton.style.right = '1rem'
  installButton.style.bottom = '1rem'
  installButton.style.zIndex = '20'
  installButton.style.boxShadow = '0 12px 36px rgba(0, 0, 0, 0.2)'

  installButton.addEventListener('click', async () => {
    if (!deferredInstallPrompt) return

    const promptEvent = deferredInstallPrompt
    deferredInstallPrompt = null
    await promptEvent.prompt()
    await promptEvent.userChoice
    removeInstallButton()
  })

  document.body.appendChild(installButton)
}

function registerInstallPrompt() {
  window.addEventListener('beforeinstallprompt', (event) => {
    event.preventDefault()
    deferredInstallPrompt = event as BeforeInstallPromptEvent
    createInstallButton()
  })

  window.addEventListener('appinstalled', () => {
    deferredInstallPrompt = null
    removeInstallButton()
  })
}

export function registerServiceWorker() {
  registerInstallPrompt()

  if (!('serviceWorker' in navigator)) return
  if (!import.meta.env.PROD) return

  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/service-worker.js').catch((error: unknown) => {
      console.warn('Service worker registration failed', error)
    })
  })
}
