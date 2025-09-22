          onClick={onClose}
          className="mt-0.5 w-8 h-8 rounded-xl flex items-center justify-center text-slate-600 hover:text-white hover:bg-white/8 transition-all border border-transparent hover:border-white/10 active:scale-90"
          aria-label="Close node inspector"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* ── Body ──────────────────────────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto custom-scrollbar px-5 py-5 space-y-6">

        {/* Resources */}
        <section>
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-[9px] font-black text-slate-500 uppercase tracking-[0.25em]">System Resources</h4>
            {anyFiltered && (
              <span className="text-[9px] text-amber-500/80 font-bold flex items-center gap-1.5">
                <span className="w-1 h-1 rounded-full bg-amber-500 animate-pulse" />
                VoI Active
              </span>
            )}
          </div>
          <div className="grid grid-cols-2 gap-2.5">
            <ResourceCard label="CPU"      value={cpu}     unit="%" isFiltered={isCpuFiltered}     icon={mkIcon(icons.cpu)}  />
