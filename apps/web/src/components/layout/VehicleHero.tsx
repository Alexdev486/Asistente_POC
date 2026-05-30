"use client";

import { motion, useReducedMotion } from "framer-motion";
import { Bike } from "lucide-react";

type VehicleHeroProps = {
  photoUrl: string;
  modelName: string | null;
};

export function VehicleHero({ photoUrl, modelName }: VehicleHeroProps) {
  const shouldReduceMotion = useReducedMotion();

  const imgSrc = `${process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1"}/${photoUrl.replace("/api/v1/", "")}`;

  return (
    <motion.div
      initial={{ opacity: 0, y: -20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.5, ease: [0.34, 1.56, 0.64, 1] }}
      className="relative overflow-hidden rounded-2xl border border-border-default bg-gradient-to-b from-surface-elevated to-surface-secondary"
    >
      {/* Imagen grande — object-contain para que no se recorte */}
      <div className="relative flex h-64 items-center justify-center bg-gradient-to-b from-surface-elevated to-surface-secondary sm:h-80">
        <img
          src={imgSrc}
          alt={modelName ?? "Motocicleta"}
          className="h-full w-full object-contain p-4"
          onError={(e) => {
            (e.target as HTMLImageElement).style.display = "none";
          }}
        />

        {/* Gradiente inferior para legibilidad del texto */}
        <div className="pointer-events-none absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-surface-secondary to-transparent" />

        {/* Etiqueta del modelo */}
        {modelName && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.3 }}
            className="absolute bottom-4 left-4 flex items-center gap-2 rounded-full border border-border-default bg-surface-secondary/80 px-4 py-1.5 backdrop-blur-md"
          >
            <Bike size={14} className="text-accent-1" />
            <span className="text-sm font-semibold text-text-primary">
              {modelName}
            </span>
          </motion.div>
        )}

        {/* Brillo animado tenue */}
        {!shouldReduceMotion && (
          <motion.div
            className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_60%_40%_at_50%_0%,rgba(59,130,246,0.08),transparent)]"
            animate={{ opacity: [0.4, 0.8, 0.4] }}
            transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
          />
        )}
      </div>
    </motion.div>
  );
}
