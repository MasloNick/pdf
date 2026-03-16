export interface Portfolio {
  id: number
  name: string
  purchase_date: string | null
  purchase_price_uah: number | null
  seller_name: string | null
  seller_edrpou: string | null
  contract_number: string | null
  debtor_count: number | null
  currency: string
  notes: string | null
  created_at: string
  updated_at: string
}

export interface Debtor {
  id: number
  portfolio_id: number
  full_name: string
  ipn: string | null
  birth_date: string | null
  phone_primary: string | null
  email: string | null
  credit_contract_number: string | null
  original_creditor: string | null
  purchased_total_uah: number | null
  collection_status: string | null
  in_erb: boolean | null
  in_bankruptcy: boolean | null
  created_at: string
  updated_at: string
}

export interface CourtCase {
  id: number
  debtor_id: number
  case_number: string | null
  court_name: string | null
  judge_name: string | null
  filing_date: string | null
  decision_date: string | null
  proceeding_type: string | null
  decision_outcome: string | null
  claimed_total: number | null
  awarded_total: number | null
  award_ratio: number | null
  ai_confidence: number | null
  ai_needs_review: boolean | null
  created_at: string
  updated_at: string
}

export interface DashboardStats {
  portfolios: number
  debtors: number
  court_cases: number
  enforcement_proceedings: number
  cases_by_outcome: Record<string, number>
  debtors_by_status: Record<string, number>
  total_purchased_uah: number
  total_awarded_uah: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}
