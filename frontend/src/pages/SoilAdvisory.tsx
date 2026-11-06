import { useState } from 'react'
import {
  fetchSoilAdvisory,
  type SoilAdvisoryResponse,
} from '../services/api'

export default function SoilAdvisory() {
  const [form, setForm] = useState({
    nitrogen: '90',
    phosphorus: '42',
    potassium: '43',
    ph: '6.5',
    soil_type: 'Loamy',
    crop: 'Rice',
    location: 'Salem',
  })

  const [result, setResult] = useState<SoilAdvisoryResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  function handleChange(
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
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
      const response = await fetchSoilAdvisory({
        nitrogen: Number(form.nitrogen),
        phosphorus: Number(form.phosphorus),
        potassium: Number(form.potassium),
        ph: Number(form.ph),
        soil_type: form.soil_type,
        crop: form.crop,
        location: form.location.trim(),
      })

      setResult(response)
    } catch (err) {
      console.error('Soil advisory failed:', err)
      setError('Unable to generate soil advisory. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const fields = [
    { name: 'nitrogen', label: 'Nitrogen (N)', unit: 'mg/kg' },
    { name: 'phosphorus', label: 'Phosphorus (P)', unit: 'mg/kg' },
    { name: 'potassium', label: 'Potassium (K)', unit: 'mg/kg' },
    { name: 'ph', label: 'Soil pH', unit: '0–14' },
  ]

  function renderAdvisory(text: string) {
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

  return (
    <div className="min-h-screen bg-green-50 p-4 md:p-8">
      <div className="mx-auto max-w-5xl">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-green-800">
            🌱 AI Soil Advisory
          </h1>
          <p className="mt-2 text-gray-600">
            Analyze your soil conditions and receive AI-powered soil improvement advice.
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="rounded-2xl border bg-white p-6 shadow-sm"
        >
          <h2 className="mb-5 text-xl font-semibold text-gray-800">
            Soil Information
          </h2>

          <div className="mb-5 grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">
                Location
              </label>
              <input
                name="location"
                value={form.location}
                onChange={handleChange}
                required
                maxLength={100}
                className="w-full rounded-lg border px-4 py-3"
              />
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">
                Soil Type
              </label>
              <select
                name="soil_type"
                value={form.soil_type}
                onChange={handleChange}
                className="w-full rounded-lg border bg-white px-4 py-3"
              >
                <option>Loamy</option>
                <option>Clay</option>
                <option>Sandy</option>
                <option>Silty</option>
                <option>Clay Loam</option>
                <option>Sandy Loam</option>
              </select>
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">
                Current Crop
              </label>
              <input
                name="crop"
                value={form.crop}
                onChange={handleChange}
                required
                maxLength={100}
                className="w-full rounded-lg border px-4 py-3"
                placeholder="e.g. Rice"
              />
            </div>

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
                  min="0"
                  max={field.name === 'ph' ? 14 : 300}
                  step="any"
                  className="w-full rounded-lg border px-4 py-3"
                />
              </div>
            ))}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-green-700 px-6 py-3 font-semibold text-white hover:bg-green-800 disabled:opacity-50"
          >
            {loading ? '🌱 Analyzing Soil...' : 'Get Soil Advisory'}
          </button>

          <p className="mt-3 text-xs text-gray-500">
            Use actual soil laboratory measurements wherever possible.
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
              🌾 Soil Advisory for {result.location}
            </h2>

            <div className="mt-5 text-sm text-gray-700">
              {renderAdvisory(result.advisory)}
            </div>

            <div className="mt-5 border-t pt-4 text-xs text-gray-500">
              <p>AI Model: {result.model_id}</p>
              <p>Generation time: {result.latency_seconds}s</p>
            </div>

            <p className="mt-4 rounded-lg bg-yellow-50 p-3 text-xs text-yellow-800">
              This is general AI-generated guidance, not a certified soil
              assessment. Verify fertilizer and soil treatment decisions with
              a soil testing laboratory or local agricultural expert.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}