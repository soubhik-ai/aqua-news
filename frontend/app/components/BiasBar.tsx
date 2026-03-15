import React from "react";
import { cn } from "@/lib/utils";

interface BiasBarProps {
  scores: number[];
  className?: string;
}

export function BiasBar({ scores, className }: BiasBarProps) {
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
          // Score is -10 to 10. Map to 0% to 100%
          const percentage = ((score + 10) / 20) * 100;
          return (
            <div
              key={i}
              className="absolute w-3 h-3 rounded-full bg-stone-800 border-2 border-white shadow-sm transform -translate-x-1/2 transition-transform hover:scale-150 cursor-pointer"
              style={{ left: `${percentage}%` }}
              title={`Bias Score: ${score}`}
            />
          );
        })}
      </div>

      <div className="flex justify-between text-[10px] uppercase tracking-wider text-stone-500 font-medium">
        <span>Far Left</span>
        <span>Center</span>
        <span>Far Right</span>
      </div>
    </div>
  );
}
