from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum

class RiskLevel(str, Enum):
    CRITICAL_STOCKOUT = "CRITICAL_STOCKOUT"
    REORDER_NOW = "REORDER_NOW"
    HEALTHY = "HEALTHY"
    OVERSTOCKED = "OVERSTOCKED"

class ABCCategory(str, Enum):
    A = "A"  # High-value / Top 20% revenue (Target: 98% service level)
    B = "B"  # Moderate value / Mid 30% revenue (Target: 95% service level)
    C = "C"  # Low value / Tail 50% revenue (Target: 90% service level)

@dataclass
class SupplierProfile:
    supplier_id: str
    supplier_name: str
    lead_time_days: float
    lead_time_std_days: float = 2.0
    moq: int = 50                 # Minimum Order Quantity
    case_pack_size: int = 10      # Batch ordering multiple
    on_time_delivery_rate: float = 0.94

@dataclass
class SKUItem:
    sku_id: str
    name: str
    category: str
    dept: str
    store_id: str
    unit_cost: float
    selling_price: float
    holding_cost_annual_rate: float = 0.20  # 20% annual holding cost
    abc_category: ABCCategory = ABCCategory.B
    supplier: Optional[SupplierProfile] = None

@dataclass
class InventoryState:
    on_hand_units: int
    in_transit_units: int = 0
    reserved_units: int = 0

    @property
    def net_effective_inventory(self) -> int:
        return max(0, self.on_hand_units + self.in_transit_units - self.reserved_units)

@dataclass
class OptimizationResult:
    sku_id: str
    sku_name: str
    category: str
    store_id: str
    daily_predicted_demand: float  # P50 / Median
    daily_demand_std: float
    demand_p10: float              # Bearish (10th Percentile)
    demand_p50: float              # Median (50th Percentile)
    demand_p90: float              # Bullish (90th Percentile)
    uncertainty_spread: float      # (P90 - P10)
    target_service_level: float
    safety_stock: int
    reorder_point: int
    current_on_hand: int
    current_in_transit: int
    net_effective_inventory: int
    days_of_inventory_remaining: float
    risk_level: RiskLevel
    recommended_reorder_qty: int
    estimated_po_cost: float
    revenue_at_risk: float
    excess_holding_cost: float
    supplier_name: str
    lead_time_days: float
    action_summary: str

@dataclass
class PurchaseOrderDraft:
    po_id: str
    supplier_id: str
    supplier_name: str
    created_date: str
    expected_delivery_date: str
    items: List[Dict] = field(default_factory=list)
    total_units: int = 0
    total_estimated_cost: float = 0.0
    status: str = "DRAFT"

@dataclass
class InventoryAuditReport:
    total_skus_evaluated: int
    critical_stockout_count: int
    reorder_now_count: int
    healthy_count: int
    overstocked_count: int
    total_revenue_at_risk: float
    total_capital_in_excess_stock: float
    total_recommended_po_value: float
    high_priority_actions: List[OptimizationResult]
    generated_pos: List[PurchaseOrderDraft]
