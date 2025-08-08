import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Basketball Stats',
  description: 'Basketball video analysis and statistics platform',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}