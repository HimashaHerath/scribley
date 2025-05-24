"use client"

import { createContext, useContext, useEffect, useState } from "react"
import { usePreference } from "@/contexts/UserPreferencesContext"

type Theme = "dark" | "light" | "system"

type ThemeProviderProps = {
  children: React.ReactNode
  defaultTheme?: Theme
  storageKey?: string
}

type ThemeProviderState = {
  theme: Theme
  setTheme: (theme: Theme) => void
}

const initialState: ThemeProviderState = {
  theme: "system",
  setTheme: () => null,
}

const ThemeProviderContext = createContext<ThemeProviderState>(initialState)

export function ThemeProvider({
  children,
  defaultTheme = "system",
  storageKey = "vite-ui-theme",
  ...props
}: ThemeProviderProps) {
  // Use user preferences for theme storage
  const [preferenceTheme, setPreferenceTheme] = usePreference('theme');
  
  // Keep localStorage for backward compatibility
  const [theme, setTheme] = useState<Theme>(
    () => (preferenceTheme as Theme) || (localStorage.getItem(storageKey) as Theme) || defaultTheme
  )

  // Update theme when preferences change
  useEffect(() => {
    if (preferenceTheme !== theme) {
      setTheme(preferenceTheme as Theme);
    }
  }, [preferenceTheme, theme]);

  useEffect(() => {
    const root = window.document.documentElement
    
    root.classList.remove("light", "dark")

    if (theme === "system") {
      const systemTheme = window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light"
      root.classList.add(systemTheme)
      return
    }

    root.classList.add(theme)
  }, [theme])

  const value = {
    theme,
    setTheme: (theme: Theme) => {
      // Update both localStorage and preferences
      localStorage.setItem(storageKey, theme)
      setPreferenceTheme(theme)
      setTheme(theme)
    },
  }

  return (
    <ThemeProviderContext.Provider {...props} value={value}>
      {children}
    </ThemeProviderContext.Provider>
  )
}

export const useTheme = () => {
  const context = useContext(ThemeProviderContext)

  if (context === undefined)
    throw new Error("useTheme must be used within a ThemeProvider")

  return context
} 