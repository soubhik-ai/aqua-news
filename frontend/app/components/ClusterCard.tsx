"use client";
import React, { useState } from "react";
import { BiasBar } from "./BiasBar";
import { ShareButtons } from "./ShareButtons";
import { ChevronDown, ChevronUp } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export interface Article {
  url: string;
  title: string;
  domain: string;
  bias_score: number;
}

export interface ClusterProps {
  data: {
    cluster_label: number;
    lead_article: Article;
    summary: string;
    bias_metrics: {
      mean: number;
      std: number;
      min_score: number;
      max_score: number;
      scores: number[];
    };
    article_count: number;
    sources: string[];
    all_articles: Article[];
    regions: string[];
    categories: string[];
  };
}

export function ClusterCard({ data }: ClusterProps) {
  const [expanded, setExpanded] = useState(false);
  const lead = data.lead_article;
  const metrics = data.bias_metrics;

  return (
    <article className="bg-white border border-stone-200 p-6 md:p-8 rounded-sm shadow-sm hover:shadow-md transition-shadow duration-300">
      {/* Meta tags */}
      <div className="flex flex-wrap gap-2 mb-4">
        {data.categories.map((c) => (
          <span
            key={c}
            className="px-2 py-0.5 bg-stone-900 text-stone-50 text-[10px] uppercase tracking-widest font-bold"
          >
            {c}
          </span>
        ))}
        {data.regions.map((r) => (
          <span
            key={r}
            className="px-2 py-0.5 bg-stone-100 text-stone-500 text-[10px] uppercase tracking-widest font-bold"
          >
            {r}
          </span>
        ))}
      </div>

      {/* Main headline */}
      <h2 className="text-2xl md:text-3xl font-serif font-bold leading-tight mb-2 text-stone-900 heading-balance">
        <a
          href={lead.url}
          target="_blank"
          rel="noopener noreferrer"
          className="hover:underline decoration-2 underline-offset-4"
        >
          {lead.title}
        </a>
      </h2>

      {/* Source & count metadata */}
      <div className="flex items-center gap-3 text-xs font-mono text-stone-500 mb-6">
        <span className="font-semibold text-stone-700">{lead.domain}</span>
        <span className="w-1 h-1 rounded-full bg-stone-300" />
        <span>
          Bias: {lead.bias_score > 0 ? `+${lead.bias_score}` : lead.bias_score}
        </span>
        <span className="w-1 h-1 rounded-full bg-stone-300" />
        <span>{data.article_count} sources covering this</span>
      </div>

      {/* Summary */}
      <div className="prose prose-stone prose-p:leading-relaxed prose-p:text-stone-700 max-w-none mb-6 text-[15px] md:text-base">
        <p>{data.summary}</p>
      </div>

      {/* Bias Visualization */}
      <div className="bg-stone-50 p-4 md:p-5 rounded border border-stone-100 mb-2">
        <div className="flex justify-between items-end mb-2">
          <h3 className="text-xs uppercase tracking-widest font-bold text-stone-400">
            Bias Spectrum Analysis
          </h3>
          <div className="flex gap-4 text-[10px] font-mono text-stone-500">
            <span>
              Mean: {metrics.mean > 0 ? `+${metrics.mean}` : metrics.mean}
            </span>
            <span>
              Range: [{metrics.min_score},{" "}
              {metrics.max_score > 0
                ? `+${metrics.max_score}`
                : metrics.max_score}
              ]
            </span>
          </div>
        </div>
        <BiasBar scores={metrics.scores} />
      </div>

      {/* Expandable Sources List */}
      <div className="mt-4">
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-stone-500 hover:text-stone-900 transition-colors py-2"
        >
          {expanded ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}
          View all {data.article_count} sources
        </button>

        <AnimatePresence>
          {expanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="overflow-hidden"
            >
              <ul className="mt-3 space-y-2 border-l-2 border-stone-100 pl-4 py-2">
                {data.all_articles.map((article, idx) => (
                  <li
                    key={idx}
                    className="flex justify-between items-start gap-4 text-sm group"
                  >
                    <a
                      href={article.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-stone-600 group-hover:text-stone-900 group-hover:underline decoration-stone-300 underline-offset-2 line-clamp-1"
                    >
                      <span className="font-semibold">{article.domain}:</span>{" "}
                      {article.title}
                    </a>
                    <span className="text-[10px] font-mono text-stone-400 bg-stone-50 px-1.5 py-0.5 rounded whitespace-nowrap">
                      {article.bias_score > 0
                        ? `+${article.bias_score}`
                        : article.bias_score}
                    </span>
                  </li>
                ))}
              </ul>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Share Actions */}
      <ShareButtons title={lead.title} url={lead.url} />
    </article>
  );
}
