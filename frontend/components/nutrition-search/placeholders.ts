export const NUTRITION_SEARCH_DEMO_LABEL = "Demo dataset"

export interface DemoFood {
  id: string
  name: string
  serving: string
  source: string
  protein_g: number
  fat_g: number
  carbs_g: number
  calories: number
  tags: string[]
  topPick?: boolean
  insight: string
  stats: { label: string; value: string }[]
}

// DEMO-ONLY food catalog used by the frontend search adapter.
// This is NOT real nutrition data and is clearly labeled in the UI.
export const DEMO_FOODS: DemoFood[] = [
  {
    id: "demo-salmon",
    name: "Wild Salmon",
    serving: "100g • Cold Water",
    source: "Cold Water",
    protein_g: 25,
    fat_g: 13,
    carbs_g: 0,
    calories: 208,
    tags: ["Omega-3+", "Premium"],
    topPick: true,
    insight:
      "Optimal for post-workout recovery and neural plasticity enhancement due to high phospholipid concentration.",
    stats: [
      { label: "Potassium", value: "628mg" },
      { label: "Vit. B-12", value: "81% DV" },
      { label: "Selenium", value: "40.2mcg" },
      { label: "Omega-3", value: "2.5g" },
    ],
  },
  {
    id: "demo-avocado",
    name: "Hass Avocado",
    serving: "Medium • Organic",
    source: "Organic",
    protein_g: 2,
    fat_g: 15,
    carbs_g: 9,
    calories: 160,
    tags: [],
    insight:
      "Monounsaturated lipids support hormone synthesis and sustained satiety.",
    stats: [
      { label: "Fiber", value: "7g" },
      { label: "Folate", value: "20% DV" },
      { label: "Potassium", value: "485mg" },
      { label: "Vit. K", value: "26% DV" },
    ],
  },
  {
    id: "demo-pumpkin",
    name: "Pumpkin Seeds",
    serving: "28g • Sprouted",
    source: "Sprouted",
    protein_g: 7,
    fat_g: 13,
    carbs_g: 4,
    calories: 151,
    tags: ["Omega-3+"],
    insight:
      "Mineral-dense lipophilic source supporting testosterone and recovery pathways.",
    stats: [
      { label: "Magnesium", value: "37% DV" },
      { label: "Zinc", value: "23% DV" },
      { label: "Iron", value: "11% DV" },
      { label: "Omega-3", value: "0.4g" },
    ],
  },
  {
    id: "demo-ribeye",
    name: "Grass-fed Ribeye",
    serving: "100g • Pasture",
    source: "Pasture",
    protein_g: 24,
    fat_g: 18,
    carbs_g: 0,
    calories: 248,
    tags: ["Top Pick"],
    insight:
      "Conjugated linoleic acid and creatine-dense for lean mass accretion.",
    stats: [
      { label: "Creatine", value: "0.4g" },
      { label: "Iron", value: "18% DV" },
      { label: "B-12", value: "64% DV" },
      { label: "Zinc", value: "39% DV" },
    ],
  },
  {
    id: "demo-blueberry",
    name: "Blueberry Kombucha",
    serving: "240ml • Fermented",
    source: "Fermented",
    protein_g: 0,
    fat_g: 0,
    carbs_g: 12,
    calories: 45,
    tags: [],
    insight: "Polyphenol-rich probiotic supporting gut microbiome diversity.",
    stats: [
      { label: "Probiotics", value: "Live" },
      { label: "Anthocyanin", value: "High" },
      { label: "Sugar", value: "8g" },
      { label: "Vit. C", value: "10% DV" },
    ],
  },
  {
    id: "demo-eggs",
    name: "Poached Eggs",
    serving: "2 Large • Pasture",
    source: "Pasture",
    protein_g: 12,
    fat_g: 10,
    carbs_g: 1,
    calories: 143,
    tags: [],
    insight: "High bioavailability protein with complete amino acid profile.",
    stats: [
      { label: "Choline", value: "27% DV" },
      { label: "Vit. D", value: "11% DV" },
      { label: "Lutein", value: "High" },
      { label: "B-12", value: "23% DV" },
    ],
  },
]

export const DEMO_RECENT_SEARCHES = [
  "Grass-fed Ribeye",
  "Avocado Oil",
  "Blueberry Kombucha",
]

export const DEMO_SUGGESTIONS = [
  "Wild Salmon",
  "Hass Avocado",
  "Pumpkin Seeds",
  "Poached Eggs",
  "Blueberry Kombucha",
]

export interface DemoFavorite {
  id: string
  name: string
  note: string
  icon: "egg" | "leaf" | "seed" | "fish"
}

export const DEMO_FAVORITES: DemoFavorite[] = [
  { id: "fav-eggs", name: "Poached Eggs", note: "High bioavailability protein", icon: "egg" },
  { id: "fav-spinach", name: "Baby Spinach", note: "Folate & Mineral dense", icon: "leaf" },
]
