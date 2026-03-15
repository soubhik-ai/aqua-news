"use client";
import React, { useState, useMemo } from "react";
import { ClusterCard } from "./ClusterCard";
import { Globe, Search, ChevronLeft, ChevronRight } from "lucide-react";

const CATEGORY_LABELS: Record<string, string> = {
  general: "Top Stories",
  geopolitics: "World & Politics",
  finance: "Business & Finance",
  technology: "Technology",
  science: "Science",
  culture: "Culture & Entertainment",
};
const CATEGORY_ORDER = ["all", "general", "geopolitics", "finance", "technology", "science", "culture"];
const ITEMS_PER_PAGE = 6;

function primaryCategory(cluster: any): string {
  const cats: string[] = cluster.categories || [];
  for (const c of CATEGORY_ORDER) {
    if (c !== "all" && cats.includes(c)) return c;
  }
  return "general";
}

interface Props {
  data: {
    clusters: any[];
    cluster_count: number;
    fetched_at: string;
  };
}

export function ClientHome({ data }: Props) {
  const clusters = data.clusters || [];
  const [activeTab, setActiveTab] = useState("all");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  // Reset page when filters change
  const setTabAndReset = (tab: string) => { setActiveTab(tab); setPage(1); };
  const setSearchAndReset = (q: string) => { setSearch(q); setPage(1); };

  // Compute available categories
  const availableCategories = useMemo(() => {
    const cats = new Set<string>();
    clusters.forEach((c: any) => (c.categories || []).forEach((cat: string) => cats.add(cat)));
    return CATEGORY_ORDER.filter((c) => c === "all" || cats.has(c));
  }, [clusters]);

  // Filter clusters
  const filtered = useMemo(() => {
    let result = clusters;

    if (activeTab !== "all") {
      result = result.filter((c: any) => primaryCategory(c) === activeTab);
    }

    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter((c: any) => {
        const lead = c.lead_article || {};
        if ((lead.title || "").toLowerCase().includes(q)) return true;
        if ((c.summary || "").toLowerCase().includes(q)) return true;
        if ((lead.domain || "").toLowerCase().includes(q)) return true;
        return (c.all_articles || []).some((a: any) => (a.title || "").toLowerCase().includes(q));
      });
    }

    return result;
  }, [clusters, activeTab, search]);

  // Pagination
  const totalPages = Math.max(1, Math.ceil(filtered.length / ITEMS_PER_PAGE));
  const safePage = Math.min(page, totalPages);
  const pageItems = filtered.slice((safePage - 1) * ITEMS_PER_PAGE, safePage * ITEMS_PER_PAGE);
  const totalSources = filtered.reduce((sum: number, c: any) => sum + (c.article_count || 0), 0);

  return (
    <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 md:py-20">
      {/* Header */}
      <header className="mb-10 border-b-4 border-stone-900 pb-8">
        <div className="flex justify-between items-end">
          <div>
            <h1 className="text-4xl md:text-5xl font-serif font-bold text-stone-900 tracking-tight">
              AQUA NEWS
            </h1>
            <p className="mt-4 text-stone-500 font-mono text-xs uppercase tracking-[0.2em] max-w-lg">
              Multi-source clustering &bull; Bias spectrum analysis &bull; AI-free editorial
            </p>
          </div>
          <div className="text-right hidden sm:block">
            <p className="font-mono text-[10px] text-stone-400 uppercase tracking-widest mb-1">
              Last Updated
            </p>
            <p className="font-mono text-xs text-stone-600 font-semibold">
              {new Date(data.fetched_at).toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
                year: "numeric",
                hour: "2-digit",
                minute: "2-digit",
              })}
            </p>
          </div>
        </div>
      </header>

      {/* Search */}
      <div className="relative mb-6">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-stone-400" />
        <input
          type="text"
          placeholder="Search by keyword, topic, or source..."
          value={search}
          onChange={(e) => setSearchAndReset(e.target.value)}
          className="w-full pl-10 pr-4 py-2.5 border border-stone-200 rounded-sm bg-white text-sm font-sans text-stone-900 placeholder:text-stone-400 focus:outline-none focus:border-stone-900 focus:ring-1 focus:ring-stone-900 transition-colors"
        />
      </div>

      {/* Category tabs */}
      <div className="flex gap-0 border-b border-stone-200 mb-6 overflow-x-auto scrollbar-hide">
        {availableCategories.map((cat) => {
          const count =
            cat === "all"
              ? clusters.length
              : clusters.filter((c: any) => primaryCategory(c) === cat).length;
          return (
            <button
              key={cat}
              onClick={() => setTabAndReset(cat)}
              className={`whitespace-nowrap px-4 py-2.5 text-xs font-mono uppercase tracking-wider border-b-2 transition-colors ${
                activeTab === cat
                  ? "border-stone-900 text-stone-900 font-bold"
                  : "border-transparent text-stone-400 hover:text-stone-600"
              }`}
            >
              {cat === "all" ? "All" : CATEGORY_LABELS[cat] || cat}
              <span className="ml-1.5 text-[10px]">({count})</span>
            </button>
          );
        })}
      </div>

      {/* Stats bar */}
      <div className="flex flex-wrap gap-8 py-3 mb-8 border-b border-stone-100 font-mono text-[11px] uppercase tracking-wider text-stone-500">
        <div className="flex items-center gap-2">
          <Globe className="w-4 h-4 text-stone-900" />
          <span className="text-stone-900 font-bold">{filtered.length}</span> Stories
        </div>
        <div>
          <span className="text-stone-900 font-bold">{totalSources}</span> Sources
        </div>
      </div>

      {/* Cards */}
      <div className="flex flex-col gap-12 md:gap-16">
        {pageItems.length === 0 ? (
          <div className="text-center py-20 text-stone-400 font-mono text-sm">
            {clusters.length === 0
              ? "Waiting for daily ingest pipeline..."
              : "No stories match your search."}
          </div>
        ) : (
          pageItems.map((cluster: any, idx: number) => (
            <ClusterCard key={`${activeTab}-${safePage}-${idx}`} data={cluster} />
          ))
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-4 mt-12 pt-6 border-t border-stone-200">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={safePage <= 1}
            className="flex items-center gap-1 px-3 py-1.5 text-xs font-mono uppercase tracking-wider border border-stone-200 rounded-sm text-stone-600 hover:bg-stone-900 hover:text-white hover:border-stone-900 disabled:opacity-30 disabled:hover:bg-white disabled:hover:text-stone-600 disabled:hover:border-stone-200 transition-all"
          >
            <ChevronLeft className="w-3 h-3" /> Prev
          </button>
          <span className="font-mono text-xs text-stone-500">
            {safePage} / {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={safePage >= totalPages}
            className="flex items-center gap-1 px-3 py-1.5 text-xs font-mono uppercase tracking-wider border border-stone-200 rounded-sm text-stone-600 hover:bg-stone-900 hover:text-white hover:border-stone-900 disabled:opacity-30 disabled:hover:bg-white disabled:hover:text-stone-600 disabled:hover:border-stone-200 transition-all"
          >
            Next <ChevronRight className="w-3 h-3" />
          </button>
        </div>
      )}

      {/* Footer */}
      <footer className="mt-20 pt-8 border-t border-stone-200 text-center text-stone-400 font-mono text-[10px] uppercase tracking-widest pb-12">
        AQUA NEWS &bull; Unbiased, automated clustering
      </footer>
    </main>
  );
}
