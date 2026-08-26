import json
from typing import List, Optional, Dict, Any
from datetime import datetime
try:
    from db.session import SessionLocal
    from db.models import PurchaseOrderModel, SKUInventoryStateModel
except ImportError:
    from src.db.session import SessionLocal
    from src.db.models import PurchaseOrderModel, SKUInventoryStateModel


def save_purchase_orders(pos: List[Any], db_session=None) -> List[Dict[str, Any]]:
    """
    Saves or updates generated purchase orders in the database.
    Accepts list of PurchaseOrder dataclass instances or dicts.
    """
    session = db_session or SessionLocal()
    saved_records = []

    try:
        for po in pos:
            # Handle dataclass vs dict
            if hasattr(po, "__dict__"):
                po_dict = po.__dict__.copy()
            elif isinstance(po, dict):
                po_dict = po.copy()
            else:
                continue

            po_id = po_dict.get("po_id")
            if not po_id:
                continue

            supplier_id = po_dict.get("supplier_id", "SUP_UNKNOWN")
            supplier_name = po_dict.get("supplier_name", "Unknown Supplier")
            status = po_dict.get("status", "DRAFT")
            total_units = int(po_dict.get("total_units", 0))
            total_estimated_cost = float(po_dict.get("total_estimated_cost", 0.0))
            items = po_dict.get("items", [])
            items_json = json.dumps(items)

            # Check if record already exists
            existing = session.query(PurchaseOrderModel).filter_by(po_id=po_id).first()
            if existing:
                existing.supplier_id = supplier_id
                existing.supplier_name = supplier_name
                existing.status = status
                existing.total_units = total_units
                existing.total_estimated_cost = total_estimated_cost
                existing.items_json = items_json
                record = existing
            else:
                record = PurchaseOrderModel(
                    po_id=po_id,
                    supplier_id=supplier_id,
                    supplier_name=supplier_name,
                    status=status,
                    total_units=total_units,
                    total_estimated_cost=total_estimated_cost,
                    items_json=items_json,
                    created_at=datetime.utcnow()
                )
                session.add(record)

            session.commit()
            session.refresh(record)
            saved_records.append(record.to_dict())

        return saved_records
    except Exception as e:
        session.rollback()
        raise e
    finally:
        if db_session is None:
            session.close()

def get_all_purchase_orders(limit: int = 100, db_session=None) -> List[Dict[str, Any]]:
    """Retrieves list of purchase orders ordered by creation date (newest first)."""
    session = db_session or SessionLocal()
    try:
        records = session.query(PurchaseOrderModel).order_by(PurchaseOrderModel.created_at.desc()).limit(limit).all()
        return [r.to_dict() for r in records]
    finally:
        if db_session is None:
            session.close()

def get_purchase_order_by_id(po_id: str, db_session=None) -> Optional[Dict[str, Any]]:
    """Finds a single purchase order by its po_id."""
    session = db_session or SessionLocal()
    try:
        record = session.query(PurchaseOrderModel).filter_by(po_id=po_id).first()
        return record.to_dict() if record else None
    finally:
        if db_session is None:
            session.close()

def upsert_sku_state(
    sku_id: str,
    store_id: str = "CA_1",
    on_hand_units: int = 0,
    in_transit_units: int = 0,
    reorder_point: float = 0.0,
    safety_stock: float = 0.0,
    risk_level: str = "HEALTHY",
    db_session=None
) -> Dict[str, Any]:
    """Upserts SKU inventory state balance into relational database."""
    session = db_session or SessionLocal()
    try:
        record = session.query(SKUInventoryStateModel).filter_by(sku_id=sku_id, store_id=store_id).first()
        if record:
            record.on_hand_units = on_hand_units
            record.in_transit_units = in_transit_units
            record.reorder_point = reorder_point
            record.safety_stock = safety_stock
            record.risk_level = risk_level
            record.last_updated = datetime.utcnow()
        else:
            record = SKUInventoryStateModel(
                sku_id=sku_id,
                store_id=store_id,
                on_hand_units=on_hand_units,
                in_transit_units=in_transit_units,
                reorder_point=reorder_point,
                safety_stock=safety_stock,
                risk_level=risk_level,
                last_updated=datetime.utcnow()
            )
            session.add(record)

        session.commit()
        session.refresh(record)
        return record.to_dict()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        if db_session is None:
            session.close()

def get_sku_state(sku_id: str, store_id: str = "CA_1", db_session=None) -> Optional[Dict[str, Any]]:
    """Retrieves single SKU state by sku_id and store_id."""
    session = db_session or SessionLocal()
    try:
        record = session.query(SKUInventoryStateModel).filter_by(sku_id=sku_id, store_id=store_id).first()
        return record.to_dict() if record else None
    finally:
        if db_session is None:
            session.close()
