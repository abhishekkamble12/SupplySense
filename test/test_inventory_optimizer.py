import pytest
import os
import sys

# Ensure src is on path for tests
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from entity.inventory_entity import (
    SKUItem,
    SupplierProfile,
    InventoryState,
    RiskLevel,
    ABCCategory
)
from utils.sku_catalog import SAMPLE_CATALOG, SUPPLIERS, get_sku_or_default
from Components.inventory_optimizer import InventoryOptimizer

@pytest.fixture
def optimizer():
    return InventoryOptimizer()

@pytest.fixture
def sample_sku():
    return SKUItem(
        sku_id="TEST_COFFEE_01",
        name="Artisan Roast Coffee",
        category="Foods",
        dept="Beverages",
        store_id="CA_1",
        unit_cost=5.0,
        selling_price=15.0,
        holding_cost_annual_rate=0.20,
        abc_category=ABCCategory.A,
        supplier=SupplierProfile(
            supplier_id="SUP_TEST",
            supplier_name="Test Roasters",
            lead_time_days=10.0,
            lead_time_std_days=2.0,
            moq=50,
            case_pack_size=10,
            on_time_delivery_rate=0.95
        )
    )

def test_critical_stockout_detection(optimizer, sample_sku):
    # Daily demand = 10, Lead time = 10 days -> Lead time demand = 100 units
    # If on hand is only 15 units, it should be CRITICAL_STOCKOUT
    state = InventoryState(on_hand_units=15, in_transit_units=0)
    result = optimizer.optimize_sku(
        sku=sample_sku,
        inventory_state=state,
        predicted_daily_demand=10.0,
        daily_demand_std=2.0
    )
    
    assert result.risk_level == RiskLevel.CRITICAL_STOCKOUT
    assert result.days_of_inventory_remaining == 1.5
    assert result.recommended_reorder_qty >= 50  # Must satisfy MOQ = 50
    assert result.recommended_reorder_qty % 10 == 0  # Must be multiple of case pack = 10
    assert result.revenue_at_risk > 0
    assert result.demand_p10 < result.demand_p50 < result.demand_p90
    assert result.uncertainty_spread == round(result.demand_p90 - result.demand_p10, 2)

def test_reorder_now_trigger(optimizer, sample_sku):
    # Daily demand = 10, Lead time = 10 -> Lead time demand = 100
    # Safety stock ~ 35 -> ROP ~ 135
    # If on hand is 120 (less than ROP 135 but greater than lead time demand 100) -> REORDER_NOW
    state = InventoryState(on_hand_units=120, in_transit_units=0)
    result = optimizer.optimize_sku(
        sku=sample_sku,
        inventory_state=state,
        predicted_daily_demand=10.0,
        daily_demand_std=2.0
    )
    
    assert result.risk_level == RiskLevel.REORDER_NOW
    assert result.recommended_reorder_qty > 0
    assert result.recommended_reorder_qty % 10 == 0

def test_healthy_inventory(optimizer, sample_sku):
    # On hand is healthy (e.g. 200 units, well above ROP but not excessively overstocked)
    state = InventoryState(on_hand_units=200, in_transit_units=0)
    result = optimizer.optimize_sku(
        sku=sample_sku,
        inventory_state=state,
        predicted_daily_demand=10.0,
        daily_demand_std=2.0
    )
    
    assert result.risk_level == RiskLevel.HEALTHY
    assert result.recommended_reorder_qty == 0
    assert result.estimated_po_cost == 0.0

def test_overstocked_inventory(optimizer, sample_sku):
    # On hand is 1000 units (100 days of supply) -> OVERSTOCKED
    state = InventoryState(on_hand_units=1000, in_transit_units=0)
    result = optimizer.optimize_sku(
        sku=sample_sku,
        inventory_state=state,
        predicted_daily_demand=10.0,
        daily_demand_std=2.0
    )
    
    assert result.risk_level == RiskLevel.OVERSTOCKED
    assert result.recommended_reorder_qty == 0
    assert result.excess_holding_cost > 0

def test_purchase_order_generation(optimizer):
    audit_report = optimizer.run_portfolio_audit()
    assert audit_report.total_skus_evaluated > 0
    assert len(audit_report.generated_pos) > 0
    
    for po in audit_report.generated_pos:
        assert po.po_id.startswith("PO-")
        assert po.total_units > 0
        assert po.total_estimated_cost > 0
        assert len(po.items) > 0
