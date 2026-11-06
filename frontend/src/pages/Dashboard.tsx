import { Link } from 'react-router-dom'

const phases = [
  { phase: 1, label: 'Foundation & IBM Integration', status: 'active',   icon: '✅' },
  { phase: 2, label: 'RAG Knowledge Base',           status: 'pending',  icon: '⏳' },
  { phase: 3, label: 'AI Chatbot + Tamil Support',   status: 'pending',  icon: '⏳' },
  { phase: 4, label: 'Weather & Crop Features',      status: 'pending',  icon: '⏳' },
  { phase: 5, label: 'Soil, Pest & Mandi',           status: 'pending',  icon: '⏳' },
  { phase: 6, label: 'Dashboard Polish & Validation',status: 'pending',  icon: '⏳' },
]

export default function Dashboard() {
  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <h1 className="text-farmer-heading mb-2">Farmer Dashboard</h1>
      <p className="text-gray-500 mb-8 text-sm">
        Phase 1 in progress — IBM Granite integration and foundation scaffolding.
      </p>

      {/* Phase status grid */}
      <section className="mb-10">
        <h2 className="text-lg font-bold text-green-800 mb-4">Implementation Progress</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {phases.map(({ phase, label, status, icon }) => (
            <div
              key={phase}
              className={`rounded-xl border p-4 ${
                status === 'active'
                  ? 'bg-green-50 border-green-300'
                  : 'bg-white border-gray-200 opacity-60'
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                <span>{icon}</span>
                <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                  Phase {phase}
                </span>
              </div>
              <p className="font-semibold text-green-900 text-sm">{label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Quick actions */}
      <section>
        <h2 className="text-lg font-bold text-green-800 mb-4">Quick Actions</h2>
        <div className="flex flex-wrap gap-3">
          <Link
            to="/granite-status"
            className="bg-green-700 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-green-800 transition-colors"
          >
            🔬 Test IBM Granite Connection
          </Link>
        </div>
        <p className="text-xs text-gray-400 mt-3">
          More features will appear here as each phase is completed.
        </p>
      </section>
    </div>
  )
}
