import { Routes, Route, Navigate } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import Portfolios from "./pages/Portfolios";
import Debtors from "./pages/Debtors";
import CourtCases from "./pages/CourtCases";
import Analytics from "./pages/Analytics";

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/portfolios" element={<Portfolios />} />
      <Route path="/debtors" element={<Debtors />} />
      <Route path="/court-cases" element={<CourtCases />} />
      <Route path="/analytics" element={<Analytics />} />
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

export default App;
