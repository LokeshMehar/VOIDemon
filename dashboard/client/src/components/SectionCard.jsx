import React from "react";

/** Convert an INI section key like 'node_range' into a readable label. */
function sectionLabel(key) {
  return key.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
}

const SECTION_META = {
  PriomonParam:   {
    gradient: "from-indigo-500/15 to-violet-500/10",
    border:   "border-indigo-500/25",
    dot:      "bg-indigo-400",
    text:     "text-indigo-400",
    ring:     "focus:ring-indigo-500/30 focus:border-indigo-500/40",
    icon: "M13 10V3L4 14h7v7l9-11h-7z",
  },
  system_setting: {
    gradient: "from-cyan-500/15 to-sky-500/10",
    border:   "border-cyan-500/25",
    dot:      "bg-cyan-400",
    text:     "text-cyan-400",
    ring:     "focus:ring-cyan-500/30 focus:border-cyan-500/40",
    icon: "M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z",
  },
  database: {
    gradient: "from-amber-500/15 to-orange-500/10",
    border:   "border-amber-500/25",
    dot:      "bg-amber-400",
    text:     "text-amber-400",
    ring:     "focus:ring-amber-500/30 focus:border-amber-500/40",
    icon: "M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4",
  },
};

const DEFAULT_META = {
  gradient: "from-slate-500/15 to-slate-700/10",
  border:   "border-slate-500/25",
  dot:      "bg-slate-400",
