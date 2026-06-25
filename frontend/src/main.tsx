import React from 'react'
import ReactDOM from 'react-dom/client'

import App from './App'
import { LauncherPanel } from './LauncherPanel'
import { registerServiceWorker } from './pwa'
import './styles.css'
import './workspace.css'
import './launcher.css'

registerServiceWorker()

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App />
    <LauncherPanel />
  </React.StrictMode>,
)
