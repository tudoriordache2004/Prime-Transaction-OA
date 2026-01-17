import Link from "next/link"
import { api } from "../../lib/api"

export default async function QuotesPage() {
  const quotes = await api.quotesLatestAll()

  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-900">
      <main className="mx-auto max-w-5xl px-6 py-10">
        <div className="flex items-baseline justify-between">
          <h1 className="text-2xl font-semibold">Quotes (latest)</h1>
          <div className="flex gap-4 text-sm">
            <Link className="underline" href="/watchlist">
              Watchlist
            </Link>
            <Link className="underline" href="/stocks">
              Stocks
            </Link>
          </div>
        </div>

        <div className="mt-6 overflow-hidden rounded-xl border bg-white">
          <table className="w-full text-sm">
            <thead className="bg-zinc-50 text-left">
              <tr className="[&>th]:px-4 [&>th]:py-3">
                <th>Symbol</th>
                <th className="text-right">Price</th>
                <th className="text-right">Prev close</th>
                <th className="text-right">High</th>
                <th className="text-right">Low</th>
                <th className="text-right">Updated</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {quotes.map((q) => (
                <tr key={q.symbol} className="[&>td]:px-4 [&>td]:py-3">
                  <td className="font-medium">
                    <Link className="underline" href={`/stocks/${q.symbol}`}>
                      {q.symbol}
                    </Link>
                  </td>
                  <td className="text-right tabular-nums">
                    {q.current_price ?? "-"}
                  </td>
                  <td className="text-right tabular-nums">
                    {q.previous_close ?? "-"}
                  </td>
                  <td className="text-right tabular-nums">
                    {q.high_price ?? "-"}
                  </td>
                  <td className="text-right tabular-nums">
                    {q.low_price ?? "-"}
                  </td>
                  <td className="text-right text-zinc-600">{q.updated_at}</td>
                </tr>
              ))}

              {quotes.length === 0 && (
                <tr>
                  <td className="px-4 py-6 text-zinc-600" colSpan={6}>
                    No quotes yet. Add symbols to watchlist and run ingest.
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
