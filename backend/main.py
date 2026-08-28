from fastapi import FastAPI, HTTPException, Depends, Query, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
import shutil
import uuid as uuid_lib
import os
import sys

from db import engine, Base, get_db
import models
from schemas import ScanInput, ScanResult
from rules import run_rule_engine
from report_generator import generate_scan_pdf


# --------------------------------------------------
# Person 1 OCR module
# --------------------------------------------------

OCR_MODULE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "OCR_module",
)

sys.path.insert(0, os.path.abspath(OCR_MODULE_DIR))

from pipeline import process_label  # noqa: E402


# --------------------------------------------------
# Database
# --------------------------------------------------

Base.metadata.create_all(bind=engine)


# --------------------------------------------------
# FastAPI
# --------------------------------------------------

app = FastAPI()


# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://compliance-checker-three.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# Upload directory
# --------------------------------------------------

UPLOAD_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "uploads",
)

os.makedirs(UPLOAD_DIR, exist_ok=True)

app.mount(
    "/uploads",
    StaticFiles(directory=UPLOAD_DIR),
    name="uploads",
)


# --------------------------------------------------
# Health
# --------------------------------------------------

@app.get("/")
def read_root():
    return {"status": "backend is running"}


# --------------------------------------------------
# Database test
# --------------------------------------------------

@app.get("/test-db")
def test_db():
    try:
        with engine.connect():
            return {"database": "connected successfully"}
    except Exception as e:
        return {
            "database": "connection failed",
            "error": str(e),
        }


# --------------------------------------------------
# Rule engine test
# --------------------------------------------------

@app.post("/test-rules")
def test_rules(scan_input: ScanInput):
    return run_rule_engine(scan_input)


# --------------------------------------------------
# JSON scan endpoint
# --------------------------------------------------

@app.post("/scan", response_model=ScanResult)
def create_scan(
    scan_input: ScanInput,
    db: Session = Depends(get_db),
):
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
        "image_ref": new_scan.image_ref,
        "timestamp": new_scan.timestamp,
        "overall_status": result["overall_status"],
        "compliance_pct": result["compliance_pct"],
        "fields_passed": result["fields_passed"],
        "fields_total": result["fields_total"],
        "field_results": result["field_results"],
    }


# --------------------------------------------------
# Fallback OCR data
# --------------------------------------------------

FALLBACK_MOCK_OCR = {
    "mrp": {
        "detected": True,
        "value": "₹199",
        "says_inclusive_of_taxes": True,
        "text_height_pct": 3.1,
        "small_text_flag": False,
    },
    "net_qty": {
        "detected": True,
        "value": "500g",
        "text_height_pct": 1.8,
        "small_text_flag": True,
    },
    "mfg_date": {
        "detected": True,
        "value": "07/2025",
        "text_height_pct": 2.0,
        "small_text_flag": False,
    },
    "consumer_care": {
        "detected": False,
        "value": None,
        "text_height_pct": None,
        "small_text_flag": None,
    },
    "address": {
        "detected": True,
        "value": "ABC Foods Pvt Ltd, Bengaluru 560001",
        "text_height_pct": 1.5,
        "small_text_flag": False,
    },
    "best_before_date": {
        "detected": False,
        "value": None,
        "applicable": True,
        "text_height_pct": None,
        "small_text_flag": None,
    },
}


# --------------------------------------------------
# Normalize OCR output
#
# Your current OCR module appears to return:
#   net_quantity
#   manufacturer_address
#
# while ScanInput expects:
#   net_qty
#   address
#
# We normalize here so Person 1's code does not need
# to be changed.
# --------------------------------------------------

def normalize_ocr_fields(extracted_fields: dict) -> dict:
    fields = dict(extracted_fields)

    if "net_qty" not in fields and "net_quantity" in fields:
        fields["net_qty"] = fields.pop("net_quantity")

    if "address" not in fields and "manufacturer_address" in fields:
        fields["address"] = fields.pop("manufacturer_address")

    return fields


# --------------------------------------------------
# Image scan endpoint
# --------------------------------------------------

