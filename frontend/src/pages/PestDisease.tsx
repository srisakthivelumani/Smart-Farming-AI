
import { useState } from 'react'
import {
  fetchPestAdvisory,
  type PestAdvisoryResponse,
} from '../services/api'

function PestDisease() {
  const [crop, setCrop] = useState('Rice')
  const [symptoms, setSymptoms] = useState('')
  const [affectedPart, setAffectedPart] = useState('Leaves')
  const [duration, setDuration] = useState('')
  const [location, setLocation] = useState('Salem')

  const [result, setResult] = useState<PestAdvisoryResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setLoading(true)
    setError('')
    setResult(null)

    try {
      const data = await fetchPestAdvisory({
        crop,
        symptoms,
        affected_part: affectedPart,
        duration,
        location,
      })
      setResult(data)
    } catch {
      setError('Unable to generate advisory. Please check the backend and try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-green-50 px-4 py-10">
      <div className="mx-auto max-w-4xl">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-green-900">
            Pest & Disease Advisory
          </h1>
          <p className="mt-2 text-gray-600">
            Describe your crop symptoms to receive AI-powered agricultural guidance.
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="space-y-5 rounded-2xl bg-white p-6 shadow-md"
        >
          <div>
            <label className="mb-2 block font-medium text-gray-700">
              Crop Name
            </label>
            <input
              value={crop}
              onChange={(e) => setCrop(e.target.value)}
              required
              minLength={2}
              maxLength={100}
              placeholder="Example: Rice"
              className="w-full rounded-lg border border-gray-300 p-3 outline-none focus:border-green-600"
            />
          </div>

          <div>
            <label className="mb-2 block font-medium text-gray-700">
              Symptoms
            </label>
            <textarea
              value={symptoms}
              onChange={(e) => setSymptoms(e.target.value)}
              required
              minLength={5}
              maxLength={2000}
              rows={4}
              placeholder="Describe leaf spots, yellowing, holes, insects, or other symptoms..."
              className="w-full rounded-lg border border-gray-300 p-3 outline-none focus:border-green-600"
            />
          </div>

          <div>
            <label className="mb-2 block font-medium text-gray-700">
              Affected Plant Part
            </label>
            <select
              value={affectedPart}
              onChange={(e) => setAffectedPart(e.target.value)}
              className="w-full rounded-lg border border-gray-300 p-3"
            >
              <option>Leaves</option>
              <option>Stem</option>
              <option>Roots</option>
              <option>Flowers</option>
              <option>Fruits</option>
              <option>Entire Plant</option>
            </select>
          </div>

          <div>
            <label className="mb-2 block font-medium text-gray-700">
              How Long Have You Observed These Symptoms?
            </label>
            <input
              value={duration}
              onChange={(e) => setDuration(e.target.value)}
              required
              maxLength={100}
              placeholder="Example: 5 days"
              className="w-full rounded-lg border border-gray-300 p-3"
            />
          </div>

          <div>
            <label className="mb-2 block font-medium text-gray-700">
              Location
            </label>
            <input
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              required
              maxLength={100}
              placeholder="Example: Salem"
              className="w-full rounded-lg border border-gray-300 p-3"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-green-700 px-5 py-3 font-semibold text-white transition hover:bg-green-800 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? 'Generating Advisory...' : 'Get Pest Advisory'}
          </button>
        </form>

        {error && (
          <div className="mt-6 rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
            {error}
          </div>
        )}

        {result && (
          <div className="mt-8 rounded-2xl border border-green-200 bg-white p-6 shadow-md">
            <h2 className="mb-4 text-2xl font-bold text-green-900">
              AI Pest Advisory
            </h2>

            <div className="whitespace-pre-wrap leading-8 text-gray-700">
              {result.advisory}
            </div>

            <div className="mt-6 border-t pt-4 text-sm text-gray-500">
              <p>Location: {result.location}</p>
              <p>AI Model: {result.model_id}</p>
              <p>Response Time: {result.latency_seconds.toFixed(2)} seconds</p>
            </div>
          </div>
        )}

        <p className="mt-6 text-center text-sm text-gray-500">
          Disclaimer: AI suggestions are preliminary guidance, not a confirmed
          diagnosis. Field inspection by an agricultural expert is required.
          Follow locally approved agricultural recommendations.
        </p>
      </div>
    </div>
  )
}

export default PestDisease
