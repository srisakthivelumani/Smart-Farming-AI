
import { Link, useLocation } from 'react-router-dom'

const navLinks = [
  { to: '/', label: 'Home' },
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/granite', label: 'IBM Granite' },
  { to: '/chat', label: 'AI Chat' },
  { to: '/weather', label: 'Weather' },
  { to: '/crop-recommendation', label: 'Crop Recommendation' },
  { to: '/soil-advisory', label: 'Soil Advisory' },
  { to: '/pest-disease', label: 'Pest & Disease' },
  { to: '/mandi-prices', label: 'Mandi Prices' },
  { to: '/knowledge-base', label: 'Knowledge Base' },
]

export default function Navbar() {
  const { pathname } = useLocation()

  return (
    <nav className="bg-green-800 text-white shadow-md">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex min-h-16 flex-wrap items-center justify-between gap-3 py-3">
          <Link
            to="/"
            className="flex items-center gap-2 text-xl font-bold tracking-tight"
          >
            <span className="text-2xl">🌾</span>
            <span>Smart Farming AI</span>
          </Link>

          <div className="flex flex-wrap items-center gap-1">
            {navLinks.map(({ to, label }) => (
              <Link
                key={to}
                to={to}
                className={`rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                  pathname === to
                    ? 'bg-green-600 text-white'
                    : 'text-green-100 hover:bg-green-700'
                }`}
              >
                {label}
              </Link>
            ))}
          </div>

          <div className="flex items-center gap-2 text-xs text-green-200">
            <span className="inline-block h-2 w-2 rounded-full bg-green-400" />
            Powered by IBM Granite
          </div>
        </div>
      </div>
    </nav>
  )
}

