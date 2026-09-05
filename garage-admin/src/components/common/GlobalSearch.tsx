import { useState } from "react"
import { Link } from "@tanstack/react-router"
import { Search } from "lucide-react"
import { Input } from "@/components/ui/input"
import { useGlobalSearch } from "@/lib/queries/search"

export function GlobalSearch() {
  const [query, setQuery] = useState("")
  const { data, isFetching } = useGlobalSearch(query, query.length >= 2)

  return (
    <div className="relative" data-testid="global-search">
      <Search className="absolute left-2.5 top-2.5 size-4 text-muted-foreground" />
      <Input
        placeholder="Search vehicles, customers, orders..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        className="pl-8"
        data-testid="global-search-input"
      />
      {query.length >= 2 && data && data.length > 0 && (
        <div className="absolute top-full mt-1 w-full rounded-md border bg-popover shadow z-50 max-h-80 overflow-auto">
          {isFetching && <div className="p-2 text-sm text-muted-foreground">Searching...</div>}
          {data.map((r) => (
            <Link
              key={`${r.doctype}-${r.name}`}
              to={r.route}
              className="flex items-center gap-2 p-2 hover:bg-[var(--app-select-row-hover-bg)] text-sm"
              onClick={() => setQuery("")}
            >
              <span className="text-xs bg-muted px-1.5 py-0.5 rounded">{r.type}</span>
              <span className="font-medium truncate">{r.label}</span>
              <span className="text-muted-foreground truncate text-xs">{r.description}</span>
            </Link>
          ))}
        </div>
      )}
      {query.length >= 2 && data && data.length === 0 && !isFetching && (
        <div className="absolute top-full mt-1 w-full rounded-md border bg-popover p-2 text-sm text-muted-foreground shadow">
          No results
        </div>
      )}
    </div>
  )
}
