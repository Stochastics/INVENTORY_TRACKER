import { API_BASE_URL } from './api.js'

function App() {
  return (
    <main className="app-shell">
      <section className="card">
        <p className="eyebrow">Inventory MVP</p>
        <h1>Mobile inventory scaffold</h1>
        <p>
          The React/Vite frontend is ready for the MVP screens that will be built in later milestones.
        </p>
        <p className="api-note">API base URL: {API_BASE_URL}</p>
      </section>
    </main>
  )
}

export default App