@app.post("/scan-with-image")
async def create_scan_with_image(
    image: UploadFile = File(...),
    product_name: str = Form(None),
    category: str = Form(None),
    db: Session = Depends(get_db),
):
    original_name = image.filename or "upload.jpg"

    if "." in original_name:
        file_extension = original_name.rsplit(".", 1)[-1].lower()
    else:
        file_extension = "jpg"

    unique_filename = (
        f"{uuid_lib.uuid4()}.{file_extension}"
    )

    file_path = os.path.join(
        UPLOAD_DIR,
        unique_filename,
    )

    # Save uploaded image
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    # --------------------------------------------------
    # Run real OCR
    # --------------------------------------------------

    ocr_used = "real"

    try:
        extracted_fields = process_label(file_path)

        # Normalize the current OCR module's field names
        extracted_fields = normalize_ocr_fields(
            extracted_fields
        )

    except Exception as e:
        print(
            "[OCR WARNING] process_label failed, "
            f"using fallback mock data: {e}"
        )

        extracted_fields = FALLBACK_MOCK_OCR
        ocr_used = "fallback_mock"

    # Helpful debug output during integration testing
    print(
        "[OCR RESULT KEYS]:",
        list(extracted_fields.keys())
    )

    # --------------------------------------------------
    # Build ScanInput
    # --------------------------------------------------

    scan_input = ScanInput(
        product_name=product_name,
        category=category,
        **extracted_fields,
    )

    # --------------------------------------------------
    # Run rule engine
    # --------------------------------------------------

    result = run_rule_engine(scan_input)

    # --------------------------------------------------
    # Save scan
    # --------------------------------------------------

    image_ref = f"uploads/{unique_filename}"

    new_scan = models.Scan(
        product_name=product_name,
        category=category,
        image_ref=image_ref,
        extracted_fields=scan_input.dict(),
        rule_results=result["field_results"],
        overall_status=result["overall_status"],
        compliance_pct=result["compliance_pct"],
    )

    db.add(new_scan)
    db.commit()
    db.refresh(new_scan)

    # --------------------------------------------------
    # Return scan result
    # --------------------------------------------------

    return {
        "scan_id": new_scan.scan_id,
        "product_name": new_scan.product_name,
        "image_ref": new_scan.image_ref,
        "timestamp": new_scan.timestamp,
        "overall_status": result["overall_status"],
        "compliance_pct": result["compliance_pct"],
        "fields_passed": result["fields_passed"],
        "fields_total": result["fields_total"],
        "field_results": result["field_results"],
        "violations": result["violations"],
        "readability_notes": result["readability_notes"],
        "ocr_source": ocr_used,
    }


# --------------------------------------------------
# Get saved scan
# --------------------------------------------------

@app.get(
    "/scan/{scan_id}",
    response_model=ScanResult,
)
def get_scan(
    scan_id: str,
    db: Session = Depends(get_db),
):
    scan = (
        db.query(models.Scan)
        .filter(models.Scan.scan_id == scan_id)
        .first()
    )

    if not scan:
        raise HTTPException(
            status_code=404,
            detail="Scan not found",
        )

    # Use the already stored rule results.
    # Do NOT run the OCR again.
    field_results = scan.rule_results or []

    fields_total = len(field_results)

    fields_passed = sum(
        1
        for field_result in field_results
        if field_result.get("status") == "pass"
    )

    return {
        "scan_id": scan.scan_id,
        "product_name": scan.product_name,
        "image_ref": scan.image_ref,
        "timestamp": scan.timestamp,
        "overall_status": scan.overall_status,
        "compliance_pct": scan.compliance_pct,
        "fields_passed": fields_passed,
        "fields_total": fields_total,
        "field_results": field_results,
    }


# --------------------------------------------------
# PDF report
# --------------------------------------------------

@app.get("/scan/{scan_id}/report.pdf")
def download_scan_report(
    scan_id: str,
    db: Session = Depends(get_db),
):
    scan = (
        db.query(models.Scan)
        .filter(models.Scan.scan_id == scan_id)
        .first()
    )

    if not scan:
        raise HTTPException(
            status_code=404,
            detail="Scan not found",
        )

    scan_input = ScanInput(
        **scan.extracted_fields
    )

    result = run_rule_engine(scan_input)

    pdf_buffer = generate_scan_pdf(
        scan,
        result,
    )

    filename = (
        f"compliance_report_{scan.scan_id}.pdf"
    )

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                f"attachment; filename={filename}"
        },
    )


# --------------------------------------------------
# List scans
# --------------------------------------------------

