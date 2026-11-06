
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'

import Navbar from './components/layout/Navbar'

import Landing from './pages/Landing'
import Dashboard from './pages/Dashboard'
import GraniteStatus from './pages/GraniteStatus'
import ChatBot from './pages/ChatBot'
import WeatherDashboard from './pages/WeatherDashboard'
import CropRecommendation from './pages/CropRecommendation'
import SoilAdvisory from './pages/SoilAdvisory'
import PestDisease from './pages/PestDisease'
import MandiPrices from './pages/MandiPrices'
import KnowledgeBase from './pages/KnowledgeBase'
function App() {
  return (
    <BrowserRouter>
      <Navbar />

      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/granite" element={<GraniteStatus />} />
        <Route path="/chat" element={<ChatBot />} />
        <Route path="/weather" element={<WeatherDashboard />} />
        <Route
          path="/crop-recommendation"
          element={<CropRecommendation />}
        />
        <Route path="*" element={<Navigate to="/" replace />} />
        <Route path="/soil-advisory" element={<SoilAdvisory />} />
        <Route path="/pest-disease" element={<PestDisease />} />
        <Route path="/mandi-prices" element={<MandiPrices />} />
        <Route path="/knowledge-base" element={<KnowledgeBase />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
