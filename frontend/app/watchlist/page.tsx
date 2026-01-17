import Link from "next/link"
import { api } from "../../lib/api"
import type { QuoteLatest } from "../../lib/types"
// import { WatchlistSearch } from "./WatchlistSearch"
import { WatchlistSearchWrapper } from "./WatchlistSearchWrapper"
import { WatchlistRemoveButton } from "./WatchlistRemoveButton"

export default async function WatchlistPage() {
  const [watchlist, stocks, quotes] = await Promise.all([
    api.watchlist(),
    api.watchlistStocks(),
    api.quotesLatestAll(),
  ])

  const quoteBySymbol = new Map<string, QuoteLatest>(
    quotes.map((q) => [q.symbol, q])
  )

  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-900">
      <main className="mx-auto max-w-5xl px-6 py-10">
        <div className="flex items-baseline justify-between">
          <h1 className="text-2xl font-semibold">Watchlist</h1>
          <Link className="text-sm underline" href="/stocks">
            All stocks
          </Link>
        </div>

        <div className="mt-6">
          <WatchlistSearchWrapper existingSymbols={watchlist.symbols} />
        </div>

        <div className="mt-6 overflow-hidden rounded-xl border bg-white">
          <table className="w-full text-sm">
            <thead className="bg-zinc-50 text-left">
              <tr className="[&>th]:px-4 [&>th]:py-3">
                <th>Symbol</th>
                <th>Name</th>
                <th className="text-right">Price</th>
                <th className="text-right">High</th>
                <th className="text-right">Low</th>
                <th className="text-right">Updated</th>
                <th className="text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {stocks.map((s) => {
                const q = quoteBySymbol.get(s.symbol)
                return (
                  <tr key={s.symbol} className="[&>td]:px-4 [&>td]:py-3">
                    <td className="font-medium">
                      <Link className="underline" href={`/stocks/${s.symbol}`}>
                        {s.symbol}
                      </Link>
                    </td>
                    <td className="text-zinc-700">{s.name ?? "-"}</td>
                    <td className="text-right tabular-nums">
                      {q?.current_price ?? "-"}
                    </td>
                    <td className="text-right tabular-nums">
                      {q?.high_price ?? "-"}
                    </td>
                    <td className="text-right tabular-nums">
                      {q?.low_price ?? "-"}
                    </td>
                    <td className="text-right text-zinc-600">
                      {q?.updated_at ?? s.updated_at}
                    </td>
                    <td className="text-right">
                      <WatchlistRemoveButton symbol={s.symbol} />
                    </td>
                  </tr>
                )
              })}

              {stocks.length === 0 && (
                <tr>
                  <td className="px-4 py-6 text-zinc-600" colSpan={6}>
                    Watchlist is empty. Use search above to add symbols.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  )
}
