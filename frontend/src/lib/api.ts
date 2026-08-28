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

const mockScanResult: ScanResult = {
  scan_id: "scan_001",
  product_image_url: "/mock/product1.jpg",
  product_name: "Sample Biscuit Pack",
  scanned_at: "2026-08-27T10:30:00Z",
  overall_compliance_percent: 80,
  fields: [
    {
      field_name: "MRP",
      detected_value: "₹45.00 incl. of all taxes",
      status: "pass",
      reason: null,
    },
    {
      field_name: "Net Quantity",
      detected_value: "100g",
      status: "pass",
      reason: null,
    },
    {
      field_name: "Manufacturing Date",
      detected_value: null,
      status: "fail",
      reason: "Manufacturing date not detected on label",
    },
    {
      field_name: "Manufacturer Address",
      detected_value: "XYZ Foods Pvt Ltd, Bangalore - 560001",
      status: "pass",
      reason: null,
    },
    {
      field_name: "Consumer Care",
      detected_value: "1800-XXX-XXXX",
      status: "fail",
      reason: "Font size below minimum readability requirement",
    },
  ],
};

export async function uploadLabel(file: File): Promise<ScanResult> {
  // Simulate network delay
  await new Promise((resolve) => setTimeout(resolve, 2500));
  return mockScanResult;
}

export async function getScanResult(scanId: string): Promise<ScanResult> {
  // Simulate network delay
  await new Promise((resolve) => setTimeout(resolve, 500));
  return mockScanResult;
}

export async function getDashboardStats() {
  await new Promise((resolve) => setTimeout(resolve, 500));
  return {
    totalScans: 124,
    compliantPercent: 80,
    mostCommonViolation: "Manufacturing date not detected",
    violationsThisWeek: 15,
  };
}

export async function getRecentScans() {
  await new Promise((resolve) => setTimeout(resolve, 500));
  return [
    mockScanResult,
    {
      ...mockScanResult,
      scan_id: "scan_002",
      product_name: "Premium Chips",
      overall_compliance_percent: 100,
      scanned_at: "2026-08-26T14:20:00Z",
      fields: mockScanResult.fields.map((f) => ({ ...f, status: "pass", reason: null })),
    },
  ];
}

export async function getAnalyticsData() {
  await new Promise((resolve) => setTimeout(resolve, 600));
  return {
    complianceOverTime: [
      { date: 'Aug 21', rate: 75 },
      { date: 'Aug 22', rate: 78 },
      { date: 'Aug 23', rate: 82 },
      { date: 'Aug 24', rate: 79 },
      { date: 'Aug 25', rate: 85 },
      { date: 'Aug 26', rate: 88 },
      { date: 'Aug 27', rate: 91 },
    ],
    violationsBreakdown: [
      { name: 'Manufacturing Date', value: 40 },
      { name: 'Consumer Care', value: 30 },
      { name: 'MRP Info', value: 15 },
      { name: 'Net Quantity', value: 10 },
      { name: 'Other', value: 5 },
    ],
    categoryScans: [
      { category: 'Snacks', scans: 120 },
      { category: 'Beverages', scans: 85 },
      { category: 'Dairy', scans: 65 },
      { category: 'Personal Care', scans: 45 },
      { category: 'Groceries', scans: 30 },
    ]
  };
}
