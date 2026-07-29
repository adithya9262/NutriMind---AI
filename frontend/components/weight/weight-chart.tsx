"use client"

import { Card } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from "recharts"
import type { BodyWeightEntryData } from "@/types/body-weight"

interface WeightChartProps {
  entries: BodyWeightEntryData[]
  className?: string
}

export function WeightChart({ entries, className = "" }: WeightChartProps) {
  const chartData = [...entries]
    .sort((a, b) => new Date(a.logged_date).getTime() - new Date(b.logged_date).getTime())
    .map((e) => ({
      date: new Date(e.logged_date).toLocaleDateString(undefined, { month: "short", day: "numeric" }),
      weight: Number(e.weight_kg),
    }))

  if (chartData.length < 2) {
    return (
      <div className={cn("flex flex-col items-center justify-center h-56 sm:h-64 text-sm text-primary-muted bg-surface/30 rounded-xl border border-dashed border-border m-2", className)}>
        <p className="font-medium text-primary mb-1">Not enough data</p>
        <p>Log at least two weight entries to visualize your trend.</p>
      </div>
    )
  }

  return (
    <Card className={cn("p-5", className)}>
      <h3 className="text-sm font-semibold text-primary mb-1">Weight Trend</h3>
      <p className="text-xs text-primary-muted mb-4">Your body weight over time</p>
      <div className="h-56 sm:h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="weightGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--color-brand)" stopOpacity={0.15} />
                <stop offset="95%" stopColor="var(--color-brand)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="var(--color-border)"
              vertical={false}
            />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 11, fill: "var(--color-text-muted)" }}
              axisLine={{ stroke: "var(--color-border)" }}
              tickLine={false}
            />
            <YAxis
              domain={["auto", "auto"]}
              tick={{ fontSize: 11, fill: "var(--color-text-muted)" }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => `${v}`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "var(--color-surface)",
                border: "1px solid var(--color-border)",
                borderRadius: "12px",
                fontSize: "13px",
                boxShadow: "var(--shadow-lg)",
              }}
            />
            <Area
              type="monotone"
              dataKey="weight"
              stroke="var(--color-brand)"
              strokeWidth={2}
              fill="url(#weightGradient)"
              dot={{ fill: "var(--color-brand)", r: 4, strokeWidth: 2, stroke: "var(--color-surface)" }}
              activeDot={{ r: 6, fill: "var(--color-brand)", strokeWidth: 2, stroke: "var(--color-surface)" }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </Card>
  )
}
