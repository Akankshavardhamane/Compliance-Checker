"use client";

import { useState, useEffect } from "react";
import { getAnalyticsData } from "@/lib/api";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";

import {
  TrendingUp,
  PieChart as PieChartIcon,
} from "lucide-react";

const COLORS = [
  "#10b981",
  "#f43f5e",
  "#f59e0b",
  "#3b82f6",
  "#8b5cf6",
];

export default function AnalyticsPage() {
  const [data, setData] = useState<any>(null);

  const [error, setError] =
    useState<string | null>(null);

  useEffect(() => {
    async function loadAnalytics() {
      try {
        setError(null);

        const result =
          await getAnalyticsData();

        setData(result);
      } catch (err) {
        console.error(err);

        setError(
          "Could not load analytics data."
        );
      }
    }

    loadAnalytics();
  }, []);

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[60vh] px-4">
        <div className="bg-red-50 border border-red-200 text-red-700 px-5 py-4 rounded-xl">
          {error}
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 lg:py-12 bg-[#F8FAFC] min-h-screen">
      {/* Header */}
      <div className="mb-10">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight mb-1">
            Analytics Overview
          </h1>

          <p className="text-slate-500 font-medium">
            Compliance trends and violation insights.
          </p>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Compliance Over Time */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-lg font-bold text-slate-900">
                Compliance Over Time
              </h2>

              <p className="text-sm text-slate-500">
                Daily compliance rate for the last 7 days
              </p>
            </div>

            <div className="bg-blue-50 p-2 rounded-lg text-blue-600">
              <TrendingUp className="h-5 w-5" />
            </div>
          </div>

          <div className="h-[300px] w-full">
            <ResponsiveContainer
              width="100%"
              height="100%"
            >
              <LineChart
                data={
                  data.complianceOverTime
                }
                margin={{
                  top: 5,
                  right: 20,
                  bottom: 5,
                  left: 0,
                }}
              >
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="#e2e8f0"
                  vertical={false}
                />

                <XAxis
                  dataKey="date"
                  axisLine={false}
                  tickLine={false}
                  tick={{
                    fill: "#64748b",
                    fontSize: 12,
                  }}
                  dy={10}
                />

                <YAxis
                  domain={[0, 100]}
                  axisLine={false}
                  tickLine={false}
                  tick={{
                    fill: "#64748b",
                    fontSize: 12,
                  }}
                  dx={-10}
                />

                <RechartsTooltip
                  contentStyle={{
                    borderRadius: "12px",
                    border:
                      "1px solid #e2e8f0",
                    boxShadow:
                      "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                  }}
                  formatter={(value: any) => [
                    `${value}%`,
                    "Compliance",
                  ]}
                />

                <Line
                  type="monotone"
                  dataKey="rate"
                  stroke="#3b82f6"
                  strokeWidth={3}
                  dot={{
                    r: 4,
                    strokeWidth: 2,
                  }}
                  activeDot={{
                    r: 6,
                  }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Breakdown of Violations */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-lg font-bold text-slate-900">
                Breakdown of Violations
              </h2>

              <p className="text-sm text-slate-500">
                Most common missing or incorrect fields
              </p>
            </div>

            <div className="bg-amber-50 p-2 rounded-lg text-amber-600">
              <PieChartIcon className="h-5 w-5" />
            </div>
          </div>

          <div className="h-[300px] w-full flex items-center">
            <ResponsiveContainer
              width="100%"
              height="100%"
            >
              <PieChart>
                <Pie
                  data={
                    data.violationsBreakdown
                  }
                  cx="50%"
                  cy="50%"
                  innerRadius={80}
                  outerRadius={110}
                  paddingAngle={5}
                  dataKey="value"
                  nameKey="name"
                >
                  {data.violationsBreakdown.map(
                    (
                      entry: any,
                      index: number
                    ) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={
                          COLORS[
                            index %
                              COLORS.length
                          ]
                        }
                      />
                    )
                  )}
                </Pie>

                <RechartsTooltip
                  contentStyle={{
                    borderRadius: "12px",
                    border:
                      "1px solid #e2e8f0",
                    boxShadow:
                      "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                  }}
                />

                <Legend
                  layout="vertical"
                  verticalAlign="middle"
                  align="right"
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}