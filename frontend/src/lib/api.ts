export interface ComplianceField {
  field_name: string;
  detected_value: string | null;
  status: "pass" | "fail" | "not_detected";
  reason: string | null;
}

export interface ScanResult {
  scan_id: string;
  product_image_url: string;
  product_name: string;
  scanned_at: string;
  overall_compliance_percent: number;
  fields: ComplianceField[];
}

const BACKEND_URL = "http://127.0.0.1:8000";

// --------------------------------------------------
// Upload image -> Backend -> OCR -> Rule Engine -> DB
// --------------------------------------------------
export async function uploadLabel(file: File): Promise<ScanResult> {
  const formData = new FormData();

  formData.append("image", file);

  const response = await fetch(`${BACKEND_URL}/scan-with-image`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorText = await response.text();

    throw new Error(
      `Scan failed (${response.status}): ${errorText}`
    );
  }

  const data = await response.json();

  console.log("REAL BACKEND SCAN RESPONSE:", data);

  if (!data.scan_id) {
    throw new Error("Backend did not return a scan_id.");
  }

  return {
    scan_id: data.scan_id,
    product_image_url: data.image_ref
      ? `${BACKEND_URL}/${data.image_ref}`
      : "",
    product_name: data.product_name ?? "Uploaded Product",
    scanned_at: data.timestamp ?? new Date().toISOString(),
    overall_compliance_percent: Number(data.compliance_pct ?? 0),

    fields: (data.field_results ?? []).map((field: any) => ({
      field_name: field.label ?? field.field ?? "Unknown Field",
      detected_value: field.detected_value ?? null,
      status:
        field.status === "pass"
          ? "pass"
          : field.status === "fail"
          ? "fail"
          : "not_detected",
      reason: field.reason ?? null,
    })),
  };
}

// --------------------------------------------------
// Get one real scan from backend
// --------------------------------------------------
export async function getScanResult(
  scanId: string
): Promise<ScanResult> {
  if (!scanId || scanId === "undefined") {
    throw new Error("Invalid scan ID.");
  }

  const response = await fetch(
    `${BACKEND_URL}/scan/${scanId}`,
    {
      method: "GET",
      cache: "no-store",
    }
  );

  if (!response.ok) {
    const errorText = await response.text();

    throw new Error(
      `Could not fetch scan (${response.status}): ${errorText}`
    );
  }

  const data = await response.json();

  return {
    scan_id: data.scan_id,
    product_image_url: data.image_ref
      ? `${BACKEND_URL}/${data.image_ref}`
      : "",
    product_name: data.product_name ?? "Uploaded Product",
    scanned_at: data.timestamp ?? new Date().toISOString(),
    overall_compliance_percent: Number(data.compliance_pct ?? 0),

    fields: (data.field_results ?? []).map((field: any) => ({
      field_name: field.label ?? field.field ?? "Unknown Field",
      detected_value: field.detected_value ?? null,
      status:
        field.status === "pass"
          ? "pass"
          : field.status === "fail"
          ? "fail"
          : "not_detected",
      reason: field.reason ?? null,
    })),
  };
}

// --------------------------------------------------
// Dashboard - still mock for now
// --------------------------------------------------
export async function getDashboardStats() {
  return {
    totalScans: 0,
    compliantPercent: 0,
    mostCommonViolation: "None",
    violationsThisWeek: 0,
  };
}

// --------------------------------------------------
// Recent scans - still mock for now
// --------------------------------------------------
export async function getRecentScans() {
  return [];
}

// --------------------------------------------------
// Analytics - still mock for now
// --------------------------------------------------
export async function getAnalyticsData() {
  return {
    complianceOverTime: [],
    violationsBreakdown: [],
    categoryScans: [],
  };
}