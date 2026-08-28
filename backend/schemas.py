from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# ---- OCR field shapes (Person 1's finalized contract) ----

class OCRField(BaseModel):
    detected: bool
    value: Optional[str] = None
    text_height_pct: Optional[float] = None
    small_text_flag: Optional[bool] = None


class MRPField(OCRField):
    says_inclusive_of_taxes: bool = False


class BestBeforeField(OCRField):
    applicable: bool = True


# ---- Request body for /scan, /test-rules, /scan-with-image ----

class ScanInput(BaseModel):
    product_name: Optional[str] = None
    category: Optional[str] = None

    mrp: MRPField
    net_quantity: OCRField
    mfg_date: OCRField
    consumer_care: OCRField
    manufacturer_address: OCRField
    best_before_date: BestBeforeField


# ---- Response models ----

class FieldResult(BaseModel):
    field: str
    label: str
    tier: str
    rule: str
    status: str
    detected_value: Optional[str] = None


class ReadabilityNote(BaseModel):
    field: str
    label: str
    text_height_pct: float
    small_text_flag: bool


class Violation(BaseModel):
    rule: str
    description: str


class ScanResult(BaseModel):
    scan_id: UUID
    product_name: Optional[str] = None
    timestamp: Optional[datetime] = None
    overall_status: str
    compliance_pct: int
    fields_passed: int
    fields_total: int
    field_results: List[FieldResult]
    violations: Optional[List[Violation]] = None
    readability_notes: Optional[List[ReadabilityNote]] = None