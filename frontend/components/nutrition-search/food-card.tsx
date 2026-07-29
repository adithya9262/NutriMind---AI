"use client"

import { motion } from "framer-motion"
import { Card } from "@/components/ui/card"
import { FavoriteButton } from "@/components/nutrition-search/favorite-button"
import type { DemoFood } from "@/components/nutrition-search/placeholders"
import { cn } from "@/lib/utils"

interface FoodCardProps {
  food: DemoFood
  favorite: boolean
  onToggleFavorite: (food: DemoFood) => void
  onSelect: (food: DemoFood) => void
}

const macroChips = [
  { key: "protein_g", label: "Prot", tone: "text-brand" },
  { key: "fat_g", label: "Fat", tone: "text-warning" },
  { key: "calories", label: "Cal", tone: "text-primary" },
] as const

export function FoodCard({
  food,
  favorite,
  onToggleFavorite,
  onSelect,
}: FoodCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card
        variant="glass"
        className="p-3 cursor-pointer group hover:border-brand transition-all duration-500 hover:-translate-y-1"
        onClick={() => onSelect(food)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault()
            onSelect(food)
          }
        }}
        aria-label={`View details for ${food.name}`}
      >
        <div className="relative w-full aspect-[4/3] rounded-2xl overflow-hidden mb-3 bg-surface-high">
          <div className="absolute inset-0 grid place-items-center text-primary-muted/30">
            <span className="text-4xl font-bold">{food.name.charAt(0)}</span>
          </div>
          <div className="absolute top-3 right-3">
            <FavoriteButton
              active={favorite}
              onToggle={() => onToggleFavorite(food)}
              label={favorite ? `Remove ${food.name} from favorites` : `Add ${food.name} to favorites`}
            />
          </div>
        </div>
        <div className="px-1">
          <div className="flex justify-between items-center gap-2 mb-1">
            <h3 className="font-semibold text-primary text-lg leading-tight truncate">
              {food.name}
            </h3>
            {food.topPick && (
              <span className="text-[10px] bg-brand-light text-brand px-2 py-0.5 rounded-full font-bold shrink-0">
                TOP PICK
              </span>
            )}
          </div>
          <p className="text-[11px] text-primary-muted/60 mb-3 uppercase tracking-wider truncate">
            {food.serving}
          </p>
          <div className="grid grid-cols-3 gap-2">
            {macroChips.map((chip) => (
              <div
                key={chip.key}
                className="bg-surface-highest/50 p-2 rounded-xl border border-white/5 text-center"
              >
                <p className="text-[9px] uppercase opacity-40 font-bold">{chip.label}</p>
                <p className={cn("font-semibold", chip.tone)}>
                  {food[chip.key]}
                  {chip.key !== "calories" ? "g" : ""}
                </p>
              </div>
            ))}
          </div>
        </div>
      </Card>
    </motion.div>
  )
}
