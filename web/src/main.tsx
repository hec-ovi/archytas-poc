import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { App } from './App'
import './styles/tokens.css'
import './styles/base.css'
import './styles/layout.css'
import './styles/componentes.css'

const raiz = document.getElementById('root')
if (!raiz) throw new Error('Falta el nodo #root')

createRoot(raiz).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
