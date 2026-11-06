
import { useState } from 'react'
import {
  fetchMandiPrices,
  type MandiPriceResponse,
} from '../services/api'

function MandiPrices() {
  const [commodity, setCommodity] = useState('Rice')
  const [state, setState] = useState('Tamil Nadu')
  const [district, setDistrict] = useState('Salem')

  const [result, setResult] = useState<MandiPriceResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSearch(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()

    setLoading(true)
    setError('')
    setResult(null)

    try {
      const data = await fetchMandiPrices(
        commodity.trim(),
        state.trim(),
        district.trim()
      )
      setResult(data)
    } catch {
      setError(
        'Unable to contact the market price service. Please try again later.'
      )
    } finally {
      setLoading(false)
    }
  }

  function formatPrice(value?: string | number) {
    if (value === undefined || value === null || value === '') {
      return '—'
    }

    const numericValue = Number(value)

    if (!Number.isFinite(numericValue)) {
      return String(value)
    }

    return `₹${numericValue.toLocaleString('en-IN')}`
  }

  return (
    <div className="min-h-screen bg-green-50 px-4 py-10">
      <div className="mx-auto max-w-6xl">

        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-green-900">
            Mandi Market Prices
          </h1>
          <p className="mt-2 text-gray-600">
            Check agricultural commodity prices from government market data.
          </p>
        </div>

        <form
          onSubmit={handleSearch}
          className="grid gap-5 rounded-2xl bg-white p-6 shadow-md md:grid-cols-2"
        >
          <div>
            <label className="mb-2 block font-medium text-gray-700">
              Commodity
            </label>
            <input
              value={commodity}
              onChange={(e) => setCommodity(e.target.value)}
              required
              maxLength={100}
              placeholder="Example: Rice"
              className="w-full rounded-lg border border-gray-300 p-3"
            />
          </div>

          <div>
            <label className="mb-2 block font-medium text-gray-700">
              State
            </label>
            <input
              value={state}
              onChange={(e) => setState(e.target.value)}
              required
              maxLength={100}
              placeholder="Example: Tamil Nadu"
              className="w-full rounded-lg border border-gray-300 p-3"
            />
          </div>

          <div>
            <label className="mb-2 block font-medium text-gray-700">
              District
            </label>
            <input
              value={district}
              onChange={(e) => setDistrict(e.target.value)}
              required
              maxLength={100}
              placeholder="Example: Salem"
              className="w-full rounded-lg border border-gray-300 p-3"
            />
          </div>

          <div className="flex items-end">
            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-green-700 px-5 py-3 font-semibold text-white hover:bg-green-800 disabled:opacity-60"
            >
              {loading ? 'Searching...' : 'Search Market Prices'}
            </button>
          </div>
        </form>

        {error && (
          <div className="mt-6 rounded-xl border border-red-200 bg-red-50 p-5 text-red-700">
            <h2 className="font-semibold">Connection Error</h2>
            <p className="mt-1">{error}</p>
          </div>
        )}

        {result && (
          <div className="mt-8">

            <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
              <h2 className="text-xl font-bold text-green-900">
                Market Price Results
              </h2>

              <span
                className={`rounded-full px-4 py-2 text-sm font-semibold ${
                  result.data_status === 'LIVE'
                    ? 'bg-green-100 text-green-800'
                    : 'bg-yellow-100 text-yellow-800'
                }`}
              >
                {result.data_status}
              </span>
            </div>

            <div className="rounded-xl bg-white p-5 shadow-sm">
              <p className="text-gray-700">{result.message}</p>

              {result.data_status === 'LIVE' &&
                result.records.length > 0 && (
                  <div className="mt-5 overflow-x-auto">
                    <table className="w-full min-w-[850px] border-collapse text-left text-sm">
                      <thead>
                        <tr className="bg-green-100 text-green-900">
                          <th className="p-3">Market</th>
                          <th className="p-3">Commodity</th>
                          <th className="p-3">Variety</th>
                          <th className="p-3">Arrival Date</th>
                          <th className="p-3">Min Price</th>
                          <th className="p-3">Max Price</th>
                          <th className="p-3">Modal Price</th>
                        </tr>
                      </thead>

                      <tbody>
                        {result.records.map((record, index) => (
                          <tr
                            key={`${record.market ?? 'market'}-${record.arrival_date ?? index}-${index}`}
                            className="border-b hover:bg-green-50"
                          >
                            <td className="p-3">
                              {record.market || '—'}
                            </td>
                            <td className="p-3">
                              {record.commodity || '—'}
                            </td>
                            <td className="p-3">
                              {record.variety || '—'}
                            </td>
                            <td className="p-3">
                              {record.arrival_date || '—'}
                            </td>
                            <td className="p-3">
                              {formatPrice(record.min_price)}
                            </td>
                            <td className="p-3">
                              {formatPrice(record.max_price)}
                            </td>
                            <td className="p-3 font-semibold text-green-800">
                              {formatPrice(record.modal_price)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

              {result.data_status === 'LIVE' &&
                result.records.length === 0 && (
                  <p className="mt-4 text-gray-600">
                    No matching market records were found. Try another
                    commodity or location.
                  </p>
                )}

              {result.data_status === 'UNAVAILABLE' && (
                <div className="mt-5 rounded-lg border border-yellow-200 bg-yellow-50 p-4 text-yellow-900">
                  <p className="font-semibold">
                    Market data is temporarily unavailable.
                  </p>
                  <p className="mt-1 text-sm">
                    No market prices are being displayed because the
                    government data service did not return records.
                    Please try again later.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        <p className="mt-6 text-center text-sm text-gray-500">
          Source: data.gov.in. Market prices are reported observations,
          not guaranteed current transaction prices. Verify prices with
          the local mandi before making selling decisions.
        </p>
      </div>
    </div>
  )
}

export default MandiPrices
