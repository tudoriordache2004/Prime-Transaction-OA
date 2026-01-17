import type { QuoteLatest, Stock, Watchlist } from "./types"

const API_BASE_URL =
  typeof window === "undefined"
    ? process.env.API_INTERNAL_BASE_URL ??
      process.env.NEXT_PUBLIC_API_BASE_URL ??
      "http://localhost:8000"
    : process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, { cache: "no-store" })

  if (!res.ok) {
    const text = await res.text().catch(() => "")
    throw new Error(`API ${path} failed: ${res.status} ${text}`)
  }

  return (await res.json()) as T
}

export const api = {
  refreshSymbol: async (symbol: string) => {
    const res = await fetch(
      `${API_BASE_URL}/watchlist/${encodeURIComponent(symbol)}/refresh`,
      {
        method: "POST",
      }
    )
    if (!res.ok) throw new Error(`refreshSymbol failed: ${res.status}`)
    return res.json()
  },

  watchlist: () => getJson<Watchlist>("/watchlist"),
  watchlistStocks: () => getJson<Stock[]>("/watchlist/stocks"),
  stocks: () => getJson<Stock[]>("/stocks"),
  stock: (symbol: string) =>
    getJson<Stock>(`/stocks/${encodeURIComponent(symbol)}`),

  quotesLatestAll: () => getJson<QuoteLatest[]>("/quotes/latest"),
  quoteLatest: (symbol: string) =>
    getJson<QuoteLatest>(`/quotes/latest/${encodeURIComponent(symbol)}`),
  quoteHistory: (symbol: string, limit = 200) =>
    getJson<{ collected_ts: number; current_price: number | null }[]>(
      `/quotes/history/${encodeURIComponent(symbol)}?limit=${limit}`
    ),

  search: (query: string) =>
    getJson<any>(`/search?query=${encodeURIComponent(query)}`),

  watchlistAdd: async (symbol: string) => {
    const res = await fetch(
      `${API_BASE_URL}/watchlist/${encodeURIComponent(symbol)}`,
      {
        method: "POST",
      }
    )
    if (!res.ok) throw new Error(`watchlistAdd failed: ${res.status}`)
    return res.json()
  },

  watchlistPurge: async (symbol: string) => {
    const res = await fetch(
      `${API_BASE_URL}/watchlist/${encodeURIComponent(symbol)}/purge`,
      { method: "DELETE" }
    )
    if (!res.ok) throw new Error(`watchlistPurge failed: ${res.status}`)
    return res.json()
  },
}
