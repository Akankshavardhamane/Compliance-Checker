import Link from "next/link";
import { Search, LayoutDashboard, UploadCloud, Bell, ChevronDown, BarChart2 } from "lucide-react";

export default function Navigation() {
  return (
    <nav className="bg-white/80 backdrop-blur-md border-b border-slate-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link href="/" className="flex items-center gap-3 group">
              <div className="bg-gradient-to-br from-slate-900 to-slate-800 p-2 rounded-xl flex items-center justify-center shadow-md shadow-slate-900/10 group-hover:shadow-lg transition-all duration-300">
                <Search className="h-5 w-5 text-white" />
              </div>
              <div className="flex flex-col">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-slate-900 text-sm leading-tight tracking-tight">Legal Metrology AI</span>
                  <span className="bg-blue-100 text-blue-700 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider">Beta</span>
                </div>
                <span className="text-xs text-slate-500 font-medium leading-tight">Compliance Checker</span>
              </div>
            </Link>
          </div>
          <div className="flex items-center space-x-2 sm:space-x-4">
            <Link
              href="/dashboard"
              className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-semibold text-slate-600 transition-colors hover:bg-slate-50 hover:text-slate-900"
            >
              <LayoutDashboard className="h-4 w-4" />
              <span className="hidden sm:inline">Dashboard</span>
            </Link>
            <Link
              href="/analytics"
              className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-semibold bg-slate-100 text-slate-900 transition-colors hover:bg-slate-200"
            >
              <BarChart2 className="h-4 w-4" />
              <span className="hidden sm:inline">Analytics</span>
            </Link>
            <Link
              href="/"
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold text-white bg-slate-900 hover:bg-slate-800 shadow-md shadow-slate-900/20 transition-all duration-300 hover:shadow-lg hover:-translate-y-0.5"
            >
              <UploadCloud className="h-4 w-4" />
              <span className="hidden sm:inline">Upload Label</span>
            </Link>
            
            <div className="h-6 w-px bg-slate-200 mx-2 hidden sm:block"></div>
            
            <button className="p-2 rounded-full text-slate-500 hover:text-slate-900 hover:bg-slate-100 transition-colors relative">
              <Bell className="h-5 w-5" />
              <span className="absolute top-2 right-2.5 h-2 w-2 bg-red-500 rounded-full ring-2 ring-white"></span>
            </button>
            
            <button className="flex items-center gap-2 p-1.5 rounded-full hover:bg-slate-100 transition-colors">
              <div className="h-8 w-8 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500 border-2 border-white shadow-sm"></div>
              <ChevronDown className="h-4 w-4 text-slate-500 hidden sm:block" />
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}
