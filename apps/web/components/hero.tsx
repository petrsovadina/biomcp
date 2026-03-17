export function Hero() {
  return (
    <section className="relative min-h-screen overflow-hidden bg-[#030303] flex items-center justify-center">
      <div className="absolute inset-0 overflow-hidden">
        <div
          style={{ animation: 'float-slow 12s ease-in-out infinite' }}
          className="absolute left-[-10%] top-[20%] h-[140px] w-[600px] rounded-full bg-gradient-to-r from-blue-500/[0.15] to-transparent border-2 border-white/[0.1] backdrop-blur-sm"
        />
        <div
          style={{ animation: 'float-reverse 15s ease-in-out 1s infinite' }}
          className="absolute right-[-5%] top-[70%] h-[120px] w-[500px] rounded-full bg-gradient-to-r from-emerald-500/[0.12] to-transparent border-2 border-white/[0.08] backdrop-blur-sm"
        />
        <div
          style={{ animation: 'float-medium 10s ease-in-out 2s infinite' }}
          className="absolute right-[20%] top-[10%] h-[60px] w-[200px] rounded-full bg-gradient-to-r from-amber-500/[0.1] to-transparent border-2 border-white/[0.06]"
        />
      </div>

      <div className="absolute inset-0 bg-gradient-to-t from-[#030303] via-transparent to-[#030303]/80" />

      <div className="relative z-10 mx-auto max-w-4xl px-6 text-center">
        <div
          className="hero-animate mb-8 inline-flex items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.03] px-4 py-1.5"
          style={{ animationDelay: '0.2s' }}
        >
          <span className="h-2 w-2 rounded-full bg-emerald-500" />
          <span className="text-sm tracking-wide text-white/60">
            Open source &middot; MIT licence &middot; 60 AI nástrojů
          </span>
        </div>

        <h1
          className="hero-animate text-5xl font-bold tracking-tight sm:text-6xl md:text-7xl lg:text-8xl"
          style={{ animationDelay: '0.35s' }}
        >
          <span className="bg-gradient-to-b from-white to-white/80 bg-clip-text text-transparent">
            AI napojení na
          </span>
          <br />
          <span className="bg-gradient-to-r from-blue-300 via-white/90 to-emerald-300 bg-clip-text text-transparent">
            české zdravotnictví
          </span>
        </h1>

        <p
          className="hero-animate mx-auto mt-8 max-w-xl text-lg leading-relaxed font-light tracking-wide text-white/40 md:text-xl"
          style={{ animationDelay: '0.5s' }}
        >
          CzechMedMCP propojuje Claude, Cursor a další AI asistenty s SUKL,
          MKN-10, PubMed a dalšími zdroji. Jeden server, jeden protokol.
        </p>

        <div
          className="hero-animate mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row"
          style={{ animationDelay: '0.65s' }}
        >
          <a
            href="#zacit"
            className="w-full rounded-xl bg-white px-8 py-4 text-center font-semibold text-[#030303] shadow-lg shadow-white/10 transition hover:bg-white/90 sm:w-auto"
          >
            Začít za 2 minuty
          </a>
          <a
            href="https://github.com/petrsovadina/CzechMedMCP"
            target="_blank"
            rel="noopener"
            className="w-full rounded-xl border border-white/10 px-8 py-4 text-center font-semibold text-white/70 transition hover:border-white/20 hover:text-white sm:w-auto"
          >
            GitHub
          </a>
        </div>

        <div
          className="hero-animate mx-auto mt-20 max-w-2xl"
          style={{ animationDelay: '0.8s' }}
        >
          <div className="overflow-hidden rounded-xl border border-white/[0.08] bg-white/[0.03] shadow-2xl backdrop-blur-sm">
            <div className="flex items-center gap-2 border-b border-white/[0.06] px-4 py-3">
              <div className="h-3 w-3 rounded-full bg-red-500/80" />
              <div className="h-3 w-3 rounded-full bg-yellow-500/80" />
              <div className="h-3 w-3 rounded-full bg-green-500/80" />
              <span className="ml-2 text-xs text-white/30">terminal</span>
            </div>
            <div className="p-6 text-left font-mono text-sm leading-relaxed">
              <p className="text-white/30"># Instalace za 10 sekund</p>
              <p className="text-emerald-400">$ pip install czechmedmcp</p>
              <p className="mt-4 text-white/30"># Spuštění MCP serveru</p>
              <p className="text-emerald-400">$ czechmedmcp run</p>
              <p className="mt-2 text-white/50">
                CzechMedMCP v0.8.0 — 60 nástrojů připraveno
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
