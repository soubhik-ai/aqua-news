import React from "react";
import { cn } from "@/lib/utils";

interface BiasBarProps {
  scores: number[];
  leadScore: number;
  className?: string;
}

export function BiasBar({ scores, leadScore, className }: BiasBarProps) {
  return (
    <div className={cn("w-full mt-4 flex flex-col gap-2", className)}>
      <div className="relative w-full h-1 bg-stone-200 rounded-full overflow-hidden">
        {/* Center line */}
        <div className="absolute left-1/2 top-0 bottom-0 w-px bg-stone-400 z-10" />

        {/* Gradient background for left vs right visual context */}
        <div className="absolute inset-0 flex">
          <div className="w-1/2 h-full bg-gradient-to-r from-blue-100 to-transparent opacity-50" />
          <div className="w-1/2 h-full bg-gradient-to-l from-red-100 to-transparent opacity-50" />
        </div>
      </div>

      <div className="relative w-full h-6 flex items-center">
        {scores.map((score, i) => {
          const percentage = ((score + 10) / 20) * 100;
          const isLead = score === leadScore;
          return (
            <div
              key={i}
              className={cn(
                "absolute transform -translate-x-1/2 transition-transform hover:scale-150 cursor-pointer",
                isLead
                  ? "w-4 h-4 rounded-full bg-stone-900 border-2 border-stone-400 shadow-md z-20 ring-2 ring-stone-300"
                  : "w-3 h-3 rounded-full bg-stone-400 border-2 border-white shadow-sm"
              )}
              style={{ left: `${percentage}%` }}
              title={isLead ? `Lead article bias: ${score}` : `Source bias: ${score}`}
            />
          );
        })}
      </div>

      <div className="flex justify-between text-[10px] uppercase tracking-wider text-stone-500 font-medium">
        <span>Far Left</span>
        <span className="flex items-center gap-1">
          <span className="inline-block w-2 h-2 rounded-full bg-stone-900 border border-stone-400"></span>
          <span>= Lead</span>
        </span>
        <span>Far Right</span>
      </div>
    </div>
  );
}
