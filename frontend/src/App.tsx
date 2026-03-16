import { Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import Layout from "./components/common/Layout";
import DashboardPage from "./pages/DashboardPage";
import PortfoliosPage from "./pages/PortfoliosPage";
import DebtorsPage from "./pages/DebtorsPage";
import CourtCasesPage from "./pages/CourtCasesPage";
import AnalyticsPage from "./pages/AnalyticsPage";
import LoginPage from "./pages/LoginPage";
import { useAuthStore } from "./store/authStore";

function App() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  if (!isAuthenticated) {
    return (
      <>
        <LoginPage />
        <Toaster position="top-right" />
      </>
    );
  }

  return (
    <>
      <Layout>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/portfolios" element={<PortfoliosPage />} />
          <Route path="/debtors" element={<DebtorsPage />} />
          <Route path="/court-cases" element={<CourtCasesPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
      <Toaster position="top-right" />
    </>
  );
}

export default App;
