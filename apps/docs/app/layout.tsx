import { Footer, Layout, Navbar } from 'nextra-theme-docs'
import { Head } from 'nextra/components'
import { getPageMap } from 'nextra/page-map'
import 'nextra-theme-docs/style.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: {
    default: 'CzechMedMCP — Český zdravotnický MCP server',
    template: '%s | CzechMedMCP',
  },
  description:
    'Open source MCP server propojující AI asistenty s 60 biomedicínskými a zdravotnickými nástroji — SUKL, MKN-10, NRPZS, PubMed, ClinicalTrials.gov a dalšími.',
  keywords: [
    'CzechMedMCP',
    'MCP server',
    'české zdravotnictví',
    'SUKL',
    'MKN-10',
    'AI zdravotnictví',
    'PubMed',
    'biomedicína',
  ],
  openGraph: {
    title: 'CzechMedMCP — Český zdravotnický MCP server',
    description:
      '60 AI nástrojů pro biomedicínský výzkum a české zdravotnictví',
    siteName: 'CzechMedMCP',
    type: 'website',
  },
}

const navbar = (
  <Navbar
    logo={
      <span style={{ fontWeight: 800, fontSize: '1.1rem' }}>
        🏥 CzechMedMCP
      </span>
    }
    projectLink="https://github.com/petrsovadina/biomcp"
  />
)

const footer = (
  <Footer>
    <span>
      MIT {new Date().getFullYear()} ©{' '}
      <a href="https://github.com/petrsovadina" target="_blank">
        Petr Sovadina
      </a>
      . Postaveno na{' '}
      <a href="https://modelcontextprotocol.io" target="_blank">
        Model Context Protocol
      </a>
      .
    </span>
  </Footer>
)

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="cs" dir="ltr" suppressHydrationWarning>
      <Head />
      <body>
        <Layout
          navbar={navbar}
          pageMap={await getPageMap()}
          docsRepositoryBase="https://github.com/petrsovadina/biomcp/tree/main/apps/docs"
          footer={footer}
          sidebar={{ defaultMenuCollapseLevel: 1 }}
          editLink="Upravit stránku"
          feedback={{ content: 'Máte otázku? Dejte nám vědět →' }}
          toc={{ title: 'Na této stránce' }}
        >
          {children}
        </Layout>
      </body>
    </html>
  )
}
