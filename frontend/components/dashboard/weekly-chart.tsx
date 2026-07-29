"use client"

import { Card } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts"

interface WeeklyChartProps {
  title: string
  description?: string
  data: { label: string; value: number; fill?: string }[]
  color?: string
  className?: string
}

const defaultData = [
  { label: "Mon", value: 1850 },
  { label: "Tue", value: 2100 },
  { label: "Wed", value: 1950 },
  { label: "Thu", value: 2200 },
  { label: "Fri", value: 1780 },
  { label: "Sat", value: 2050 },
  { label: "Sun", value: 1920 },
]

export function WeeklyChart({
  title,
  description,
  data = defaultData,
  color = "var(--color-brand)",
  className = "",
}: WeeklyChartProps) {
  const chartData = data.map((d) => ({
    ...d,
    fill: d.fill || color,
  }))

  return (
    <Card className={cn("p-5 card-hover", className)}>
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-primary">{title}</h3>
        {description && (
          <p className="text-xs text-primary-muted mt-0.5">{description}</p>
        )}
      </div>
      <div className="h-48 sm:h-56">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} barCategoryGap="20%" margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="var(--color-border)"
              vertical={false}
            />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 12, fill: "var(--color-text-muted)" }}
              axisLine={{ stroke: "var(--color-border)" }}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 12, fill: "var(--color-text-muted)" }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "var(--color-surface)",
                border: "1px solid var(--color-border)",
                borderRadius: "12px",
                fontSize: "13px",
                boxShadow: "var(--shadow-lg)",
              }}
              cursor={{ fill: "var(--color-brand-muted)" }}
            />
            <Bar
              dataKey="value"
              radius={[6, 6, 0, 0]}
              maxBarSize={40}
              fill={color}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  )
}
