export interface Portfolio {
  id: number;
  name: string;
  seller_name: string;
  purchase_date: string;
  purchase_price: number;
  total_nominal_value: number;
  currency: string;
  contract_number: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface Debtor {
  id: number;
  debtor_type: "individual" | "legal_entity";
  last_name: string | null;
  first_name: string | null;
  patronymic: string | null;
  full_name: string | null;
  ipn: string | null;
  edrpou: string | null;
  birth_date: string | null;
  status: string;
  is_bankrupt: boolean;
  created_at: string;
  updated_at: string;
}

export interface CourtCase {
  id: number;
  debtor_id: number;
  case_number: string;
  court_name: string;
  judge_name: string | null;
  proceeding_type: string;
  claim_amount: number | null;
  court_fee: number | null;
  filing_date: string | null;
  status: string;
  current_stage: string | null;
  decision_date: string | null;
  decision_type: string | null;
  awarded_amount: number | null;
  created_at: string;
  updated_at: string;
}

export interface DashboardStats {
  portfolios: number;
  debtors: number;
  court_cases: number;
  active_enforcements: number;
  bankrupt_debtors: number;
  cases_by_status: Record<string, number>;
}
