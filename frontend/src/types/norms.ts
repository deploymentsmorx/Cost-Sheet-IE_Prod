export interface NormLibrarySummary {
  id: number
  client_id: number
  label: string
  effective_date: string
  is_current: boolean
  is_draft: boolean
  created_at: string
}

export interface MaterialGrade {
  id: number
  name: string
  base_grade_id: number | null
  premium_amount: string | null
  updated_at: string
}

export interface RmPriceBand {
  id: number
  grade_id: number
  thickness_band: string
  price_per_kg: string
  updated_at: string
}

export interface ScrapRate {
  rate_per_kg: string
  updated_at: string
}

export interface ProcessRate {
  id: number
  operation_name: string
  unit: string
  rate: string
  sort_order: number
  group_label: string
  updated_at: string
}

export interface CostOverheadParam {
  id: number
  applies_to: "raw_material" | "bought_out" | "process_cost"
  param_name: string
  sort_order: number
  param_value: string | null
  updated_at: string
}

export interface NormLibraryDetail {
  library: NormLibrarySummary
  material_grades: MaterialGrade[]
  rm_price_bands: RmPriceBand[]
  scrap_rate: ScrapRate | null
  process_rates: ProcessRate[]
  overhead_params: CostOverheadParam[]
}

export interface NormsLookup {
  norm_library_id: number | null
  material_grades: MaterialGrade[]
  process_rates: ProcessRate[]
  overhead_params: CostOverheadParam[]
}

// Request bodies
export interface RmPriceUpdate {
  grade_id: number
  thickness_band: string
  price_per_kg: string
}

export interface GradePremiumUpdate {
  grade_id: number
  premium_amount: string
}

export interface RmPricesBulkUpdate {
  scrap_rate?: string
  grade_premium_updates?: GradePremiumUpdate[]
  price_updates?: RmPriceUpdate[]
}

export interface ProcessRateUpdate {
  id: number
  rate: string
}

export interface OverheadParamUpdate {
  id: number
  param_value: string | null
}
