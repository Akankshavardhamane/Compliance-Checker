import { getScanResult } from "@/lib/api";
import { CheckCircle2, XCircle, AlertTriangle, ArrowLeft, Download, ScanLine } from "lucide-react";
import Link from "next/link";
import { notFound } from "next/navigation";

export default async function ResultsPage({ params }: { params: { id: string } }) {
  const result = await getScanResult(params.id);

  if (!result) {
    notFound();
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "pass": return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      case "fail": return <XCircle className="h-5 w-5 text-red-500" />;
      default: return <AlertTriangle className="h-5 w-5 text-amber-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "pass": return <span className="text-xs font-medium text-green-700 bg-green-100 px-2 py-1 rounded-full">Pass ✅</span>;
      case "fail": return <span className="text-xs font-medium text-red-700 bg-red-100 px-2 py-1 rounded-full">Fail ❌</span>;
      default: return <span className="text-xs font-medium text-amber-700 bg-amber-100 px-2 py-1 rounded-full">Not Detected ⚠️</span>;
    }
  };

  const isCompliant = result.overall_compliance_percent === 100;

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <Link href="/" className="inline-flex items-center text-sm font-medium text-gray-500 hover:text-gray-900">
          <ArrowLeft className="h-4 w-4 mr-1" /> Back to Upload
        </Link>
        <div className="flex gap-3">
          <button className="inline-flex items-center px-4 py-2 bg-white border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50">
            <Download className="h-4 w-4 mr-2" /> Download Report (PDF)
          </button>
          <Link href="/" className="inline-flex items-center px-4 py-2 bg-black text-white rounded-md text-sm font-medium hover:bg-gray-800">
            <ScanLine className="h-4 w-4 mr-2" /> Scan Another Product
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 flex flex-col items-center">
            <div className="w-full aspect-square bg-gray-100 rounded-lg mb-6 overflow-hidden flex items-center justify-center border border-gray-200">
               <span className="text-gray-400">Product Image</span>
            </div>
            <h2 className="text-xl font-bold text-gray-900 text-center mb-1">{result.product_name}</h2>
            <p className="text-sm text-gray-500 mb-6 text-center">Scan ID: {result.scan_id}</p>
            
            <div className={`w-full p-4 rounded-xl text-center border ${isCompliant ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
              <div className="text-sm font-medium mb-1 text-gray-700">Overall Compliance</div>
              <div className={`text-4xl font-bold ${isCompliant ? 'text-green-600' : 'text-red-600'}`}>
                {result.overall_compliance_percent}%
              </div>
            </div>
          </div>
        </div>

        <div className="lg:col-span-2">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
              <h3 className="font-semibold text-gray-800">Compliance Details</h3>
            </div>
            <div className="divide-y divide-gray-100">
              {result.fields.map((field, idx) => (
                <div key={idx} className="p-6 hover:bg-gray-50 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex gap-3">
                      <div className="mt-0.5">{getStatusIcon(field.status)}</div>
                      <div>
                        <h4 className="font-medium text-gray-900 mb-1">{field.field_name}</h4>
                        <div className="text-sm text-gray-600 mb-2">
                          <span className="font-medium">Detected:</span> {field.detected_value || "None"}
                        </div>
                        {field.reason && (
                          <div className="text-sm text-red-600 bg-red-50 p-2 rounded border border-red-100">
                            {field.reason}
                          </div>
                        )}
                      </div>
                    </div>
                    <div>
                      {getStatusBadge(field.status)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
