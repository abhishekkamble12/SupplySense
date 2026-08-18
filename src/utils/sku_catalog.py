from typing import Dict, List, Optional
from entity.inventory_entity import SKUItem, SupplierProfile, ABCCategory

# Realistic Multi-Tier Retail Suppliers
SUPPLIERS: Dict[str, SupplierProfile] = {
    "SUP_GLOBAL_BEV": SupplierProfile(
        supplier_id="SUP_GLOBAL_BEV",
        supplier_name="Apex Global Beverage Dist.",
        lead_time_days=14.0,
        lead_time_std_days=2.5,
        moq=100,
        case_pack_size=24,
        on_time_delivery_rate=0.92
    ),
    "SUP_NATURAL_ORGANICS": SupplierProfile(
        supplier_id="SUP_NATURAL_ORGANICS",
        supplier_name="Verde Organics Co.",
        lead_time_days=7.0,
        lead_time_std_days=1.2,
        moq=50,
        case_pack_size=12,
        on_time_delivery_rate=0.97
    ),
    "SUP_HOME_ESSENTIALS": SupplierProfile(
        supplier_id="SUP_HOME_ESSENTIALS",
        supplier_name="Pacific Home Goods Ltd.",
        lead_time_days=21.0,
        lead_time_std_days=4.0,
        moq=120,
        case_pack_size=20,
        on_time_delivery_rate=0.88
    ),
    "SUP_PERSONAL_CARE": SupplierProfile(
        supplier_id="SUP_PERSONAL_CARE",
        supplier_name="Lumina Health & Wellness",
        lead_time_days=10.0,
        lead_time_std_days=1.8,
        moq=60,
        case_pack_size=12,
        on_time_delivery_rate=0.95
    ),
    "SUP_ELECTRONICS_DIRECT": SupplierProfile(
        supplier_id="SUP_ELECTRONICS_DIRECT",
        supplier_name="VoltDirect Supply Chain",
        lead_time_days=28.0,
        lead_time_std_days=5.0,
        moq=40,
        case_pack_size=10,
        on_time_delivery_rate=0.85
    )
}

# SKU Catalog mapping with unit economics & ABC stratification
SAMPLE_CATALOG: Dict[str, SKUItem] = {
    "SKU_FOODS_1_001": SKUItem(
        sku_id="SKU_FOODS_1_001",
        name="Artisan Dark Roast Ground Coffee 12oz",
        category="Foods",
        dept="Beverages",
        store_id="CA_1",
        unit_cost=4.80,
        selling_price=11.99,
        holding_cost_annual_rate=0.18,
        abc_category=ABCCategory.A,
        supplier=SUPPLIERS["SUP_NATURAL_ORGANICS"]
    ),
    "SKU_FOODS_1_002": SKUItem(
        sku_id="SKU_FOODS_1_002",
        name="Organic Almond Milk Unsweetened 32oz",
        category="Foods",
        dept="Dairy Alternatives",
        store_id="CA_1",
        unit_cost=1.90,
        selling_price=4.49,
        holding_cost_annual_rate=0.22,
        abc_category=ABCCategory.A,
        supplier=SUPPLIERS["SUP_GLOBAL_BEV"]
    ),
    "SKU_FOODS_2_045": SKUItem(
        sku_id="SKU_FOODS_2_045",
        name="Extra Virgin Olive Oil Cold Pressed 750ml",
        category="Foods",
        dept="Pantry",
        store_id="CA_1",
        unit_cost=8.20,
        selling_price=18.99,
        holding_cost_annual_rate=0.15,
        abc_category=ABCCategory.B,
        supplier=SUPPLIERS["SUP_NATURAL_ORGANICS"]
    ),
    "SKU_HOBBIES_1_010": SKUItem(
        sku_id="SKU_HOBBIES_1_010",
        name="Ergonomic Memory Foam Travel Pillow",
        category="Hobbies",
        dept="Travel Accessories",
        store_id="TX_1",
        unit_cost=9.50,
        selling_price=24.99,
        holding_cost_annual_rate=0.20,
        abc_category=ABCCategory.B,
        supplier=SUPPLIERS["SUP_HOME_ESSENTIALS"]
    ),
    "SKU_HOUSEHOLD_1_120": SKUItem(
        sku_id="SKU_HOUSEHOLD_1_120",
        name="Eco-Friendly Laundry Detergent Sheets 60pk",
        category="Household",
        dept="Cleaning",
        store_id="WI_1",
        unit_cost=5.10,
        selling_price=14.99,
        holding_cost_annual_rate=0.15,
        abc_category=ABCCategory.A,
        supplier=SUPPLIERS["SUP_HOME_ESSENTIALS"]
    ),
    "SKU_HOUSEHOLD_2_088": SKUItem(
        sku_id="SKU_HOUSEHOLD_2_088",
        name="Cast Iron Skillet Pre-Seasoned 10-inch",
        category="Household",
        dept="Cookware",
        store_id="CA_2",
        unit_cost=14.00,
        selling_price=34.99,
        holding_cost_annual_rate=0.18,
        abc_category=ABCCategory.B,
        supplier=SUPPLIERS["SUP_HOME_ESSENTIALS"]
    ),
    "SKU_CARE_1_004": SKUItem(
        sku_id="SKU_CARE_1_004",
        name="Hydrating Hyaluronic Acid Serum 30ml",
        category="Personal Care",
        dept="Skincare",
        store_id="TX_2",
        unit_cost=6.50,
        selling_price=22.00,
        holding_cost_annual_rate=0.20,
        abc_category=ABCCategory.A,
        supplier=SUPPLIERS["SUP_PERSONAL_CARE"]
    ),
    "SKU_ELEC_1_015": SKUItem(
        sku_id="SKU_ELEC_1_015",
        name="Braided Fast-Charging USB-C Cable (2-Pack)",
        category="Electronics",
        dept="Accessories",
        store_id="CA_1",
        unit_cost=3.20,
        selling_price=12.99,
        holding_cost_annual_rate=0.15,
        abc_category=ABCCategory.C,
        supplier=SUPPLIERS["SUP_ELECTRONICS_DIRECT"]
    )
}

def get_sku_or_default(sku_id: str, store_id: str = "CA_1", price: float = 9.99) -> SKUItem:
    """Retrieves metadata from catalog or builds dynamic fallback SKU."""
    if sku_id in SAMPLE_CATALOG:
        return SAMPLE_CATALOG[sku_id]
    
    default_supplier = SUPPLIERS["SUP_NATURAL_ORGANICS"]
    unit_cost = round(price * 0.45, 2)
    return SKUItem(
        sku_id=sku_id,
        name=f"Commercial Product ({sku_id})",
        category="General",
        dept="Retail Goods",
        store_id=store_id,
        unit_cost=unit_cost,
        selling_price=price,
        holding_cost_annual_rate=0.20,
        abc_category=ABCCategory.B,
        supplier=default_supplier
    )

def get_all_catalog_skus() -> List[SKUItem]:
    return list(SAMPLE_CATALOG.values())
