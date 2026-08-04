"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface ReleasePoint {
  time_hours: number;
  fraction_released: number;
}

export function ReleaseChart({ profile }: { profile: ReleasePoint[] }) {
  if (!profile.length) return null;

  return (
    <div className="mt-4">
      <h4 className="mb-2 text-sm font-medium">Release profile</h4>
      <div className="h-48 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={profile}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis
              dataKey="time_hours"
              stroke="var(--muted)"
              tick={{ fontSize: 11 }}
              label={{ value: "Time (hrs)", position: "insideBottom", offset: -2, fontSize: 11 }}
            />
            <YAxis
              stroke="var(--muted)"
              tick={{ fontSize: 11 }}
              domain={[0, 1]}
              tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
            />
            <Tooltip
              contentStyle={{
                background: "var(--surface-elevated)",
                border: "1px solid var(--border)",
                borderRadius: 8,
                fontSize: 12,
              }}
              formatter={(v: number) => [`${(v * 100).toFixed(1)}%`, "Released"]}
              labelFormatter={(t) => `${t} hrs`}
            />
            <Line
              type="monotone"
              dataKey="fraction_released"
              stroke="var(--primary)"
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
