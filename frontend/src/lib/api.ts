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

export interface DashboardScan {
  scan_id: string;
  product_name: string;
  scanned_at: string;
  overall_compliance_percent: number;
  overall_status: string;
}

export interface RecentScansResponse {
  total: number;
  page: number;
  page_size: number;
  scans: DashboardScan[];
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
// Get one real scan
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
// Dashboard stats -> REAL BACKEND
// --------------------------------------------------
export async function getDashboardStats() {
  const response = await fetch(
    `${BACKEND_URL}/dashboard/stats`,
    {
      method: "GET",
      cache: "no-store",
    }
  );

  if (!response.ok) {
    const errorText = await response.text();

    throw new Error(
      `Could not fetch dashboard stats (${response.status}): ${errorText}`
    );
  }

  const data = await response.json();

  return {
    totalScans: Number(data.total_scans ?? 0),
    compliantPercent: Number(data.compliant_pct ?? 0),
    mostCommonViolation: data.top_violation ?? "None",
    violationsThisWeek: Number(
      data.violations_this_week ?? 0
    ),
  };
}

// --------------------------------------------------
// Recent scans -> REAL BACKEND
// Supports:
// status, search, page and page_size
// --------------------------------------------------
export async function getRecentScans({
  status = "all",
  search = "",
  page = 1,
  pageSize = 10,
}: {
  status?: "all" | "compliant" | "non-compliant" | "flagged";
  search?: string;
  page?: number;
  pageSize?: number;
} = {}): Promise<RecentScansResponse> {
  const params = new URLSearchParams();

  if (status !== "all") {
    // Backend has no separate "flagged" status.
    // For now, Flagged means non-compliant / violation found.
    const backendStatus =
      status === "flagged"
        ? "non-compliant"
        : status;

    params.set("status", backendStatus);
  }

  if (search.trim()) {
    params.set("search", search.trim());
  }

  params.set("page", String(page));
  params.set("page_size", String(pageSize));

  const response = await fetch(
    `${BACKEND_URL}/scans?${params.toString()}`,
    {
      method: "GET",
      cache: "no-store",
    }
  );

  if (!response.ok) {
    const errorText = await response.text();

    throw new Error(
      `Could not fetch scans (${response.status}): ${errorText}`
    );
  }

  const data = await response.json();

  return {
    total: Number(data.total ?? 0),
    page: Number(data.page ?? page),
    page_size: Number(data.page_size ?? pageSize),
    scans: (data.scans ?? []).map((scan: any) => ({
      scan_id: scan.scan_id,
      product_name:
        scan.product_name ?? "Uploaded Product",
      scanned_at:
        scan.timestamp ?? new Date().toISOString(),
      overall_compliance_percent: Number(
        scan.compliance_pct ?? 0
      ),
      overall_status:
        scan.overall_status ?? "non-compliant",
    })),
  };
}

// --------------------------------------------------
// Analytics -> still mock for now
// --------------------------------------------------
export async function getAnalyticsData() {
  return {
    complianceOverTime: [],
    violationsBreakdown: [],
    categoryScans: [],
  };
}