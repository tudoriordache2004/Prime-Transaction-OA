import Link from "next/link"
import { api } from "../../../lib/api"
import { PriceChart } from "./PriceChart"

type Props = { params: Promise<{ symbol: string }> }

export default async function StockDetailsPage({ params }: Props) {
  const { symbol } = await params

  const [stock, quote, history] = await Promise.all([
    api.stock(symbol),
    api.quoteLatest(symbol),
    api.quoteHistory(symbol, 200),
  ])

  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-900">
      <main className="mx-auto max-w-3xl px-6 py-10">
        <Link className="text-sm underline" href="/watchlist">
          ← Back
        </Link>

        <h1 className="mt-4 text-2xl font-semibold">
          {stock.symbol}{" "}
          <span className="text-zinc-600 font-normal">{stock.name ?? ""}</span>
        </h1>

        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          <div className="rounded-xl border bg-white p-4">
            <div className="text-xs text-zinc-600">Exchange</div>
            <div className="mt-1">{stock.exchange ?? "-"}</div>
          </div>
          <div className="rounded-xl border bg-white p-4">
            <div className="text-xs text-zinc-600">Currency</div>
            <div className="mt-1">{stock.currency ?? "-"}</div>
          </div>
          <div className="rounded-xl border bg-white p-4">
            <div className="text-xs text-zinc-600">Industry</div>
            <div className="mt-1">{stock.industry ?? "-"}</div>
          </div>
          <div className="rounded-xl border bg-white p-4">
            <div className="text-xs text-zinc-600">Updated</div>
            <div className="mt-1">{stock.updated_at}</div>
          </div>
        </div>

        <div className="mt-6 rounded-xl border bg-white p-4">
          <div className="text-xs text-zinc-600">Latest quote</div>
          <div className="mt-6 rounded-xl border bg-white p-4">
            <div className="text-xs text-zinc-600">Price history</div>
            <div className="mt-2">
              <PriceChart points={history} />
            </div>
          </div>
          <div className="mt-2 grid grid-cols-2 gap-3 text-sm">
            <div>
              Price:{" "}
              <span className="tabular-nums">{quote.current_price ?? "-"}</span>
            </div>
            <div>
              Prev close:{" "}
              <span className="tabular-nums">
                {quote.previous_close ?? "-"}
              </span>
            </div>
            <div>
              High:{" "}
              <span className="tabular-nums">{quote.high_price ?? "-"}</span>
            </div>
            <div>
              Low:{" "}
              <span className="tabular-nums">{quote.low_price ?? "-"}</span>
            </div>
            <div>
              Open:{" "}
              <span className="tabular-nums">{quote.open_price ?? "-"}</span>
            </div>
            <div>
              Updated: <span className="tabular-nums">{quote.updated_at}</span>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
