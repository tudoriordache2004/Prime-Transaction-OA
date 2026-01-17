"use client"

type Point = {
  current_price: number | null
  collected_ts?: number
  quote_ts?: number
}

export function PriceChart({
  points,
  height = 160,
}: {
  points: Point[]
  height?: number
}) {
  const data = points
    .map((p) => ({
      t: p.collected_ts ?? p.quote_ts ?? 0,
      v: p.current_price,
    }))
    .filter((p) => p.t > 0 && typeof p.v === "number") as {
    t: number
    v: number
  }[]

  if (data.length < 2) {
    return <div className="text-sm text-zinc-600">Not enough data yet.</div>
  }

  data.sort((a, b) => a.t - b.t)

  const width = 600
  const min = Math.min(...data.map((d) => d.v))
  const max = Math.max(...data.map((d) => d.v))
  const span = Math.max(max - min, 1e-9)

  const toX = (i: number) => (i / (data.length - 1)) * (width - 20) + 10
  const toY = (v: number) => (1 - (v - min) / span) * (height - 20) + 10

  const d = data
    .map((p, i) => `${i === 0 ? "M" : "L"} ${toX(i)} ${toY(p.v)}`)
    .join(" ")

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full">
      <path d={d} fill="none" stroke="currentColor" strokeWidth="2" />
    </svg>
  )
}
