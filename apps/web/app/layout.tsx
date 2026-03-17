import type { Metadata } from 'next'
import { Geist, Geist_Mono } from 'next/font/google'
import { ThemeProvider } from '@/components/theme-provider'
import './globals.css'

const geistSans = Geist({ variable: '--font-sans', subsets: ['latin'] })
const geistMono = Geist_Mono({ variable: '--font-mono', subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'CzechMedMCP — AI napojení na české zdravotnictví',
  description:
    'Open source MCP server propojující Claude, Cursor a další AI asistenty s SUKL, MKN-10, PubMed a dalšími zdroji. 60 nástrojů, jeden protokol.',
  keywords: [
    'MCP', 'AI', 'zdravotnictví', 'SUKL', 'MKN-10', 'PubMed',
    'Claude', 'Cursor', 'české zdravotnictví', 'biomedicína',
  ],
  openGraph: {
    title: 'CzechMedMCP — AI napojení na české zdravotnictví',
    description: '60 AI nástrojů pro biomedicínský výzkum a české zdravotnictví. SUKL, MKN-10, PubMed a další.',
    siteName: 'CzechMedMCP',
    type: 'website',
    locale: 'cs_CZ',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'CzechMedMCP — AI napojení na české zdravotnictví',
    description: '60 AI nástrojů pro biomedicínský výzkum a české zdravotnictví.',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="cs" suppressHydrationWarning>
      <body className={`${geistSans.variable} ${geistMono.variable} font-sans antialiased bg-white text-gray-900 dark:bg-[#030303] dark:text-white`}>
        <ThemeProvider>
          {children}
        </ThemeProvider>
      </body>
    </html>
  )
}
