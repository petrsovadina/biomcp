import { FadeIn } from '@/components/fade-in'

export function CodeExample() {
  return (
    <section className="bg-[#030303] py-24 md:py-32">
      <div className="mx-auto max-w-6xl px-6">
        <FadeIn className="text-center">
          <h2 className="text-3xl font-bold tracking-tight text-white md:text-4xl">
            Jak to vypadá v praxi
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-white/50">
            Přirozený dialog s AI — CzechMedMCP pracuje na pozadí.
          </p>
        </FadeIn>

        <FadeIn delay={0.2} className="mx-auto mt-16 max-w-3xl">
          <div className="overflow-hidden rounded-2xl border border-white/[0.08] bg-white/[0.03] backdrop-blur-sm">
            <div className="border-b border-white/[0.06] px-6 py-4">
              <span className="text-sm font-medium text-white/60">
                Claude Desktop + CzechMedMCP
              </span>
            </div>
            <div className="space-y-6 p-6">
              <div className="flex justify-end">
                <div className="max-w-md rounded-2xl rounded-br-md bg-blue-600 px-4 py-3 text-sm text-white">
                  Najdi lék Metformin, zkontroluj dostupnost a porovnej
                  alternativy podle doplatku.
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex gap-3">
                  <div className="h-8 w-8 shrink-0 rounded-full bg-gradient-to-br from-violet-500 to-blue-500" />
                  <div className="space-y-2">
                    <div className="inline-block rounded-lg bg-white/[0.05] px-3 py-1 font-mono text-xs text-emerald-400">
                      czechmed_search_medicine(query=&quot;Metformin&quot;)
                    </div>
                    <div className="inline-block rounded-lg bg-white/[0.05] px-3 py-1 font-mono text-xs text-emerald-400">
                      czechmed_check_availability(sukl_code=&quot;0012345&quot;)
                    </div>
                    <div className="inline-block rounded-lg bg-white/[0.05] px-3 py-1 font-mono text-xs text-emerald-400">
                      czechmed_compare_alternatives(atc_code=&quot;A10BA02&quot;)
                    </div>
                    <div className="max-w-lg rounded-2xl rounded-bl-md bg-white/[0.06] px-4 py-3 text-sm leading-relaxed text-white/80">
                      <p className="font-semibold text-white">Metformin — přehled</p>
                      <p className="mt-2">Nalezeno 12 přípravků s metforminem. Přípravek <strong>Metformin Teva 1000 mg</strong> (SUKL: 0012345) je aktuálně <span className="text-emerald-400">dostupný</span>.</p>
                      <p className="mt-2">Doplatek: <strong>0 Kč</strong> (plně hrazeno).</p>
                      <p className="mt-2">V ATC skupině A10BA02 je 8 alternativ — nejnižší doplatek 0 Kč (Metformin Teva), nejvyšší 45 Kč (Glucophage XR).</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </FadeIn>
      </div>
    </section>
  )
}
