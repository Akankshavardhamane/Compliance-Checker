import { getDashboardStats, getRecentScans } from "@/lib/api";
import { ClipboardList, Percent, AlertCircle, Calendar, ChevronRight, Search, TrendingUp, TrendingDown, Calendar as CalendarIcon, Download, MoreHorizontal } from "lucide-react";
import Link from "next/link";

export default async function DashboardPage() {
  const [stats, scans] = await Promise.all([getDashboardStats(), getRecentScans()]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 lg:py-12 bg-[#F8FAFC] min-h-screen">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-10 gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight mb-1">Dashboard</h1>
          <p className="text-slate-500 font-medium">Overview of all label compliance scans.</p>
        </div>
        <div className="flex items-center gap-3">
          <button className="hidden sm:flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 text-slate-700 text-sm font-semibold rounded-lg shadow-sm hover:bg-slate-50 hover:shadow-md transition-all">
            <CalendarIcon className="h-4 w-4 text-slate-500" />
            Last 30 Days
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 text-slate-700 text-sm font-semibold rounded-lg shadow-sm hover:bg-slate-50 hover:shadow-md transition-all">
            <Download className="h-4 w-4 text-slate-500" />
            Export CSV
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
        {/* Total Scans Card */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-all group">
          <div className="flex justify-between items-start mb-4">
            <div className="bg-blue-50 text-blue-600 p-2.5 rounded-xl group-hover:scale-110 transition-transform">
              <ClipboardList className="h-5 w-5" />
            </div>
            <span className="flex items-center gap-1 text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-1 rounded-full">
              <TrendingUp className="h-3 w-3" /> +12.5%
            </span>
          </div>
          <div>
            <div className="text-slate-500 text-sm font-semibold mb-1">Total Scans</div>
            <div className="text-3xl font-bold text-slate-900 tracking-tight">{stats.totalScans}</div>
          </div>
        </div>
        
        {/* Compliant % Card */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-all group">
          <div className="flex justify-between items-start mb-4">
            <div className="bg-emerald-50 text-emerald-600 p-2.5 rounded-xl group-hover:scale-110 transition-transform">
              <Percent className="h-5 w-5" />
            </div>
            <span className="flex items-center gap-1 text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-1 rounded-full">
              <TrendingUp className="h-3 w-3" /> +4.2%
            </span>
          </div>
          <div>
            <div className="text-slate-500 text-sm font-semibold mb-1">Compliant %</div>
            <div className="text-3xl font-bold text-slate-900 tracking-tight flex items-end gap-2">
              {stats.compliantPercent}%
              <div className="w-24 h-2 bg-slate-100 rounded-full mb-2 overflow-hidden">
                <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${stats.compliantPercent}%` }}></div>
              </div>
            </div>
          </div>
        </div>

        {/* Most Common Violation Card */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-all group">
          <div className="flex justify-between items-start mb-4">
            <div className="bg-amber-50 text-amber-600 p-2.5 rounded-xl group-hover:scale-110 transition-transform">
              <AlertCircle className="h-5 w-5" />
            </div>
            <span className="flex items-center gap-1 text-xs font-bold text-slate-600 bg-slate-100 px-2 py-1 rounded-full">
              Attention
            </span>
          </div>
          <div>
            <div className="text-slate-500 text-sm font-semibold mb-1">Top Violation</div>
            <div className="text-base font-bold text-slate-800 leading-tight truncate" title={stats.mostCommonViolation}>
              {stats.mostCommonViolation}
            </div>
          </div>
        </div>

        {/* Violations This Week Card */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-all group">
          <div className="flex justify-between items-start mb-4">
            <div className="bg-rose-50 text-rose-600 p-2.5 rounded-xl group-hover:scale-110 transition-transform">
              <Calendar className="h-5 w-5" />
            </div>
            <span className="flex items-center gap-1 text-xs font-bold text-rose-600 bg-rose-50 px-2 py-1 rounded-full">
              <TrendingDown className="h-3 w-3" /> -2.1%
            </span>
          </div>
          <div>
            <div className="text-slate-500 text-sm font-semibold mb-1">Violations This Week</div>
            <div className="text-3xl font-bold text-slate-900 tracking-tight">{stats.violationsThisWeek}</div>
          </div>
        </div>
      </div>

      {/* Table Section */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {/* Table Header / Filters */}
        <div className="p-5 border-b border-slate-200 flex flex-col xl:flex-row justify-between items-start xl:items-center gap-4">
          <div className="flex bg-slate-100/80 p-1 rounded-xl border border-slate-200/60 w-full sm:w-auto overflow-x-auto">
            <button className="px-5 py-2 bg-white text-slate-900 text-sm font-semibold rounded-lg shadow-sm border border-slate-200/50 whitespace-nowrap">All Scans</button>
            <button className="px-5 py-2 text-slate-500 hover:text-slate-900 text-sm font-semibold rounded-lg transition-colors whitespace-nowrap">Compliant</button>
            <button className="px-5 py-2 text-slate-500 hover:text-slate-900 text-sm font-semibold rounded-lg transition-colors whitespace-nowrap">Non-compliant</button>
            <button className="px-5 py-2 text-slate-500 hover:text-slate-900 text-sm font-semibold rounded-lg transition-colors whitespace-nowrap">Flagged</button>
          </div>
          <div className="relative w-full xl:w-80 group">
            <Search className="h-4 w-4 text-slate-400 absolute left-3.5 top-1/2 transform -translate-y-1/2 group-focus-within:text-blue-500 transition-colors" />
            <input 
              type="text" 
              placeholder="Search products..." 
              className="w-full pl-10 pr-12 py-2.5 bg-white border border-slate-200 rounded-xl text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all shadow-sm"
            />
            <div className="absolute right-3 top-1/2 transform -translate-y-1/2 flex items-center gap-1">
              <kbd className="hidden sm:inline-flex items-center justify-center px-1.5 py-0.5 text-[10px] font-bold text-slate-400 bg-slate-100 border border-slate-200 rounded shadow-sm">⌘K</kbd>
            </div>
          </div>
        </div>

        {/* Data Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left whitespace-nowrap">
            <thead className="text-[11px] font-bold text-slate-400 uppercase tracking-wider bg-slate-50/50 border-b border-slate-200">
              <tr>
                <th className="px-6 py-4">Product</th>
                <th className="px-6 py-4">Scanned Date</th>
                <th className="px-6 py-4">Compliance Score</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {scans.map((scan, idx) => (
                <tr key={scan.scan_id} className="hover:bg-slate-50/80 transition-colors group">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-4">
                      <div className={`relative w-12 h-12 rounded-xl flex-shrink-0 flex items-center justify-center overflow-hidden border-2 shadow-sm ${scan.overall_compliance_percent === 100 ? 'border-emerald-100 bg-emerald-50/50' : 'border-rose-100 bg-rose-50/50'}`}>
                        {/* Status Indicator Ring (simulated with border) */}
                        <div className={`absolute top-0 right-0 w-2.5 h-2.5 rounded-full border-2 border-white ${scan.overall_compliance_percent === 100 ? 'bg-emerald-500' : 'bg-rose-500'}`}></div>
                        <span className="text-[10px] font-semibold text-slate-400">IMG</span>
                      </div>
                      <div>
                        <div className="font-bold text-slate-900 text-sm mb-0.5">{scan.product_name}</div>
                        <div className="text-xs font-medium text-slate-500">SKU: PRD-{1000 + idx}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="font-semibold text-slate-700 text-sm">
                      {new Date(scan.scanned_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}
                    </div>
                    <div className="text-xs font-medium text-slate-400 mt-0.5">
                      {idx === 0 ? "2 hours ago" : "1 day ago"}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="flex-1 max-w-[100px] h-2 bg-slate-100 rounded-full overflow-hidden">
                        <div 
                          className={`h-full rounded-full ${scan.overall_compliance_percent === 100 ? 'bg-emerald-500' : 'bg-amber-500'}`} 
                          style={{ width: `${scan.overall_compliance_percent}%` }}
                        ></div>
                      </div>
                      <span className="font-bold text-slate-700">{scan.overall_compliance_percent}%</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    {scan.overall_compliance_percent === 100 ? (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200/60 shadow-sm">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                        Compliant
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-rose-50 text-rose-700 border border-rose-200/60 shadow-sm">
                        <span className="w-1.5 h-1.5 rounded-full bg-rose-500"></span>
                        Violation Found
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Link 
                        href={`/results/${scan.scan_id}`} 
                        className="inline-flex items-center justify-center px-3 py-1.5 bg-white border border-slate-200 text-xs font-bold text-slate-700 rounded-lg hover:bg-slate-50 hover:text-blue-600 transition-colors shadow-sm"
                      >
                        View Details <ChevronRight className="h-3 w-3 ml-1" />
                      </Link>
                      <button className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors">
                        <MoreHorizontal className="h-4 w-4" />
                      </button>
                    </div>
                    {/* Fallback for when not hovering on mobile */}
                    <Link 
                        href={`/results/${scan.scan_id}`} 
                        className="xl:hidden inline-flex items-center justify-center text-xs font-bold text-blue-600 hover:text-blue-700 transition-colors"
                      >
                        View
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {/* Pagination Footer */}
        <div className="p-4 border-t border-slate-200 bg-slate-50/50 flex justify-between items-center text-sm">
          <span className="font-medium text-slate-500">Showing <span className="font-bold text-slate-900">1</span> to <span className="font-bold text-slate-900">2</span> of <span className="font-bold text-slate-900">124</span> scans</span>
          <div className="flex gap-2">
            <button className="px-3 py-1.5 border border-slate-200 bg-white text-slate-400 font-semibold rounded-lg cursor-not-allowed shadow-sm">Previous</button>
            <button className="px-3 py-1.5 border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 font-semibold rounded-lg shadow-sm transition-colors">Next</button>
          </div>
        </div>
      </div>
    </div>
  );
}
