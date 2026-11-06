import { useState } from 'react'
import {
  fetchCropRecommendation,
  type CropRecommendationResponse,
} from '../services/api'

function renderRecommendation(text: string) {
  const normalized = text.replace(/\\\*/g, '*')

  return normalized.split('\n').map((line, index) => {
    const parts = line.split(/(\*\*.*?\*\*)/g)

    return (
      <p key={index} className="mb-2 leading-7">
        {parts.map((part, i) =>
          part.startsWith('**') && part.endsWith('**') ? (
            <strong key={i} className="font-semibold text-green-800">
              {part.slice(2, -2)}
            </strong>
          ) : (
            part
          )
        )}
      </p>
    )
  })
}

export default function CropRecommendation() {
  const [form, setForm] = useState({
    nitrogen: '90',
    phosphorus: '42',
    potassium: '43',
    temperature: '25',
    humidity: '80',
    ph: '6.5',
    rainfall: '200',
    location: 'Salem',
  })

  const [result, setResult] =
    useState<CropRecommendationResponse | null>(null)

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  function handleChange(
    e: React.ChangeEvent<HTMLInputElement>
  ) {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()

    if (loading) return

    setLoading(true)
    setError('')
    setResult(null)

    try {
      const response = await fetchCropRecommendation({
        nitrogen: Number(form.nitrogen),
        phosphorus: Number(form.phosphorus),
        potassium: Number(form.potassium),
        temperature: Number(form.temperature),
        humidity: Number(form.humidity),
        ph: Number(form.ph),
        rainfall: Number(form.rainfall),
        location: form.location.trim(),
      })

      setResult(response)
    } catch (err) {
      console.error('Crop recommendation failed:', err)
      setError('Unable to generate crop recommendations. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const fields = [
    { name: 'nitrogen', label: 'Nitrogen (N)', unit: 'mg/kg' },
    { name: 'phosphorus', label: 'Phosphorus (P)', unit: 'mg/kg' },
    { name: 'potassium', label: 'Potassium (K)', unit: 'mg/kg' },
    { name: 'temperature', label: 'Temperature', unit: '°C' },
    { name: 'humidity', label: 'Humidity', unit: '%' },
    { name: 'ph', label: 'Soil pH', unit: '0–14' },
    { name: 'rainfall', label: 'Rainfall', unit: 'mm' },
  ]

  return (
    <div className="min-h-screen bg-green-50 p-4 md:p-8">
      <div className="mx-auto max-w-5xl">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-green-800">
            🌱 AI Crop Recommendation
          </h1>
          <p className="mt-2 text-gray-600">
            Enter soil and climate details to receive AI-powered crop suggestions.
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="rounded-2xl border bg-white p-6 shadow-sm"
        >
          <h2 className="mb-5 text-xl font-semibold text-gray-800">
            Farming Conditions
          </h2>

          <div className="mb-5">
            <label className="mb-2 block text-sm font-medium text-gray-700">
              Location
            </label>
            <input
              name="location"
              value={form.location}
              onChange={handleChange}
              required
              maxLength={100}
              className="w-full rounded-lg border px-4 py-3 outline-none focus:border-green-600"
              placeholder="Enter your location"
            />
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {fields.map((field) => (
              <div key={field.name}>
                <label className="mb-2 block text-sm font-medium text-gray-700">
                  {field.label} ({field.unit})
                </label>
                <input
                  type="number"
                  name={field.name}
                  value={form[field.name as keyof typeof form]}
                  onChange={handleChange}
                  required
                  step="any"
                  className="w-full rounded-lg border px-4 py-3 outline-none focus:border-green-600"
                />
              </div>
            ))}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="mt-6 w-full rounded-xl bg-green-700 px-6 py-3 font-semibold text-white hover:bg-green-800 disabled:opacity-50"
          >
            {loading ? '🌱 Analyzing...' : 'Get Crop Recommendations'}
          </button>

          <p className="mt-3 text-xs text-gray-500">
            Enter actual soil test and local climate measurements where available.
            Default values are examples only.
          </p>
        </form>

        {error && (
          <div className="mt-5 rounded-xl border border-red-200 bg-red-50 p-4 text-red-700">
            {error}
          </div>
        )}

        {result && (
          <div className="mt-6 rounded-2xl border bg-white p-6 shadow-sm">
            <h2 className="text-xl font-bold text-green-800">
              🌾 Recommended Crops for {result.location}
            </h2>

            <div className="mt-5 text-sm text-gray-700">
  {renderRecommendation(result.recommendation)}
</div>

            <div className="mt-5 border-t pt-4 text-xs text-gray-500">
              <p>AI Model: {result.model_id}</p>
              <p>Generation time: {result.latency_seconds}s</p>
            </div>

            <p className="mt-4 rounded-lg bg-yellow-50 p-3 text-xs text-yellow-800">
              These are AI-generated suggestions, not guaranteed agricultural
              outcomes. Verify recommendations with local agricultural experts
              before planting.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}