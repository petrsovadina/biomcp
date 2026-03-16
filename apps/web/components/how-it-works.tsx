import { FadeIn } from '@/components/fade-in'

const steps = [
  {
    num: '01',
    title: 'Instalace',
    desc: 'Jeden příkaz a MCP server je připraven.',
    code: 'pip install czechmedmcp',
  },
  {
    num: '02',
    title: 'Propojení',
    desc: 'Přidejte server do Claude Desktop, Cursor nebo jiného klienta.',
    code: '{ "mcpServers": { "czechmed": { "command": "czechmedmcp", "args": ["run"] } } }',
  },
  {
    num: '03',
    title: 'Používání',
    desc: 'Ptejte se přirozeně v češtině — AI využije správné nástroje automaticky.',
    code: '"Najdi lék Metformin a porovnej alternativy podle doplatku"',
  },
]

export function HowItWorks() {
  return (
    <section id="jak-to-funguje" className="bg-[#030303] py-24 md:py-32">
      <div className="mx-auto max-w-4xl px-6">
        <FadeIn className="text-center">
          <h2 className="text-3xl font-bold tracking-tight text-white md:text-4xl">
            3 kroky k nasazení
          </h2>
        </FadeIn>

        <div className="mt-16 space-y-12">
          {steps.map((s, i) => (
            <FadeIn key={s.num} delay={i * 0.15} className="flex gap-6">
              <div className="flex flex-col items-center">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-blue-500/20 text-sm font-bold text-blue-400">
                  {s.num}
                </div>
                {i < steps.length - 1 && (
                  <div className="mt-2 h-full w-px bg-white/[0.08]" />
                )}
              </div>
              <div className="pb-8">
                <h3 className="text-xl font-semibold text-white">{s.title}</h3>
                <p className="mt-2 text-white/50">{s.desc}</p>
                <div className="mt-4 overflow-x-auto rounded-lg bg-white/[0.04] px-4 py-3 font-mono text-sm text-emerald-400">
                  {s.code}
                </div>
              </div>
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  )
}
