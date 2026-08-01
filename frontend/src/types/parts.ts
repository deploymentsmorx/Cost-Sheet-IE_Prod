export interface Workbook {
  id: number
  name: string
  client_id: number
  client_name: string | null
  description: string | null
  created_at: string
  sheet_count: number
}

// ---------------------------------------------------------------------------
// Per-line RM chain result
// ---------------------------------------------------------------------------

export interface RmLineResult {
  part_weight: string
  total_part_weight: string
  blank_weight: string
  total_blank_weight: string
  blank_rate: string
  blank_cost: string
  process_loss_pct: string
  process_loss_weight: string
  scrap_weight: string
  scrap_cost: string
  rm_cost: string
  norm_library_id: number
}

// ---------------------------------------------------------------------------
// Line-level structured process operations
// ---------------------------------------------------------------------------

export interface LineOperation {
  id: number
  costing_line_id: number
  operation_type: string
  input_data: Record<string, unknown>
  operation_cost: string
}

export interface CostingLine {
  id: number
  cost_sheet_id: number
  sl_no: number
  description: string | null
  spec: string | null
  grade_id: number | null
  thickness_band: string | null
  thickness_mm: string | null
  qty: string
  part_weight: string
  efficiency_pct: string
  operations: LineOperation[]
  rm_result: RmLineResult | null
  line_process_cost: string | null
  saved_at: string | null
}

// ---------------------------------------------------------------------------
// BO line items
// ---------------------------------------------------------------------------

export interface BOLineItem {
  id: number
  cost_sheet_id: number
  sl_no: number
  description: string | null
  qty: string
  unit_price: string
  bo_line_cost: string
}

// ---------------------------------------------------------------------------
// Sheet-level finishing operations
// ---------------------------------------------------------------------------

export interface SheetFinishingOp {
  id: number
  cost_sheet_id: number
  operation_name: string
  input_qty: string
  computed_cost: string
}

// ---------------------------------------------------------------------------
// Sheet-level calculation result
// ---------------------------------------------------------------------------

export interface BlockMarkup {
  base_total: string
  overhead: string
  rework: string
  inventory: string
  profit: string
  grand_total: string
}

export interface SheetCalcResult {
  line_process_costs: string[]
  total_rm_cost: string
  total_bo_cost: string
  total_process_cost: string
  total_finishing_cost: string
  rm_block: BlockMarkup
  bo_block: BlockMarkup
  process_block: BlockMarkup
  unit_price: string
  transport_cost: string
  discount_pct: string
  price_after_discount: string
  bal_margin: string
  bal_margin_per_kg: string
  total_part_weight: string
  norm_library_id: number
}

// ---------------------------------------------------------------------------
// Process Cost Row
// ---------------------------------------------------------------------------

export interface ProcessCostRow {
  id: number
  costing_line_id: number
  equi_spec: string | null
  thk: string | null
  unit_cut_length: string | null
  use_laser: boolean
  machining_rate: string | null
  bev_slant: string | null
  bev_length: string | null
  bend_num_bends: number | null
  drill_size: string | null
  drill_hours: string | null
  drill_type: string
  has_rolling: boolean
  cutting_cost: string
  machining_cost: string
  bevelling_cost: string
  bending_rate: string
  bending_cost: string
  drilling_rate: string
  drilling_cost: string
  rolling_rate: string
  rolling_cost: string
  row_total: string
  total_wt: string
}

// ---------------------------------------------------------------------------
// Full sheet response (merged Part + CostingSheet)
// ---------------------------------------------------------------------------

export interface CostSheetWithLines {
  id: number
  workbook_id: number
  name: string
  part_no: string | null
  description: string | null
  drawing_no: string | null
  benchmark_price: string | null
  client_id: number | null
  supply_version: string
  discount_pct: string
  transport_cost: string
  created_at: string
  lines: CostingLine[]
  bo_items: BOLineItem[]
  finishing_ops: SheetFinishingOp[]
  process_rows: ProcessCostRow[]
  sheet_result: SheetCalcResult | null
}

// ---------------------------------------------------------------------------
// Workbook summary
// ---------------------------------------------------------------------------

export interface CostSheetSummary {
  sheet_id: number
  name: string
  part_no: string | null
  supply_version: string
  total_price: string | null
  rm_cost: string | null
  bo_grand_total: string | null
  process_grand_total: string | null
  bal_margin: string | null
  total_weight: string | null
  discount_pct: string | null
  pct_change_vs_previous: string | null
  saved_at: string | null
  line_count: number
  saved_count: number
}

export interface WorkbookSummaryOut {
  id: number
  name: string
  client_id: number
  client_name: string | null
  cost_sheets: CostSheetSummary[]
}
