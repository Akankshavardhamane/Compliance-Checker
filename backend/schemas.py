from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID

# ---- What Person 1's OCR module sends you ----
class FieldData(BaseModel):
    value: Optional[str] = None
    detected: bool = False
    confidence: Optional[float] = 0.0
    font_size_ok: Optional[bool] = None

class ScanInput(BaseModel):
    mrp: FieldData
    net_qty: FieldData
    mfg_date: FieldData
    address: FieldData
    consumer_care: FieldData
    country_of_origin: Optional[FieldData] = None
    is_imported: bool = False
    product_name: Optional[str] = None
    category: Optional[str] = None
    exemption: Optional[str] = None

# ---- What you send back to frontend ----
class FieldResult(BaseModel):
    field: str
    label: str
    status: str
    detected_value: Optional[str] = None
    reason: str

class ScanResult(BaseModel):
    scan_id: UUID
    product_name: Optional[str]
    timestamp: datetime
    overall_status: str
    compliance_pct: float
    fields_passed: int
    fields_total: int
    field_results: List[FieldResult]

    class Config:
        from_attributes = True