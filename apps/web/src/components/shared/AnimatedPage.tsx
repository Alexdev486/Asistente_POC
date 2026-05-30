"use client";

import { type ReactNode } from "react";
import { motion, useReducedMotion } from "framer-motion";

type AnimatedPageProps = {
  id: string;
  children: ReactNode;
  className?: string;
};

export function AnimatedPage({ id, children, className }: AnimatedPageProps) {
  const shouldReduceMotion = useReducedMotion();

  return (
    <motion.div
      key={id}
      initial={shouldReduceMotion ? { opacity: 1 } : { opacity: 0, y: 16, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={shouldReduceMotion ? { opacity: 1 } : { opacity: 0, y: -16, scale: 0.98 }}
      transition={{
        duration: shouldReduceMotion ? 0 : 0.35,
        ease: [0.22, 1, 0.36, 1] as [number, number, number, number],
      }}
      className={className}
    >
      {children}
    </motion.div>
  );
}
