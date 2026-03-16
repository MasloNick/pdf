import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Portfolios from './pages/Portfolios'
import Debtors from './pages/Debtors'
import CourtCases from './pages/CourtCases'
import ImportPage from './pages/ImportPage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="portfolios" element={<Portfolios />} />
        <Route path="debtors" element={<Debtors />} />
        <Route path="court-cases" element={<CourtCases />} />
        <Route path="import" element={<ImportPage />} />
      </Route>
    </Routes>
  )
}

export default App
