import os
import sys
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from entity.inventory_entity import RiskLevel, InventoryState
from utils.sku_catalog import SAMPLE_CATALOG, SUPPLIERS, get_sku_or_default, get_all_catalog_skus
from Components.inventory_optimizer import InventoryOptimizer
from logger.logger import logging
from exception.exception import CustomException

class SupplyChainCopilot:
    """
    Autonomous AI Supply Chain Copilot & Assistant.
    Understands natural language questions about inventory risk, generates what-if simulations,
    drafts supplier PO communications, and optimizes working capital.
    """

    def __init__(self, optimizer: Optional[InventoryOptimizer] = None):
        self.optimizer = optimizer or InventoryOptimizer()

    def process_query(self, user_message: str) -> Dict[str, Any]:
        """
        Main query processing pipeline. Parses intent, retrieves live context,
        and constructs an actionable, structured response.
        """
        try:
            msg_lower = user_message.lower().strip()
            
            # 1. Supplier Email Drafting Intent
            if any(k in msg_lower for k in ["draft", "email", "vendor", "letter", "po email", "supplier email"]):
                return self._handle_draft_email(msg_lower, user_message)

            # 2. What-If / Simulation Intent
            if any(k in msg_lower for k in ["simulate", "what if", "delay", "surge", "disruption", "port congestion"]):
                return self._handle_simulation_query(msg_lower)

            # 3. Stockout Risk & Critical SKU Query
            if any(k in msg_lower for k in ["critical", "stockout", "risk", "run out", "danger", "urgent"]):
                return self._handle_risk_query()

            # 4. Purchase Order & Reorder Query
            if any(k in msg_lower for k in ["reorder", "purchase order", "po", "order", "buy"]):
                return self._handle_reorder_query()

            # 5. Excess / Overstock / Working Capital Query
            if any(k in msg_lower for k in ["excess", "overstock", "dead stock", "working capital", "cash", "carrying cost"]):
                return self._handle_capital_query()

            # 6. Specific SKU Inquiry
            for sku_id, sku in SAMPLE_CATALOG.items():
                if sku_id.lower() in msg_lower or any(word in msg_lower for word in sku.name.lower().split() if len(word) > 4):
                    return self._handle_single_sku_query(sku)

            # Default General Summary & Guidance
            return self._handle_general_summary()

        except Exception as e:
            logging.error(f"Copilot query failed: {str(e)}")
            raise CustomException(e, sys)

    def _handle_risk_query(self) -> Dict[str, Any]:
        audit = self.optimizer.run_portfolio_audit()
        critical_items = [item for item in audit.high_priority_actions if item.risk_level == RiskLevel.CRITICAL_STOCKOUT]
        
        response_text = f"### 🚨 Stockout Risk Radar\n\n"
        response_text += f"We currently have **{len(critical_items)} SKUs in Critical Stockout** condition with **${audit.total_revenue_at_risk:,.2f}** in projected lost revenue over the supplier lead time window:\n\n"
        
        for item in critical_items:
            response_text += f"- **{item.sku_name}** (`{item.sku_id}`):\n"
            response_text += f"  - **On-Hand Stock**: {item.current_on_hand} units (~{item.days_of_inventory_remaining:.1f} days left)\n"
            response_text += f"  - **Supplier Lead Time**: {item.lead_time_days:.0f} days ({item.supplier_name})\n"
            response_text += f"  - **Urgent Action**: Place expedited PO for **{item.recommended_reorder_qty} units** (Est. ${item.estimated_po_cost:,.2f})\n\n"
            
        return {
            "type": "STOCKOUT_REPORT",
            "reply": response_text,
            "actions": [
                {"label": "Approve All Emergency POs", "action": "approve_emergency_pos"},
                {"label": "Simulate Supplier Expedite", "action": "simulate_expedite"}
            ]
        }

    def _handle_reorder_query(self) -> Dict[str, Any]:
        audit = self.optimizer.run_portfolio_audit()
        pos = audit.generated_pos
        
        response_text = f"### 📦 Purchase Order & Replenishment Summary\n\n"
        response_text += f"SupplySense has generated **{len(pos)} Draft Purchase Orders** representing **${audit.total_recommended_po_value:,.2f}** in total replenishment capital:\n\n"
        
        for po in pos:
            response_text += f"#### **{po.po_id}** — {po.supplier_name}\n"
            response_text += f"- **Expected Delivery**: {po.expected_delivery_date}\n"
            response_text += f"- **Total Units**: {po.total_units} units | **Total Value**: ${po.total_estimated_cost:,.2f}\n"
            for itm in po.items:
                response_text += f"  - {itm['sku_name']}: {itm['quantity']} units (@ ${itm['unit_cost']:.2f}/ea = ${itm['line_total']:,.2f})\n"
            response_text += "\n"

        return {
            "type": "PO_SUMMARY",
            "reply": response_text,
            "actions": [
                {"label": "Dispatch POs to ERP", "action": "dispatch_erp"}
            ]
        }

    def _handle_capital_query(self) -> Dict[str, Any]:
        audit = self.optimizer.run_portfolio_audit()
        
        response_text = f"### 💰 Working Capital & Carrying Cost Diagnostics\n\n"
        response_text += f"- **Trapped Capital in Overstock**: ${audit.total_capital_in_excess_stock:,.2f}/month in carrying costs.\n"
        response_text += f"- **Overstocked SKUs**: {audit.overstocked_count} items with inventory coverage exceeding 75+ days.\n"
        response_text += f"- **Total Capital Required for Reorders**: ${audit.total_recommended_po_value:,.2f}\n\n"
        response_text += f"**Optimization Recommendation**: Run a 15% targeted promotional campaign on overstocked electronics and hobby SKUs to free up working capital and fund high-velocity food replenishments."

        return {
            "type": "CAPITAL_AUDIT",
            "reply": response_text,
            "actions": [
                {"label": "Generate Markdown Campaign", "action": "markdown_promo"}
            ]
        }

    def _handle_draft_email(self, msg_lower: str, original_msg: str) -> Dict[str, Any]:
        # Identify vendor or SKU
        matched_supplier = None
        for supp_id, supp in SUPPLIERS.items():
            if supp.supplier_name.lower() in msg_lower or supp_id.lower() in msg_lower:
                matched_supplier = supp
                break
        
        if not matched_supplier:
            matched_supplier = SUPPLIERS["SUP_NATURAL_ORGANICS"]

        # Identify items
        items_to_order = []
        for sku_id, sku in SAMPLE_CATALOG.items():
            if sku.supplier and sku.supplier.supplier_id == matched_supplier.supplier_id:
                items_to_order.append(sku)

        target_sku = items_to_order[0] if items_to_order else list(SAMPLE_CATALOG.values())[0]
        po_number = f"PO-{datetime.now().strftime('%Y%m%d')}-001"
        delivery_date = (datetime.now() + timedelta(days=matched_supplier.lead_time_days)).strftime("%B %d, %Y")

        email_content = f"""Subject: URGENT: Purchase Order {po_number} - {matched_supplier.supplier_name}

Dear {matched_supplier.supplier_name} Account Team,

Please accept this official Purchase Order ({po_number}) on behalf of our retail supply chain operations:

• SKU: {target_sku.name} ({target_sku.sku_id})
• Quantity: {matched_supplier.moq} units ({matched_supplier.moq // matched_supplier.case_pack_size} case packs)
• Unit Agreed Price: ${target_sku.unit_cost:.2f}
• Total PO Amount: ${matched_supplier.moq * target_sku.unit_cost:,.2f}
• Required Delivery Date: {delivery_date}

Due to unexpected retail demand acceleration in our California fulfillment centers, please confirm receipt of this PO and let us know if expedited air freight is available to shorten the {matched_supplier.lead_time_days:.0f}-day lead time.

Best regards,
Supply Chain Operations Director
SupplySense Autonomous Procurement Engine"""

        return {
            "type": "DRAFT_EMAIL",
            "reply": f"### 📧 Drafted Supplier PO Communication\n\n```text\n{email_content}\n```",
            "actions": [
                {"label": "Send Email via SMTP / Resend", "action": "send_email"},
                {"label": "Export PO PDF", "action": "export_pdf"}
            ]
        }

    def _handle_simulation_query(self, msg_lower: str) -> Dict[str, Any]:
        # Extract lead time delta or demand spike numbers if mentioned
        days_match = re.search(r'(\d+)\s*(day|days)', msg_lower)
        days = float(days_match.group(1)) if days_match else 14.0

        surge_match = re.search(r'(\d+)%', msg_lower)
        surge_multiplier = 1.0 + (float(surge_match.group(1)) / 100.0) if surge_match else 1.35

        target_sku = SAMPLE_CATALOG["SKU_FOODS_1_001"]

        # Run simulation
        opt_res = self.optimizer.optimize_sku(
            sku=target_sku,
            inventory_state=InventoryState(on_hand_units=18),
            predicted_daily_demand=14.5 * surge_multiplier,
            custom_lead_time_days=target_sku.supplier.lead_time_days + days
        )

        response_text = f"### 🧪 Stress-Test Simulation: {target_sku.name}\n\n"
        response_text += f"- **Disruption Parameters**: +{days:.0f} Days Supplier Delay, +{(surge_multiplier-1)*100:.0f}% Demand Surge\n"
        response_text += f"- **Updated Safety Stock Required**: {opt_res.safety_stock} units (+{opt_res.safety_stock - 22} units delta)\n"
        response_text += f"- **Updated Reorder Point (ROP)**: {opt_res.reorder_point} units\n"
        response_text += f"- **Immediate PO Required**: {opt_res.recommended_reorder_qty} units (Est. ${opt_res.estimated_po_cost:,.2f})\n"
        response_text += f"- **Revenue at Risk if Unaddressed**: ${opt_res.revenue_at_risk:,.2f}\n"

        return {
            "type": "SIMULATION_RESULT",
            "reply": response_text,
            "actions": [
                {"label": "Adjust Safety Stock in ERP", "action": "apply_safety_stock"}
            ]
        }

    def _handle_single_sku_query(self, sku) -> Dict[str, Any]:
        res = self.optimizer.optimize_sku(
            sku=sku,
            inventory_state=InventoryState(on_hand_units=20),
            predicted_daily_demand=10.0
        )
        
        reply = f"### 🔍 SKU Inspection: {sku.name} (`{sku.sku_id}`)\n\n"
        reply += f"- **Category / Store**: {sku.category} ({sku.dept}) | {sku.store_id}\n"
        reply += f"- **Supplier**: {sku.supplier.supplier_name} (Lead Time: {sku.supplier.lead_time_days:.0f} days, MOQ: {sku.supplier.moq})\n"
        reply += f"- **Unit Economics**: COGS ${sku.unit_cost:.2f} | Retail Price ${sku.selling_price:.2f} (Margin: {((sku.selling_price-sku.unit_cost)/sku.selling_price)*100:.1f}%)\n"
        reply += f"- **Optimization Status**: {res.risk_level.value} (Safety Stock: {res.safety_stock} units, ROP: {res.reorder_point} units)\n"
        reply += f"- **Action Plan**: {res.action_summary}"

        return {
            "type": "SKU_INFO",
            "reply": reply,
            "actions": [
                {"label": f"Create PO for {sku.sku_id}", "action": "create_po"}
            ]
        }

    def _handle_general_summary(self) -> Dict[str, Any]:
        audit = self.optimizer.run_portfolio_audit()
        reply = f"### ⚡ SupplySense Assistant\n\n"
        reply += f"I am your Autonomous Supply Chain Decision Engine. Current portfolio status:\n\n"
        reply += f"- **{audit.critical_stockout_count} Critical Stockouts** requiring emergency PO placement.\n"
        reply += f"- **${audit.total_revenue_at_risk:,.2f}** in revenue at risk across California and Texas hubs.\n"
        reply += f"- **{len(audit.generated_pos)} Draft POs** ready for vendor dispatch (${audit.total_recommended_po_value:,.2f} total).\n\n"
        reply += f"You can ask me to:\n"
        reply += f"1. *'Which SKUs are in danger of stockout?'*\n"
        reply += f"2. *'Draft an email to Verde Organics for Coffee order'* \n"
        reply += f"3. *'What happens if supplier lead times increase by 20 days?'*"

        return {
            "type": "GENERAL_SUMMARY",
            "reply": reply,
            "actions": [
                {"label": "Run Full Health Audit", "action": "audit"}
            ]
        }
