import apiClient from "./client";
import type {
  CourtCase,
  CourtStats,
  DashboardSummary,
  Debtor,
  DebtorListResponse,
  JudgeStats,
  Portfolio,
} from "../types";

// ── Auth ────────────────────────────────────────────────
export const login = (username: string, password: string) =>
  apiClient.post<{ access_token: string }>("/auth/login", { username, password });

// ── Portfolios ──────────────────────────────────────────
export const getPortfolios = (page = 1, size = 50) =>
  apiClient.get<Portfolio[]>("/portfolios", { params: { page, size } });

export const createPortfolio = (data: Partial<Portfolio>) =>
  apiClient.post<Portfolio>("/portfolios", data);

export const getPortfolio = (id: string) =>
  apiClient.get<Portfolio>(`/portfolios/${id}`);

// ── Debtors ─────────────────────────────────────────────
export const getDebtors = (params: {
  page?: number;
  size?: number;
  portfolio_id?: string;
  status?: string;
  search?: string;
}) => apiClient.get<DebtorListResponse>("/debtors", { params });

export const getDebtor = (id: string) =>
  apiClient.get<Debtor>(`/debtors/${id}`);

// ── Court Cases ─────────────────────────────────────────
export const getCourtCases = (params: {
  debtor_id?: string;
  status?: string;
  page?: number;
  size?: number;
}) => apiClient.get<CourtCase[]>("/court-cases", { params });

export const getCourtCase = (id: string) =>
  apiClient.get<CourtCase>(`/court-cases/${id}`);

// ── Analytics ───────────────────────────────────────────
export const getDashboard = () =>
  apiClient.get<DashboardSummary>("/analytics/dashboard");

export const getCourtStats = () =>
  apiClient.get<CourtStats[]>("/analytics/courts");

export const getJudgeStats = (courtName?: string) =>
  apiClient.get<JudgeStats[]>("/analytics/judges", {
    params: courtName ? { court_name: courtName } : {},
  });
