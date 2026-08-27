from sqlalchemy import Column, String, DateTime, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from db import Base

class Scan(Base):
    __tablename__ = "scans"

    scan_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, default=datetime.utcnow)
    image_ref = Column(String, nullable=True)
    product_name = Column(String, nullable=True)
    category = Column(String, nullable=True)
    extracted_fields = Column(JSON, nullable=True)
    rule_results = Column(JSON, nullable=True)
    overall_status = Column(String, nullable=True)
    compliance_pct = Column(Float, nullable=True)