from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from db import engine, Base, get_db
import models
from schemas import ScanInput, ScanResult
from rules import run_rule_engine
from datetime import datetime, timedelta
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

@app.get("/dashboard/stats")
def dashboard_stats(db: Session = Depends(get_db)):
    all_scans = db.query(models.Scan).all()

    total_scans = len(all_scans)

    if total_scans == 0:
        return {
            "total_scans": 0,
            "compliant_pct": 0,
            "top_violation": None,
            "violations_this_week": 0,
        }

    # Compliant % — average compliance_pct across all scans
    compliance_values = [s.compliance_pct for s in all_scans if s.compliance_pct is not None]
    compliant_pct = round(sum(compliance_values) / len(compliance_values), 1) if compliance_values else 0

    # Top violation — most frequently failing field label across all scans
    field_fail_counts = {}
    for scan in all_scans:
        if not scan.rule_results:
            continue
        for field_result in scan.rule_results:
            if field_result.get("status") == "fail":
                label = field_result.get("label", field_result.get("field"))
                field_fail_counts[label] = field_fail_counts.get(label, 0) + 1

    top_violation = None
    if field_fail_counts:
        top_violation = max(field_fail_counts, key=field_fail_counts.get)

    # Violations this week — non-compliant scans in the last 7 days
    one_week_ago = datetime.utcnow() - timedelta(days=7)
    violations_this_week = sum(
        1 for s in all_scans
        if s.timestamp and s.timestamp >= one_week_ago and s.overall_status == "non-compliant"
    )

    return {
        "total_scans": total_scans,
        "compliant_pct": compliant_pct,
        "top_violation": top_violation,
        "violations_this_week": violations_this_week,
    }

@app.get("/analytics")
def analytics(db: Session = Depends(get_db)):
    all_scans = db.query(models.Scan).all()

    # ---- 1. Compliance over time (last 7 days) ----
    today = datetime.utcnow().date()
    daily_compliance = {}
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        daily_compliance[day.isoformat()] = []

    for scan in all_scans:
        if not scan.timestamp or scan.compliance_pct is None:
            continue
        scan_day = scan.timestamp.date()
        key = scan_day.isoformat()
        if key in daily_compliance:
            daily_compliance[key].append(scan.compliance_pct)

    compliance_over_time = []
    for day, values in daily_compliance.items():
        avg = round(sum(values) / len(values), 1) if values else 0
        compliance_over_time.append({"date": day, "compliance_pct": avg})

    # ---- 2. Violation breakdown by field ----
    field_fail_counts = {}
    for scan in all_scans:
        if not scan.rule_results:
            continue
        for field_result in scan.rule_results:
            if field_result.get("status") == "fail":
                label = field_result.get("label", field_result.get("field"))
                field_fail_counts[label] = field_fail_counts.get(label, 0) + 1

    violation_breakdown = [
        {"field": label, "count": count}
        for label, count in sorted(field_fail_counts.items(), key=lambda x: -x[1])
    ]

    # ---- 3. Scans by category ----
    category_counts = {}
    for scan in all_scans:
        cat = scan.category or "Uncategorized"
        category_counts[cat] = category_counts.get(cat, 0) + 1

    scans_by_category = [
        {"category": cat, "count": count}
        for cat, count in category_counts.items()
    ]

    return {
        "compliance_over_time": compliance_over_time,
        "violation_breakdown": violation_breakdown,
        "scans_by_category": scans_by_category,
    }