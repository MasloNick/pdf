// ── Portfolio ────────────────────────────────────────────
export interface Portfolio {
  id: string;
  name: string;
  seller_name: string;
  purchase_date: string;
  purchase_price: number;
  total_nominal_debt: number;
  currency: string;
  contract_number: string | null;
  notes: string | null;
  debtor_count: number;
  created_at: string;
  updated_at: string;
}

// ── Debtor ──────────────────────────────────────────────
export type DebtorType = "individual" | "legal_entity" | "entrepreneur";
export type DebtorStatus =
  | "new"
  | "in_court"
  | "judgment_obtained"
  | "enforcement"
  | "partially_recovered"
  | "fully_recovered"
  | "bankrupt"
  | "written_off";

export interface Debtor {
  id: string;
  portfolio_id: string;
  debtor_type: DebtorType;
  full_name: string;
  ipn_code: string | null;
  date_of_birth: string | null;
  registration_address: string | null;
  region: string | null;
  phone: string | null;
  email: string | null;
  original_debt_amount: number;
  current_debt_amount: number;
  currency: string;
  original_creditor: string | null;
  status: DebtorStatus;
  created_at: string;
  updated_at: string;
}

export interface DebtorListResponse {
  items: Debtor[];
  total: number;
  page: number;
  size: number;
}

// ── Court Case ──────────────────────────────────────────
export type CaseType = "civil" | "commercial" | "administrative" | "nakazne" | "pozovne";
export type CaseStatus =
  | "draft"
  | "filed"
  | "in_progress"
  | "decided"
  | "appealed"
  | "cassation"
  | "enforcement"
  | "closed"
  | "returned";

export interface CourtCase {
  id: string;
  debtor_id: string;
  case_number: string;
  case_type: CaseType;
  status: CaseStatus;
  court_name: string;
  court_code: string | null;
  judge_name: string | null;
  claim_amount: number;
  court_fee_amount: number | null;
  awarded_amount: number | null;
  filing_date: string | null;
  hearing_date: string | null;
  decision_date: string | null;
  party_replacement_needed: boolean;
  party_replacement_status: string | null;
  created_at: string;
  updated_at: string;
}

// ── Analytics ───────────────────────────────────────────
export interface DashboardSummary {
  portfolio_stats: {
    total_portfolios: number;
    total_debtors: number;
    total_nominal_debt: number;
    total_current_debt: number;
    total_recovered: number;
  };
  cases_by_status: Record<string, number>;
  recent_decisions_count: number;
  pending_enforcement_count: number;
  bankruptcy_alerts_count: number;
  needs_review_count: number;
}

export interface CourtStats {
  court_name: string;
  total_cases: number;
  satisfied_count: number;
  denied_count: number;
  satisfaction_rate: number;
  avg_awarded_amount: number | null;
}

export interface JudgeStats {
  judge_name: string;
  court_name: string;
  total_cases: number;
  satisfied_count: number;
  denied_count: number;
  satisfaction_rate: number;
}
