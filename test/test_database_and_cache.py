import os
import sys
import pytest

# Ensure src directory is in sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

try:
    from db.session import init_db, SessionLocal
    from db.repository import (
        save_purchase_orders,
        get_all_purchase_orders,
        get_purchase_order_by_id,
        upsert_sku_state,
        get_sku_state
    )
    from db.cache import CacheManager
except ImportError:
    from src.db.session import init_db, SessionLocal
    from src.db.repository import (
        save_purchase_orders,
        get_all_purchase_orders,
        get_purchase_order_by_id,
        upsert_sku_state,
        get_sku_state
    )
    from src.db.cache import CacheManager

@pytest.fixture(autouse=True)
def setup_database():
    """Initializes schema before tests."""
    init_db()

def test_database_po_operations():
    test_po = {
        "po_id": "PO-TEST-9999",
        "supplier_id": "SUP_TEST_01",
        "supplier_name": "Test Roastery Co",
        "status": "APPROVED",
        "total_units": 150,
        "total_estimated_cost": 750.50,
        "items": [
            {
                "sku_id": "TEST_COFFEE_01",
                "sku_name": "Artisan Roast Coffee",
                "reorder_units": 150,
                "unit_cost": 5.00,
                "total_cost": 750.00
            }
        ]
    }

    # 1. Save PO
    saved = save_purchase_orders([test_po])
    assert len(saved) == 1
    assert saved[0]["po_id"] == "PO-TEST-9999"
    assert saved[0]["total_units"] == 150

    # 2. Fetch by ID
    fetched = get_purchase_order_by_id("PO-TEST-9999")
    assert fetched is not None
    assert fetched["supplier_name"] == "Test Roastery Co"
    assert len(fetched["items"]) == 1

    # 3. List all POs
    all_pos = get_all_purchase_orders()
    po_ids = [p["po_id"] for p in all_pos]
    assert "PO-TEST-9999" in po_ids

def test_sku_state_persistence():
    state = upsert_sku_state(
        sku_id="SKU_DB_TEST_01",
        store_id="CA_1",
        on_hand_units=45,
        in_transit_units=20,
        reorder_point=80.0,
        safety_stock=25.0,
        risk_level="REORDER_NOW"
    )

    assert state["sku_id"] == "SKU_DB_TEST_01"
    assert state["on_hand_units"] == 45
    assert state["risk_level"] == "REORDER_NOW"

    fetched = get_sku_state("SKU_DB_TEST_01", store_id="CA_1")
    assert fetched is not None
    assert fetched["in_transit_units"] == 20

def test_cache_manager_operations():
    cache = CacheManager(redis_url="redis://localhost:6379/9999")  # Force fallback or local

    # 1. Set & Get
    cache.set("test_key", {"status": "ok", "value": 123}, ttl_seconds=60)
    val = cache.get("test_key")
    assert val is not None
    assert val["status"] == "ok"
    assert val["value"] == 123

    # 2. Stats
    stats = cache.stats()
    assert stats["hits"] >= 1
    assert "backend" in stats

    # 3. Delete & Clear
    cache.delete("test_key")
    assert cache.get("test_key") is None
