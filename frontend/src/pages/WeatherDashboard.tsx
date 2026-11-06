
import { useState } from 'react'
import { fetchWeather, type WeatherResponse } from '../services/api'

export default function WeatherDashboard() {
  const [location, setLocation] = useState('Salem')
  const [weather, setWeather] = useState<WeatherResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSearch(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()

    if (!location.trim() || loading) return

    setLoading(true)
    setError('')

    try {
      const result = await fetchWeather(location.trim())
      setWeather(result)
    } catch (err) {
      console.error('Weather request failed:', err)
      setError('Unable to retrieve weather. Check the city name and try again.')
      setWeather(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-green-50 p-4 md:p-8">
      <div className="mx-auto max-w-5xl">

        <div className="mb-6">
          <h1 className="text-3xl font-bold text-green-800">
            🌦️ Weather Dashboard
          </h1>
          <p className="mt-2 text-gray-600">
            Live weather information for farming decisions
          </p>
        </div>

        <form onSubmit={handleSearch} className="mb-6 flex gap-2">
          <input
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="Enter city name..."
            className="min-w-0 flex-1 rounded-xl border border-gray-300 bg-white px-4 py-3 outline-none focus:border-green-600"
          />

          <button
            type="submit"
            disabled={loading || !location.trim()}
            className="rounded-xl bg-green-700 px-6 py-3 font-medium text-white hover:bg-green-800 disabled:opacity-50"
          >
            {loading ? 'Loading...' : 'Search'}
          </button>
        </form>

        {error && (
          <div className="mb-5 rounded-xl border border-red-200 bg-red-50 p-4 text-red-700">
            {error}
          </div>
        )}

        {weather && (
          <div className="space-y-5">

            <div className="rounded-2xl bg-green-700 p-6 text-white shadow-lg">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="text-xl font-semibold">
                    {weather.location}, {weather.country}
                  </h2>
                  <p className="mt-1 capitalize text-green-100">
                    {weather.description}
                  </p>
                </div>

                <span className="rounded-full bg-white/20 px-3 py-1 text-xs font-semibold">
                  {weather.data_status}
                </span>
              </div>

              <div className="mt-6">
                <p className="text-5xl font-bold">
                  {weather.temperature_c.toFixed(1)}°C
                </p>
                <p className="mt-2 text-green-100">
                  Feels like {weather.feels_like_c.toFixed(1)}°C
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">

              {[
                {
                  label: 'Humidity',
                  value: `${weather.humidity_percent}%`,
                  icon: '💧',
                },
                {
                  label: 'Wind Speed',
                  value: `${weather.wind_speed_mps} m/s`,
                  icon: '💨',
                },
                {
                  label: 'Pressure',
                  value: `${weather.pressure_hpa} hPa`,
                  icon: '🌡️',
                },
                {
                  label: 'Cloudiness',
                  value: `${weather.cloudiness_percent}%`,
                  icon: '☁️',
                },
                {
                  label: 'Temperature',
                  value: `${weather.temperature_c.toFixed(1)}°C`,
                  icon: '🌞',
                },
                {
                  label: 'Weather',
                  value: weather.weather,
                  icon: '🌦️',
                },
              ].map((item) => (
                <div
                  key={item.label}
                  className="rounded-xl border border-green-100 bg-white p-5 shadow-sm"
                >
                  <p className="text-sm text-gray-500">
                    {item.icon} {item.label}
                  </p>
                  <p className="mt-2 text-2xl font-bold text-gray-800">
                    {item.value}
                  </p>
                </div>
              ))}

            </div>

            <p className="text-center text-xs text-gray-500">
              Weather data provided by OpenWeatherMap.
              Weather observations are not a forecast.
            </p>
          </div>
        )}

        {!weather && !loading && !error && (
          <div className="rounded-xl border border-dashed border-green-300 bg-white p-10 text-center text-gray-500">
            Search for a city to view its current weather.
          </div>
        )}

      </div>
    </div>
  )
}
