/**
 * Centralised API client.
 * All backend calls go through this module — never call fetch/axios directly
 * from components. Use the typed functions below.
 */
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30_000, // 30 s — Granite on Lite can be slow
  headers: { 'Content-Type': 'application/json' },
})

// ── Response types ────────────────────────────────────────────────────────────

export interface HealthResponse {
  status: string
  app: string
  version: string
  granite: {
    configured: boolean
    model_id: string
    endpoint: string
    note: string
  }
  external_apis: {
    openweather: boolean
    datagov: boolean
  }
}

export interface GraniteTestResponse {
  connection_test: {
    success: boolean
    model_id: string
    endpoint: string
    credentials: {
      api_key_configured: boolean
      project_id_configured: boolean
    }
  }
  inference_result?: {
    sample_response: string
    input_tokens: number
    output_tokens: number
    latency_seconds: number
    note: string
  }
  error?: {
    type: string
    ibm_error: string
    action: string
  }
  tamil_generation_probe?: {
    attempted: boolean
    response?: string
    note?: string
    disclaimer?: string
    reason?: string
  }
}
export interface ChatRequest {
  question: string
  language: 'English' | 'Tamil'
}

export interface ChatSource {
  source: string
  page: number
  file_type: string
  score: number
}

export interface ChatResponse {
  question: string
  language: string
  answer: string
  sources: ChatSource[]
  context_used: boolean
  model_id: string
  latency_seconds: number
}

export interface WeatherResponse {
  location: string
  country: string
  temperature_c: number
  feels_like_c: number
  humidity_percent: number
  pressure_hpa: number
  weather: string
  description: string
  wind_speed_mps: number
  cloudiness_percent: number
  data_status: 'LIVE' | 'CACHED'
}
export interface CropRecommendationRequest {
  nitrogen: number
  phosphorus: number
  potassium: number
  temperature: number
  humidity: number
  ph: number
  rainfall: number
  location: string
}

export interface CropRecommendationResponse {
  location: string
  recommendation: string
  model_id: string
  latency_seconds: number
}
export interface SoilAdvisoryRequest {
  nitrogen: number
  phosphorus: number
  potassium: number
  ph: number
  soil_type: string
  crop: string
  location: string
}

export interface SoilAdvisoryResponse {
  location: string
  advisory: string
  model_id: string
  latency_seconds: number
}

export async function fetchSoilAdvisory(
  request: SoilAdvisoryRequest
): Promise<SoilAdvisoryResponse> {
  const res = await api.post<SoilAdvisoryResponse>(
    '/soil-advisory',
    request
  )
  return res.data
}

// Pest & Disease Advisory

export interface PestAdvisoryRequest {
  crop: string
  symptoms: string
  affected_part: string
  duration: string
  location: string
}

export interface PestAdvisoryResponse {
  location: string
  advisory: string
  model_id: string
  latency_seconds: number
}

export async function fetchPestAdvisory(
  request: PestAdvisoryRequest
) {
  const res = await api.post<PestAdvisoryResponse>(
    '/pest-advisory',
    request
  )
  return res.data
}

// Mandi Market Prices

export interface MandiPriceRecord {
  state?: string
  district?: string
  market?: string
  commodity?: string
  variety?: string
  arrival_date?: string
  min_price?: string | number
  max_price?: string | number
  modal_price?: string | number
}

export interface MandiPriceResponse {
  data_status: 'LIVE' | 'UNAVAILABLE'
  message: string
  total?: number
  records: MandiPriceRecord[]
}

export async function fetchMandiPrices(
  commodity: string,
  state: string,
  district: string
) {
  const res = await api.get<MandiPriceResponse>('/mandi-prices', {
    params: { commodity, state, district },
    timeout: 60000,
  })

  return res.data
}

export async function uploadKnowledgeDocument(file: File) {
  const formData = new FormData()
  formData.append('file', file)

  const response = await api.post('/kb/upload', formData, {
    timeout: 120000,
  })

  return response.data
}

export async function fetchKnowledgeDocuments() {
  const response = await api.get('/kb/documents')
  return response.data
}



export async function testGraniteConnection(): Promise<GraniteTestResponse> {
  const res = await api.get<GraniteTestResponse>('/granite/test')
  return res.data
}
export async function sendChatMessage(
  request: ChatRequest
): Promise<ChatResponse> {
  const res = await api.post<ChatResponse>('/chat', request)
  return res.data
}

export async function fetchWeather(
  location: string
): Promise<WeatherResponse> {
  const res = await api.get<WeatherResponse>(
    `/weather/${encodeURIComponent(location)}`
  )
  return res.data
}

export async function fetchCropRecommendation(
  request: CropRecommendationRequest
): Promise<CropRecommendationResponse> {
  const res = await api.post<CropRecommendationResponse>(
    '/crop-recommend',
    request
  )
  return res.data
}

export default api
