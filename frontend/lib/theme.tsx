"use client";
import { createContext, useCallback, useContext, useEffect, useState } from "react";

type Theme = "dark" | "light";
const KEY = "retainiq_theme";
const Ctx = createContext<{ theme: Theme; toggle: () => void }>({ theme: "dark", toggle: () => {} });

export function useTheme() {
  return useContext(Ctx);
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>("dark");

  useEffect(() => {
    try {
      const saved = localStorage.getItem(KEY) as Theme | null;
      const initial: Theme = saved === "light" || saved === "dark" ? saved : "dark";
      setTheme(initial);
      document.documentElement.classList.toggle("dark", initial === "dark");
      document.documentElement.classList.toggle("light", initial === "light");
      document.body.classList.toggle("light", initial === "light");
    } catch {
      /* private mode — keep dark default */
    }
  }, []);

  const toggle = useCallback(() => {
    setTheme((prev) => {
      const next: Theme = prev === "dark" ? "light" : "dark";
      try {
        localStorage.setItem(KEY, next);
      } catch {
        /* ignore */
      }
      document.documentElement.classList.toggle("dark", next === "dark");
      document.documentElement.classList.toggle("light", next === "light");
      document.body.classList.toggle("light", next === "light");
      return next;
    });
  }, []);

  return <Ctx.Provider value={{ theme, toggle }}>{children}</Ctx.Provider>;
}

/** Inline in <head> to avoid theme flash before hydration. */
export function ThemeScript() {
  const code = `(function(){try{var t=localStorage.getItem('${KEY}');if(t!=='light'&&t!=='dark')t='dark';document.documentElement.classList.toggle('dark',t==='dark');document.documentElement.classList.toggle('light',t==='light');}catch(e){document.documentElement.classList.add('dark')}})();`;
  return <script dangerouslySetInnerHTML={{ __html: code }} />;
}
