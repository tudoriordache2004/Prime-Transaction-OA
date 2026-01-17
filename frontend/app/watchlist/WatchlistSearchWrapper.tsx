"use client"

import { useRouter } from "next/navigation"
import { WatchlistSearch } from "./WatchlistSearch"

export function WatchlistSearchWrapper({
  existingSymbols,
}: {
  existingSymbols: string[]
}) {
  const router = useRouter()
  return (
    <WatchlistSearch
      existingSymbols={existingSymbols}
      onChanged={() => router.refresh()}
    />
  )
}
