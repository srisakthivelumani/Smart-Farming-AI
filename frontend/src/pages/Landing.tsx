import { Link } from 'react-router-dom'

const features = [
  { icon: '🤖', title: 'AI Farming Chatbot',      desc: 'Ask questions in Tamil or English. Powered by IBM Granite.' },
  { icon: '🌱', title: 'Crop Recommendation',     desc: 'Location, season, soil and weather-aware advice.' },
  { icon: '🌤️', title: 'Weather Advisory',        desc: 'Live forecasts with farming-specific guidance.' },
  { icon: '🧪', title: 'Soil & Fertilizer',       desc: 'Science-backed recommendations from trusted sources.' },
  { icon: '🐛', title: 'Pest & Disease Advisory', desc: 'Safe, source-backed pest management guidance.' },
  { icon: '📈', title: 'Mandi Price Tracker',     desc: 'Live market prices from verified government data.' },
]

export default function Landing() {
  return (
    <div className="flex flex-col">
      {/* Hero */}
      <section className="bg-green-800 text-white py-20 px-4 text-center">
        <h1 className="text-4xl sm:text-5xl font-bold mb-4">
          AI-Powered Smart Farming
        </h1>
        <p className="text-xl text-green-100 max-w-2xl mx-auto mb-8">
          Expert agricultural guidance for Indian farmers — in Tamil and English.
          Backed by IBM Granite and verified agricultural knowledge.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            to="/dashboard"
            className="bg-white text-green-800 font-semibold px-8 py-3 rounded-lg hover:bg-green-50 transition-colors"
          >
            Go to Dashboard
          </Link>
          <Link
            to="/granite-status"
            className="border border-white text-white font-semibold px-8 py-3 rounded-lg hover:bg-green-700 transition-colors"
          >
            Check IBM Granite Status
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="max-w-7xl mx-auto px-4 py-16 w-full">
        <h2 className="text-2xl font-bold text-green-800 text-center mb-10">
          Features
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map(({ icon, title, desc }) => (
            <div
              key={title}
              className="bg-white rounded-xl border border-green-100 p-6 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="text-3xl mb-3">{icon}</div>
              <h3 className="font-bold text-green-800 mb-2">{title}</h3>
              <p className="text-gray-600 text-sm">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Disclaimer */}
      <section className="bg-amber-50 border-t border-amber-200 py-8 px-4 text-center">
        <p className="text-amber-800 text-sm max-w-2xl mx-auto">
          ⚠️ All AI-generated advice is for informational purposes only.
          Verify recommendations with a local agricultural officer before making
          farming decisions. Live data is clearly labelled — this platform never
          fabricates weather, soil, or market price data.
        </p>
      </section>
    </div>
  )
}
