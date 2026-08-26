import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class PurchaseOrderModel(Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    po_id = Column(String(64), unique=True, index=True, nullable=False)
    supplier_id = Column(String(64), index=True, nullable=False)
    supplier_name = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(32), default="DRAFT", nullable=False)
    total_units = Column(Integer, nullable=False)
    total_estimated_cost = Column(Float, nullable=False)
    items_json = Column(Text, nullable=False)

    def to_dict(self):
        items = []
        if self.items_json:
            try:
                items = json.loads(self.items_json)
            except Exception:
                items = []

        return {
            "po_id": self.po_id,
            "supplier_id": self.supplier_id,
            "supplier_name": self.supplier_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "status": self.status,
            "total_units": self.total_units,
            "total_estimated_cost": self.total_estimated_cost,
            "items": items
        }

class SKUInventoryStateModel(Base):
    __tablename__ = "sku_inventory_states"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sku_id = Column(String(64), index=True, nullable=False)
    store_id = Column(String(64), default="CA_1", nullable=False)
    on_hand_units = Column(Integer, default=0, nullable=False)
    in_transit_units = Column(Integer, default=0, nullable=False)
    reorder_point = Column(Float, default=0.0)
    safety_stock = Column(Float, default=0.0)
    risk_level = Column(String(32), default="HEALTHY")
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "sku_id": self.sku_id,
            "store_id": self.store_id,
            "on_hand_units": self.on_hand_units,
            "in_transit_units": self.in_transit_units,
            "reorder_point": self.reorder_point,
            "safety_stock": self.safety_stock,
            "risk_level": self.risk_level,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None
        }
