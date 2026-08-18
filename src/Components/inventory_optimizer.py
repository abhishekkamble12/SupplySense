import os
import sys
import math
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

from entity.inventory_entity import (
    SKUItem,
    SupplierProfile,
    InventoryState,
    OptimizationResult,
    PurchaseOrderDraft,
    InventoryAuditReport,
    RiskLevel,
    ABCCategory
)
from utils.sku_catalog import get_sku_or_default, get_all_catalog_skus, SUPPLIERS
from logger.logger import logging
from exception.exception import CustomException

class InventoryOptimizer:
    """
    Enterprise Inventory Optimization & Autonomous Decision Engine.
    Converts ML demand forecasts and supplier lead times into dynamic safety stocks,
    reorder points, stockout risk alarms, and automated purchase orders.
    """

    # Service level Z-score lookup
    SERVICE_LEVEL_Z: Dict[float, float] = {
        0.85: 1.04,
        0.90: 1.28,
        0.95: 1.645,
        0.98: 2.055,
        0.99: 2.326,
        0.999: 3.09
    }

    # ABC Velocity Target Service Levels
    ABC_SERVICE_TARGETS: Dict[ABCCategory, float] = {
        ABCCategory.A: 0.98,  # Hero items / 98% non-stockout guarantee
        ABCCategory.B: 0.95,  # Standard catalog / 95% service level
        ABCCategory.C: 0.90   # Long-tail / 90% service level
    }

    def __init__(self):
        pass

    def get_z_value(self, service_level: float) -> float:
        """Finds closest Z-score for target service level."""
        closest_sl = min(self.SERVICE_LEVEL_Z.keys(), key=lambda x: abs(x - service_level))
        return self.SERVICE_LEVEL_Z[closest_sl]

    def optimize_sku(
        self,
        sku: SKUItem,
        inventory_state: InventoryState,
        predicted_daily_demand: float,
        daily_demand_std: Optional[float] = None,
        custom_service_level: Optional[float] = None,
        custom_lead_time_days: Optional[float] = None
    ) -> OptimizationResult:
        """
        Executes stochastic inventory optimization for a single SKU.
        """
        try:
            supplier = sku.supplier or SUPPLIERS["SUP_NATURAL_ORGANICS"]
            lead_time = custom_lead_time_days if custom_lead_time_days is not None else supplier.lead_time_days
            lead_time_std = supplier.lead_time_std_days
            
            # Floor daily demand to prevent negative values
            d_mean = max(0.1, float(predicted_daily_demand))
            
            # If demand std is not provided, estimate using Poisson/Coefficient of Variation ~ 0.35
            if daily_demand_std is None or daily_demand_std <= 0:
                d_std = max(0.2, d_mean * 0.35)
            else:
                d_std = float(daily_demand_std)

            # 1. Target Service Level from ABC category
            target_sl = custom_service_level or self.ABC_SERVICE_TARGETS.get(sku.abc_category, 0.95)
            z_score = self.get_z_value(target_sl)

            # 2. Safety Stock Formula (accounting for demand variance & lead time variance)
            # SS = Z * sqrt( (L * sigma_D^2) + (D^2 * sigma_L^2) )
            variance_term = (lead_time * (d_std ** 2)) + ((d_mean ** 2) * (lead_time_std ** 2))
            safety_stock = int(math.ceil(z_score * math.sqrt(max(0.0, variance_term))))

            # 3. Dynamic Reorder Point (ROP) = (Demand * Lead Time) + Safety Stock
            lead_time_demand = d_mean * lead_time
            reorder_point = int(math.ceil(lead_time_demand + safety_stock))

            # 4. Inventory Balances & Days of Inventory (DOI)
            net_effective = inventory_state.net_effective_inventory
            doi = round(inventory_state.on_hand_units / d_mean, 1) if d_mean > 0 else 999.0

            # 5. Risk Assessment & Classification
            if net_effective < lead_time_demand:
                risk_level = RiskLevel.CRITICAL_STOCKOUT
                action_summary = (
                    f"CRITICAL: Stock will be depleted in {doi} days, shorter than supplier lead time "
                    f"({lead_time:.0f} days). Expedited PO required!"
                )
            elif net_effective <= reorder_point:
                risk_level = RiskLevel.REORDER_NOW
                action_summary = (
                    f"REORDER: Net inventory ({net_effective} units) is below Reorder Point ({reorder_point} units). "
                    f"Place order to maintain {target_sl*100:.0f}% service level."
                )
            elif net_effective > (reorder_point * 2.8) or doi > 75:
                risk_level = RiskLevel.OVERSTOCKED
                action_summary = (
                    f"OVERSTOCKED: {doi} days of inventory on hand. Excess working capital locked. "
                    f"Consider promotional markdown or delaying future POs."
                )
            else:
                risk_level = RiskLevel.HEALTHY
                action_summary = f"HEALTHY: Inventory levels optimal for projected demand over next {doi} days."

            # 6. Purchase Order Quantity Batching (MOQ & Case Packs)
            reorder_qty = 0
            if risk_level in [RiskLevel.CRITICAL_STOCKOUT, RiskLevel.REORDER_NOW]:
                # Replenish to target level (ROP + Cycle buffer)
                target_level = reorder_point + int(lead_time_demand * 0.8)
                deficit = max(0, target_level - net_effective)
                
                # Round up to supplier case pack size
                case_pack = max(1, supplier.case_pack_size)
                reorder_qty = int(math.ceil(deficit / case_pack) * case_pack)
                
                # Apply Minimum Order Quantity (MOQ)
                if reorder_qty < supplier.moq:
                    reorder_qty = supplier.moq

            estimated_po_cost = round(reorder_qty * sku.unit_cost, 2)

            # 7. Financial Risk Quantifications
            # Revenue at Risk (projected lost sales during lead time gap)
            shortage_units = max(0.0, lead_time_demand - net_effective)
            revenue_at_risk = round(shortage_units * sku.selling_price, 2)

            # Excess Holding Cost (monthly carrying cost for stock exceeding ROP)
            excess_units = max(0, net_effective - (reorder_point * 2))
            daily_holding_rate = sku.holding_cost_annual_rate / 365.0
            excess_holding_cost = round(excess_units * sku.unit_cost * daily_holding_rate * 30.0, 2)

            # 0. Calculate Probabilistic Demand Quantiles (P10, P50, P90)
            d_p50 = d_mean
            d_p10 = max(0.1, round(d_mean - (1.28155 * d_std), 2))
            d_p90 = round(d_mean + (1.28155 * d_std), 2)
            uncertainty_spread = round(d_p90 - d_p10, 2)

            return OptimizationResult(
                sku_id=sku.sku_id,
                sku_name=sku.name,
                category=sku.category,
                store_id=sku.store_id,
                daily_predicted_demand=round(d_mean, 2),
                daily_demand_std=round(d_std, 2),
                demand_p10=d_p10,
                demand_p50=round(d_p50, 2),
                demand_p90=d_p90,
                uncertainty_spread=uncertainty_spread,
                target_service_level=target_sl,
                safety_stock=safety_stock,
                reorder_point=reorder_point,
                current_on_hand=inventory_state.on_hand_units,
                current_in_transit=inventory_state.in_transit_units,
                net_effective_inventory=net_effective,
                days_of_inventory_remaining=doi,
                risk_level=risk_level,
                recommended_reorder_qty=reorder_qty,
                estimated_po_cost=estimated_po_cost,
                revenue_at_risk=revenue_at_risk,
                excess_holding_cost=excess_holding_cost,
                supplier_name=supplier.supplier_name,
                lead_time_days=lead_time,
                action_summary=action_summary
            )
        except Exception as e:
            logging.error(f"Error optimizing SKU {sku.sku_id}: {str(e)}")
            raise CustomException(e, sys)

    def generate_purchase_orders(self, optimization_results: List[OptimizationResult]) -> List[PurchaseOrderDraft]:
        """
        Consolidates recommended reorders into vendor-specific Draft Purchase Orders.
        """
        supplier_buckets: Dict[str, List[OptimizationResult]] = {}
        for res in optimization_results:
            if res.recommended_reorder_qty > 0:
                sku_obj = get_sku_or_default(res.sku_id, res.store_id)
                supp = sku_obj.supplier or SUPPLIERS["SUP_NATURAL_ORGANICS"]
                if supp.supplier_id not in supplier_buckets:
                    supplier_buckets[supp.supplier_id] = []
                supplier_buckets[supp.supplier_id].append(res)

        purchase_orders: List[PurchaseOrderDraft] = []
        now = datetime.now()

        for idx, (supp_id, items) in enumerate(supplier_buckets.items(), start=1):
            supplier_profile = SUPPLIERS.get(supp_id, SUPPLIERS["SUP_NATURAL_ORGANICS"])
            expected_date = now + timedelta(days=supplier_profile.lead_time_days)
            
            po_items = []
            po_total_units = 0
            po_total_cost = 0.0

            for itm in items:
                sku_obj = get_sku_or_default(itm.sku_id, itm.store_id)
                line_cost = round(itm.recommended_reorder_qty * sku_obj.unit_cost, 2)
                po_items.append({
                    "sku_id": itm.sku_id,
                    "sku_name": itm.sku_name,
                    "quantity": itm.recommended_reorder_qty,
                    "unit_cost": sku_obj.unit_cost,
                    "line_total": line_cost
                })
                po_total_units += itm.recommended_reorder_qty
                po_total_cost += line_cost

            po_draft = PurchaseOrderDraft(
                po_id=f"PO-{now.strftime('%Y%m%d')}-{idx:03d}",
                supplier_id=supplier_profile.supplier_id,
                supplier_name=supplier_profile.supplier_name,
                created_date=now.strftime("%Y-%m-%d"),
                expected_delivery_date=expected_date.strftime("%Y-%m-%d"),
                items=po_items,
                total_units=po_total_units,
                total_estimated_cost=round(po_total_cost, 2),
                status="DRAFT"
            )
            purchase_orders.append(po_draft)

        return purchase_orders

    def run_portfolio_audit(
        self,
        sku_states: Optional[List[Dict]] = None
    ) -> InventoryAuditReport:
        """
        Runs complete inventory optimization audit across sample store SKUs.
        """
        # Default mock inventory states for live evaluation
        default_eval_data = [
            {"sku_id": "SKU_FOODS_1_001", "on_hand": 18, "in_transit": 0, "daily_demand": 14.5, "demand_std": 3.2},
            {"sku_id": "SKU_FOODS_1_002", "on_hand": 85, "in_transit": 48, "daily_demand": 18.0, "demand_std": 4.1},
            {"sku_id": "SKU_FOODS_2_045", "on_hand": 4,  "in_transit": 0, "daily_demand": 6.2,  "demand_std": 1.5},
            {"sku_id": "SKU_HOBBIES_1_010", "on_hand": 140, "in_transit": 0, "daily_demand": 2.1,  "demand_std": 0.8},
            {"sku_id": "SKU_HOUSEHOLD_1_120", "on_hand": 32, "in_transit": 20, "daily_demand": 11.0, "demand_std": 2.8},
            {"sku_id": "SKU_HOUSEHOLD_2_088", "on_hand": 9,  "in_transit": 0, "daily_demand": 3.5,  "demand_std": 1.1},
            {"sku_id": "SKU_CARE_1_004", "on_hand": 12, "in_transit": 0, "daily_demand": 8.4,  "demand_std": 2.0},
            {"sku_id": "SKU_ELEC_1_015", "on_hand": 450, "in_transit": 0, "daily_demand": 4.0,  "demand_std": 1.0}
        ]

        active_data = sku_states if sku_states is not None else default_eval_data
        results: List[OptimizationResult] = []

        critical_count = 0
        reorder_count = 0
        healthy_count = 0
        overstock_count = 0
        total_rev_at_risk = 0.0
        total_excess_capital = 0.0

        for item in active_data:
            sku = get_sku_or_default(item["sku_id"])
            inv_state = InventoryState(
                on_hand_units=item.get("on_hand", 0),
                in_transit_units=item.get("in_transit", 0)
            )
            opt_res = self.optimize_sku(
                sku=sku,
                inventory_state=inv_state,
                predicted_daily_demand=item.get("daily_demand", 10.0),
                daily_demand_std=item.get("demand_std", 2.5)
            )
            results.append(opt_res)

            if opt_res.risk_level == RiskLevel.CRITICAL_STOCKOUT:
                critical_count += 1
            elif opt_res.risk_level == RiskLevel.REORDER_NOW:
                reorder_count += 1
            elif opt_res.risk_level == RiskLevel.HEALTHY:
                healthy_count += 1
            elif opt_res.risk_level == RiskLevel.OVERSTOCKED:
                overstock_count += 1

            total_rev_at_risk += opt_res.revenue_at_risk
            total_excess_capital += opt_res.excess_holding_cost

        # Generate draft purchase orders
        generated_pos = self.generate_purchase_orders(results)
        total_po_value = sum(po.total_estimated_cost for po in generated_pos)

        # High priority actions: items needing PO or critical stockout
        high_priority = [r for r in results if r.risk_level in [RiskLevel.CRITICAL_STOCKOUT, RiskLevel.REORDER_NOW]]

        return InventoryAuditReport(
            total_skus_evaluated=len(results),
            critical_stockout_count=critical_count,
            reorder_now_count=reorder_count,
            healthy_count=healthy_count,
            overstocked_count=overstock_count,
            total_revenue_at_risk=round(total_rev_at_risk, 2),
            total_capital_in_excess_stock=round(total_excess_capital, 2),
            total_recommended_po_value=round(total_po_value, 2),
            high_priority_actions=high_priority,
            generated_pos=generated_pos
        )