@app.get("/scans")
def list_scans(
    status: Optional[str] = Query(
        None,
        description="compliant or non-compliant",
    ),
    search: Optional[str] = Query(
        None,
        description="search by product name",
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(
        10,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
):
    query = db.query(models.Scan)

    if status:
        query = query.filter(
            models.Scan.overall_status == status
        )

    if search:
        query = query.filter(
            models.Scan.product_name.ilike(
                f"%{search}%"
            )
        )

    total = query.count()

    scans = (
        query
        .order_by(models.Scan.timestamp.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    results = [
        {
            "scan_id": scan.scan_id,
            "product_name": scan.product_name,
            "category": scan.category,
            "timestamp": scan.timestamp,
            "overall_status": scan.overall_status,
            "compliance_pct": scan.compliance_pct,
        }
        for scan in scans
    ]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "scans": results,
    }


# --------------------------------------------------
# Dashboard stats
# --------------------------------------------------

@app.get("/dashboard/stats")
def dashboard_stats(
    db: Session = Depends(get_db),
):
    all_scans = db.query(models.Scan).all()

    total_scans = len(all_scans)

    if total_scans == 0:
        return {
            "total_scans": 0,
            "compliant_pct": 0,
            "top_violation": None,
            "violations_this_week": 0,
        }

    compliance_values = [
        scan.compliance_pct
        for scan in all_scans
        if scan.compliance_pct is not None
    ]

    compliant_pct = (
        round(
            sum(compliance_values)
            / len(compliance_values),
            1,
        )
        if compliance_values
        else 0
    )

    field_fail_counts = {}

    for scan in all_scans:
        if not scan.rule_results:
            continue

        for field_result in scan.rule_results:
            if field_result.get("status") == "fail":
                label = field_result.get(
                    "label",
                    field_result.get("field"),
                )

                field_fail_counts[label] = (
                    field_fail_counts.get(label, 0)
                    + 1
                )

    top_violation = (
        max(
            field_fail_counts,
            key=field_fail_counts.get,
        )
        if field_fail_counts
        else None
    )

    one_week_ago = (
        datetime.utcnow()
        - timedelta(days=7)
    )

    violations_this_week = sum(
        1
        for scan in all_scans
        if (
            scan.timestamp
            and scan.timestamp >= one_week_ago
            and scan.overall_status
            == "non-compliant"
        )
    )

    return {
        "total_scans": total_scans,
        "compliant_pct": compliant_pct,
        "top_violation": top_violation,
        "violations_this_week": violations_this_week,
    }


# --------------------------------------------------
# Analytics
# --------------------------------------------------

@app.get("/analytics")
def analytics(
    db: Session = Depends(get_db),
):
    all_scans = db.query(models.Scan).all()

    today = datetime.utcnow().date()

    daily_compliance = {
        (today - timedelta(days=i)).isoformat(): []
        for i in range(6, -1, -1)
    }

    for scan in all_scans:
        if (
            not scan.timestamp
            or scan.compliance_pct is None
        ):
            continue

        key = scan.timestamp.date().isoformat()

        if key in daily_compliance:
            daily_compliance[key].append(
                scan.compliance_pct
            )

    compliance_over_time = [
        {
            "date": day,
            "compliance_pct": (
                round(
                    sum(values) / len(values),
                    1,
                )
                if values
                else 0
            ),
        }
        for day, values
        in daily_compliance.items()
    ]

    field_fail_counts = {}

    for scan in all_scans:
        if not scan.rule_results:
            continue

        for field_result in scan.rule_results:
            if field_result.get("status") == "fail":
                label = field_result.get(
                    "label",
                    field_result.get("field"),
                )

                field_fail_counts[label] = (
                    field_fail_counts.get(label, 0)
                    + 1
                )

    violation_breakdown = [
        {
            "field": label,
            "count": count,
        }
        for label, count
        in sorted(
            field_fail_counts.items(),
            key=lambda x: -x[1],
        )
    ]

    category_counts = {}

    for scan in all_scans:
        category = (
            scan.category
            or "Uncategorized"
        )

        category_counts[category] = (
            category_counts.get(category, 0)
            + 1
        )

    scans_by_category = [
        {
            "category": category,
            "count": count,
        }
        for category, count
        in category_counts.items()
    ]

    return {
        "compliance_over_time":
            compliance_over_time,
        "violation_breakdown":
            violation_breakdown,
        "scans_by_category":
            scans_by_category,
    }