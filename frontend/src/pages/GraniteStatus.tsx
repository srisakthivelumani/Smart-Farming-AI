import { useState } from 'react'
import { testGraniteConnection, type GraniteTestResponse } from '../services/api'

type TestState = 'idle' | 'loading' | 'done' | 'error'

export default function GraniteStatus() {
  const [state, setState] = useState<TestState>('idle')
  const [result, setResult] = useState<GraniteTestResponse | null>(null)
  const [networkError, setNetworkError] = useState<string | null>(null)

  async function runTest() {
    setState('loading')
    setResult(null)
    setNetworkError(null)
    try {
      const data = await testGraniteConnection()
      setResult(data)
      setState('done')
    } catch (err: unknown) {
      // Network-level error (backend unreachable, CORS, etc.)
      const msg = err instanceof Error ? err.message : String(err)
      setNetworkError(msg)
      setState('error')
    }
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="text-farmer-heading mb-2">IBM Granite Connection Test</h1>
      <p className="text-gray-500 text-sm mb-6">
        Sends a real inference request to IBM watsonx.ai. Reports credential
        status, model availability, latency, token usage, and a Tamil generation
        quality probe. The exact IBM error is shown if the test fails.
      </p>

      <button
        onClick={runTest}
        disabled={state === 'loading'}
        className="bg-green-700 text-white px-6 py-2 rounded-lg font-medium hover:bg-green-800 disabled:opacity-50 transition-colors mb-6"
      >
        {state === 'loading' ? '⏳ Testing (may take 10–20s on Lite tier)…' : '🔬 Run Connection Test'}
      </button>

      {/* Network-level error */}
      {state === 'error' && networkError && (
        <div className="bg-red-50 border border-red-300 rounded-lg p-4 mb-4">
          <h3 className="font-bold text-red-700 mb-1">Backend unreachable</h3>
          <p className="text-red-600 text-sm font-mono">{networkError}</p>
          <p className="text-red-500 text-xs mt-2">
            Make sure the FastAPI backend is running on port 8000.
          </p>
        </div>
      )}

      {/* IBM test result */}
      {result && (
        <div className="space-y-4">
          {/* Connection summary */}
          <div className={`rounded-lg border p-4 ${
            result.connection_test.success
              ? 'bg-green-50 border-green-300'
              : 'bg-red-50 border-red-300'
          }`}>
            <h3 className="font-bold mb-2 text-sm uppercase tracking-wide text-gray-600">
              Connection Test
            </h3>
            <div className="flex items-center gap-2 mb-1">
              <span className={`font-bold text-lg ${result.connection_test.success ? 'text-green-700' : 'text-red-700'}`}>
                {result.connection_test.success ? '✅ SUCCESS' : '❌ FAILED'}
              </span>
            </div>
            <p className="text-sm text-gray-700">
              <span className="font-medium">Model: </span>{result.connection_test.model_id}
            </p>
            <p className="text-sm text-gray-700">
              <span className="font-medium">Endpoint: </span>{result.connection_test.endpoint}
            </p>
            <p className="text-sm text-gray-700">
              <span className="font-medium">API Key configured: </span>
              {result.connection_test.credentials.api_key_configured ? 'Yes' : 'No ⚠️'}
            </p>
            <p className="text-sm text-gray-700">
              <span className="font-medium">Project ID configured: </span>
              {result.connection_test.credentials.project_id_configured ? 'Yes' : 'No ⚠️'}
            </p>
          </div>

          {/* IBM Error (if failed) */}
          {result.error && (
            <div className="bg-red-50 border border-red-300 rounded-lg p-4">
              <h3 className="font-bold text-red-700 mb-2">IBM Error Detail</h3>
              <p className="text-sm font-mono text-red-600 whitespace-pre-wrap">{result.error.ibm_error}</p>
              <p className="text-xs text-red-500 mt-2">{result.error.action}</p>
            </div>
          )}

          {/* Inference result (if success) */}
          {result.inference_result && (
            <div className="bg-white border border-green-200 rounded-lg p-4">
              <h3 className="font-bold text-green-800 mb-2 text-sm uppercase tracking-wide">
                English Inference Result
              </h3>
              <p className="text-sm text-gray-800 italic mb-3">"{result.inference_result.sample_response}"</p>
              <div className="flex flex-wrap gap-4 text-xs text-gray-500">
                <span>📥 Input tokens: <strong>{result.inference_result.input_tokens}</strong></span>
                <span>📤 Output tokens: <strong>{result.inference_result.output_tokens}</strong></span>
                <span>⏱ Latency: <strong>{result.inference_result.latency_seconds}s</strong></span>
              </div>
              <p className="text-xs text-amber-600 mt-2">{result.inference_result.note}</p>
            </div>
          )}

          {/* Tamil probe */}
          {result.tamil_generation_probe && (
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <h3 className="font-bold text-purple-800 mb-2 text-sm uppercase tracking-wide">
                Tamil Generation Probe (Experimental)
              </h3>
              {result.tamil_generation_probe.attempted ? (
                <>
                  <p className="text-sm text-gray-800 italic mb-2 whitespace-pre-wrap">
                    "{result.tamil_generation_probe.response || '(empty response)'}"
                  </p>
                  <p className="text-xs text-purple-600">{result.tamil_generation_probe.note}</p>
                  <p className="text-xs text-amber-600 mt-1">{result.tamil_generation_probe.disclaimer}</p>
                </>
              ) : (
                <p className="text-sm text-gray-500">{result.tamil_generation_probe.reason}</p>
              )}
            </div>
          )}
        </div>
      )}

      {state === 'idle' && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-sm text-gray-500">
          Click the button above to run a live inference test. Results will appear here.
          <br />
          <strong className="text-gray-700">Note:</strong> Granite on IBM Cloud Lite can take 10–20 seconds.
          This test consumes a small number of tokens from your monthly allowance.
        </div>
      )}
    </div>
  )
}
