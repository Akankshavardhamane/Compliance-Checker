from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from db import engine, Base, get_db
import models
from schemas import ScanInput, ScanResult
from rules import run_rule_engine

Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.get("/")
def read_root():
    return {"status": "backend is running"}


@app.get("/test-db")
def test_db():
    try:
        with engine.connect() as connection:
            return {"database": "connected successfully"}
    except Exception as e:
        return {"database": "connection failed", "error": str(e)}


@app.post("/test-rules")
def test_rules(scan_input: ScanInput):
    return run_rule_engine(scan_input)


@app.post("/scan", response_model=ScanResult)
def create_scan(scan_input: ScanInput, db: Session = Depends(get_db)):
    result = run_rule_engine(scan_input)

    new_scan = models.Scan(
        product_name=scan_input.product_name,
        category=scan_input.category,
        image_ref=None,
        extracted_fields=scan_input.dict(),
        rule_results=result["field_results"],
        overall_status=result["overall_status"],
        compliance_pct=result["compliance_pct"],
    )
    db.add(new_scan)
    db.commit()
    db.refresh(new_scan)

    return {
        "scan_id": new_scan.scan_id,
        "product_name": new_scan.product_name,
        "timestamp": new_scan.timestamp,
        "overall_status": result["overall_status"],
        "compliance_pct": result["compliance_pct"],
        "fields_passed": result["fields_passed"],
        "fields_total": result["fields_total"],
        "field_results": result["field_results"],
    }


@app.get("/scan/{scan_id}", response_model=ScanResult)
def get_scan(scan_id: str, db: Session = Depends(get_db)):
    scan = db.query(models.Scan).filter(models.Scan.scan_id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    total = len(scan.rule_results) if scan.rule_results else 0
    passed = sum(1 for r in scan.rule_results if r["status"] == "pass") if scan.rule_results else 0

    return {
        "scan_id": scan.scan_id,
        "product_name": scan.product_name,
        "timestamp": scan.timestamp,
        "overall_status": scan.overall_status,
        "compliance_pct": scan.compliance_pct,
        "fields_passed": passed,
        "fields_total": total,
        "field_results": scan.rule_results,
    }


@app.get("/scans")
def list_scans(
    status: Optional[str] = Query(None, description="compliant, non-compliant, or exempt"),
    search: Optional[str] = Query(None, description="search by product name"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(models.Scan)

    if status:
        query = query.filter(models.Scan.overall_status == status)

    if search:
        query = query.filter(models.Scan.product_name.ilike(f"%{search}%"))

    total = query.count()

    scans = (
        query.order_by(models.Scan.timestamp.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    results = []
    for scan in scans:
        results.append({
            "scan_id": scan.scan_id,
            "product_name": scan.product_name,
            "category": scan.category,
            "timestamp": scan.timestamp,
            "overall_status": scan.overall_status,
            "compliance_pct": scan.compliance_pct,
        })

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "scans": results,
    }