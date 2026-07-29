import type { Metadata } from "next"
import { GeistSans } from "geist/font/sans"
import { AuthProvider } from "@/contexts/auth-context"
import { ErrorBoundary } from "@/components/error-boundary"
import { ThemeProvider } from "@/components/theme-provider"
import "./globals.css"

export const metadata: Metadata = {
  title: "NutriMind AI — Precision Biology",
  description: "Track your nutrition, monitor your body weight, and manage your daily health tasks with AI-powered insights.",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className={GeistSans.className} suppressHydrationWarning>
      <head>
        {/*
          Blocking inline script — runs synchronously before the browser paints
          a single pixel. Reads the user's saved theme and font-size from
          localStorage and sets data-theme / data-font-size on <html> so there
          is zero flash of the wrong theme, even on a hard reload or first visit
          after login.
        */}
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{
  var t=localStorage.getItem('"app_theme"')||localStorage.getItem('app_theme');
  var theme=(t&&(t=t.replace(/"/g,'')))?t:'dark';
  if(theme==='system'){
    theme=window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';
  }
  document.documentElement.setAttribute('data-theme',theme);
  var fs=localStorage.getItem('"app_font_size"')||localStorage.getItem('app_font_size');
  if(fs){fs=fs.replace(/"/g,'');if(fs!=='medium')document.documentElement.setAttribute('data-font-size',fs);}
}catch(e){}})();`,
          }}
        />
      </head>
      <body className="font-sans antialiased">
        <ThemeProvider
          attribute="data-theme"
          defaultTheme="dark"
          enableSystem
          disableTransitionOnChange
        >
          <ErrorBoundary>
            <AuthProvider>
              <main className="min-h-screen">{children}</main>
            </AuthProvider>
          </ErrorBoundary>
        </ThemeProvider>
      </body>
    </html>
  )
}
