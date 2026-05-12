"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sun, Moon } from "lucide-react";

// Shared hook — sync theme to body class + localStorage
// Uses a custom "theme-change" event so all instances stay in sync
export function useTheme() {
  const [theme, set] = useState<"dark" | "light">(() => {
    if (typeof window === "undefined") return "dark";
    return localStorage.getItem("app-theme") === "light" ? "light" : "dark";
  });

  useEffect(() => {
    document.body.classList.toggle("theme-light", theme === "light");
  }, [theme]);

  // Sync when any other useTheme instance changes the theme
  useEffect(() => {
    const sync = () => {
      const saved = localStorage.getItem("app-theme") === "light" ? "light" : "dark";
      set(saved);
    };
    window.addEventListener("theme-change", sync);
    return () => window.removeEventListener("theme-change", sync);
  }, []);

  const apply = (next: "dark" | "light") => {
    set(next);
    localStorage.setItem("app-theme", next);
    document.body.classList.toggle("theme-light", next === "light");
    window.dispatchEvent(new Event("theme-change"));
  };

  return { theme, toggle: () => apply(theme === "dark" ? "light" : "dark"), apply };
}

// Floating theme button — renders on every page via layout
export default function ThemePreferences() {
  const { theme, toggle } = useTheme();

  return (
    <motion.button
      onClick={toggle}
      whileHover={{ scale: 1.10 }}
      whileTap={{ scale: 0.86 }}
      transition={{ type: "spring", stiffness: 380, damping: 26 }}
      aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
      title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
      className="fixed bottom-6 right-6 z-[9999] w-10 h-10 rounded-full flex items-center justify-center"
      style={{
        background: "rgba(10,10,14,0.88)",
        border: "1px solid rgba(255,255,255,0.10)",
        backdropFilter: "blur(20px)",
        boxShadow: "0 4px 20px rgba(0,0,0,0.45), inset 0 1px 0 rgba(255,255,255,0.06)",
      }}
    >
      <AnimatePresence mode="wait" initial={false}>
        {theme === "dark" ? (
          <motion.span key="moon"
            initial={{ opacity: 0, rotate: -40, scale: 0.5 }}
            animate={{ opacity: 1, rotate: 0,   scale: 1   }}
            exit={   { opacity: 0, rotate:  40, scale: 0.5 }}
            transition={{ duration: 0.18, ease: [0.22, 1, 0.36, 1] }}
            style={{ display: "flex" }}
          >
            <Moon size={15} style={{ color: "rgba(255,255,255,0.55)" }} />
          </motion.span>
        ) : (
          <motion.span key="sun"
            initial={{ opacity: 0, rotate:  40, scale: 0.5 }}
            animate={{ opacity: 1, rotate: 0,   scale: 1   }}
            exit={   { opacity: 0, rotate: -40, scale: 0.5 }}
            transition={{ duration: 0.18, ease: [0.22, 1, 0.36, 1] }}
            style={{ display: "flex" }}
          >
            <Sun size={15} style={{ color: "#FBBF24" }} />
          </motion.span>
        )}
      </AnimatePresence>
    </motion.button>
  );
}
