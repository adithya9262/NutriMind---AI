"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import { motion } from "framer-motion"
import { Camera, ImageUp, RotateCcw, Utensils, Upload } from "lucide-react"
import { Alert } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { PageHeader } from "@/components/ui/page-header"
import { Spinner } from "@/components/ui/spinner"
import { analyzeFoodImage } from "@/services/api/food-recognition"
import type { DetectedFood } from "@/types/nutrition"

type PageStatus = "idle" | "analyzing" | "results" | "error"

function getConfidenceVariant(score: number): "success" | "warning" | "error" {
  if (score >= 0.7) return "success"
  if (score >= 0.4) return "warning"
  return "error"
}

function getConfidenceLabel(score: number): string {
  if (score >= 0.7) return "High"
  if (score >= 0.4) return "Medium"
  return "Low"
}

function DetectedFoodCard({
  food,
  index,
  onAddToDiary,
}: {
  food: DetectedFood
  index: number
  onAddToDiary: (food: DetectedFood) => void
}) {
  const confidence = Number.parseFloat(food.confidence_score) || 0

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1, duration: 0.35 }}
    >
      <Card
        variant="glass"
        className="overflow-hidden transition-all duration-300 hover:border-brand/40 hover:-translate-y-0.5"
      >
        <div className="p-5 space-y-4">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0 flex-1">
              <h3 className="font-semibold text-primary text-base leading-tight capitalize">
                {food.food_name}
              </h3>
              {food.serving_size_g && (
                <p className="text-xs text-primary-muted/70 mt-0.5">
                  Serving: {food.serving_size_g}g
                </p>
              )}
            </div>
            <Badge variant={getConfidenceVariant(confidence)} size="sm">
              {getConfidenceLabel(confidence)} ({food.confidence_score})
            </Badge>
          </div>

          <div className="flex flex-wrap gap-1.5">
            <span className="inline-flex items-center gap-1 rounded-lg bg-surface-highest/50 px-2.5 py-1 text-xs font-medium border border-white/5 text-primary">
              {food.calories_kcal}
              <span className="text-[10px] text-primary-muted/50 font-normal ml-0.5">
                kcal
              </span>
            </span>
            <span className="inline-flex items-center gap-1 rounded-lg bg-surface-highest/50 px-2.5 py-1 text-xs font-medium border border-white/5 text-brand">
              {food.protein_g}g
              <span className="text-[10px] text-primary-muted/50 font-normal ml-0.5">
                Protein
              </span>
            </span>
            <span className="inline-flex items-center gap-1 rounded-lg bg-surface-highest/50 px-2.5 py-1 text-xs font-medium border border-white/5 text-info">
              {food.carbohydrate_g}g
              <span className="text-[10px] text-primary-muted/50 font-normal ml-0.5">
                Carbs
              </span>
            </span>
            <span className="inline-flex items-center gap-1 rounded-lg bg-surface-highest/50 px-2.5 py-1 text-xs font-medium border border-white/5 text-warning">
              {food.fat_g}g
              <span className="text-[10px] text-primary-muted/50 font-normal ml-0.5">
                Fat
              </span>
            </span>
          </div>

          {food.ingredients && food.ingredients.length > 0 && (
            <div className="pt-1 border-t border-border/40">
              <p className="text-[11px] text-primary-muted/60 mb-1.5 font-medium uppercase tracking-wider">
                Ingredients
              </p>
              <div className="flex flex-wrap gap-1">
                {food.ingredients.map((ingredient, i) => (
                  <span
                    key={i}
                    className="text-[11px] text-primary-secondary bg-surface-highest/30 border border-border/50 rounded-md px-2 py-0.5"
                  >
                    {ingredient}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="flex justify-end pt-1 border-t border-border/40">
            <Button
              variant="secondary"
              size="sm"
              pill
              onClick={() => onAddToDiary(food)}
            >
              <Utensils className="h-3.5 w-3.5" />
              Add to Food Diary
            </Button>
          </div>
        </div>
      </Card>
    </motion.div>
  )
}

export default function FoodRecognitionPage() {
  const [status, setStatus] = useState<PageStatus>("idle")
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [foods, setFoods] = useState<DetectedFood[]>([])
  const [errorMessage, setErrorMessage] = useState("")
  const fileInputRef = useRef<HTMLInputElement>(null)
  const dropRef = useRef<HTMLDivElement>(null)
  const previewUrlRef = useRef<string | null>(null)
  const [isDragOver, setIsDragOver] = useState(false)

  useEffect(() => {
    return () => {
      if (previewUrlRef.current) {
        URL.revokeObjectURL(previewUrlRef.current)
      }
    }
  }, [])

  function handleFile(file: File) {
    if (!file.type.startsWith("image/")) {
      setErrorMessage("Please select a valid image file.")
      return
    }
    if (file.size > 10 * 1024 * 1024) {
      setErrorMessage("File must be under 10MB.")
      return
    }
    setErrorMessage("")
    setSelectedFile(file)
    if (previewUrlRef.current) {
      URL.revokeObjectURL(previewUrlRef.current)
    }
    const url = URL.createObjectURL(file)
    previewUrlRef.current = url
    setPreviewUrl(url)
    setStatus("idle")
    setFoods([])
  }

  function handleFileInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
  }

  function handleCameraCapture() {
    fileInputRef.current?.click()
  }

  function handleDragOver(e: React.DragEvent) {
    e.preventDefault()
    setIsDragOver(true)
  }

  function handleDragLeave() {
    setIsDragOver(false)
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault()
    setIsDragOver(false)
    const file = e.dataTransfer.files?.[0]
    if (file) handleFile(file)
  }

  function handleReset() {
    setStatus("idle")
    setSelectedFile(null)
    if (previewUrlRef.current) {
      URL.revokeObjectURL(previewUrlRef.current)
      previewUrlRef.current = null
    }
    setPreviewUrl(null)
    setFoods([])
    setErrorMessage("")
    if (fileInputRef.current) fileInputRef.current.value = ""
  }

  const handleAnalyze = useCallback(async () => {
    if (!selectedFile) return
    setStatus("analyzing")
    setErrorMessage("")

    try {
      const response = await analyzeFoodImage(selectedFile)

      if (!response.success) {
        setStatus("error")
        setErrorMessage(response.message || "Analysis failed. Please try again.")
        return
      }

      if (!response.data?.foods || response.data.foods.length === 0) {
        const rawMsg = response.data?.raw_response || ""
        const isApiError = rawMsg.includes("API key") || rawMsg.includes("401") || rawMsg.includes("403") || rawMsg.includes("quota") || rawMsg.includes("rate limit")
        setStatus("error")
        setErrorMessage(isApiError ? "Food recognition service is currently unavailable. Please try again later." : (response.message || "No food items detected in the image."))
        return
      }

      setFoods(response.data.foods)
      setStatus("results")
    } catch (err) {
      setStatus("error")
      setErrorMessage(
        err instanceof Error ? err.message : "An unexpected error occurred.",
      )
    }
  }, [selectedFile])

  function handleAddToDiary(food: DetectedFood) {
    const hour = new Date().getHours()
    let meal_type = "breakfast"
    if (hour >= 11 && hour < 15) meal_type = "lunch"
    else if (hour >= 15 && hour < 21) meal_type = "dinner"
    else if (hour >= 21 || hour < 6) meal_type = "snack"
    const params = new URLSearchParams({
      food_name: food.food_name,
      serving_description: food.serving_size_g ? `${food.serving_size_g}g` : "100g",
      calories_kcal: food.calories_kcal || "0",
      protein_g: food.protein_g || "0",
      carbohydrate_g: food.carbohydrate_g || "0",
      fat_g: food.fat_g || "0",
      meal_type,
    })
    window.location.href = `/nutrition/logs?${params.toString()}`
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Food Recognition"
        description="AI-powered food identification — snap a photo and get instant macro analysis."
      />

      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        capture="environment"
        onChange={handleFileInputChange}
        className="hidden"
        aria-hidden="true"
      />

      {status === "idle" && !previewUrl && (
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3 }}
        >
          <Card variant="glass" className="p-8">
            <div
              ref={dropRef}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-12 text-center transition-all duration-200 ${
                isDragOver
                  ? "border-brand bg-brand-light/20"
                  : "border-border/60 hover:border-brand/40 hover:bg-surface-highest/20"
              }`}
            >
              <div className="mb-5 grid h-16 w-16 place-items-center rounded-2xl bg-brand-light">
                <ImageUp className="h-8 w-8 text-brand" aria-hidden="true" />
              </div>
              <h3 className="text-lg font-semibold text-primary">
                Upload a food photo
              </h3>
              <p className="mt-1.5 text-sm text-primary-secondary max-w-sm">
                Drag and drop an image here, or use the buttons below to capture
                or choose a photo.
              </p>
              <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
                <Button
                  variant="primary"
                  size="md"
                  pill
                  onClick={handleCameraCapture}
                >
                  <Camera className="h-4 w-4" />
                  Take Photo
                </Button>
                <Button
                  variant="secondary"
                  size="md"
                  pill
                  onClick={() => fileInputRef.current?.click()}
                >
                  <Upload className="h-4 w-4" />
                  Choose File
                </Button>
              </div>
            </div>
          </Card>
        </motion.div>
      )}

      {previewUrl && status !== "analyzing" && status !== "results" && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-4"
        >
          <Card variant="glass" className="p-5">
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-primary">Image Preview</h3>
              <div className="overflow-hidden rounded-xl">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={previewUrl}
                  alt="Selected food"
                  className="w-full max-h-80 object-contain bg-black/20"
                />
              </div>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <p className="text-xs text-primary-muted/70 truncate max-w-[50%]">
                  {selectedFile?.name}
                </p>
                <div className="flex gap-2">
                  <Button variant="ghost" size="sm" pill onClick={handleReset}>
                    <RotateCcw className="h-3.5 w-3.5" />
                    Change
                  </Button>
                  <Button variant="primary" size="sm" pill onClick={handleAnalyze}>
                    <Utensils className="h-3.5 w-3.5" />
                    Analyze
                  </Button>
                </div>
              </div>
            </div>
          </Card>
        </motion.div>
      )}

      {status === "analyzing" && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.3 }}
        >
          <Card variant="glass" className="p-10">
            <div className="flex flex-col items-center justify-center text-center space-y-5">
              {previewUrl && (
                <div className="relative overflow-hidden rounded-2xl">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={previewUrl}
                    alt="Analyzing"
                    className="w-40 h-40 object-cover opacity-60"
                  />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="h-12 w-12 rounded-full bg-surface/80 backdrop-blur-sm flex items-center justify-center shadow-lg">
                      <Spinner size="lg" />
                    </div>
                  </div>
                  {/* Scanning bar animation */}
                  <motion.div
                    className="absolute left-0 top-0 w-full h-1 bg-brand-primary shadow-[0_0_8px_2px_rgba(var(--color-brand-primary-rgb),0.5)]"
                    animate={{ y: [0, 160, 0] }}
                    transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
                  />
                </div>
              )}
              <div>
                <div className="flex items-center justify-center gap-2.5">
                  <Spinner size="md" />
                  <p className="text-sm font-semibold text-primary">
                    Analyzing Image
                  </p>
                </div>
                <p className="mt-1.5 text-xs text-primary-muted/70">
                  Identifying food items and calculating nutritional data...
                </p>
              </div>
              <div className="flex gap-1.5">
                <span className="h-2 w-2 rounded-full bg-brand animate-bounce [animation-delay:0ms]" />
                <span className="h-2 w-2 rounded-full bg-brand animate-bounce [animation-delay:150ms]" />
                <span className="h-2 w-2 rounded-full bg-brand animate-bounce [animation-delay:300ms]" />
              </div>
            </div>
          </Card>
        </motion.div>
      )}

      {status === "error" && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-4"
        >
          {previewUrl && (
            <Card variant="glass" className="p-5">
              <div className="overflow-hidden rounded-xl mb-4">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={previewUrl}
                  alt="Selected food"
                  className="w-full max-h-60 object-contain bg-black/20"
                />
              </div>
            </Card>
          )}
          <Alert variant="error">
            <div className="flex items-center justify-between w-full">
              <span>{errorMessage || "Analysis failed. Please try again."}</span>
              <div className="flex gap-2 shrink-0">
                <Button variant="secondary" size="sm" pill onClick={handleReset}>
                  <RotateCcw className="h-3.5 w-3.5" />
                  Try Again
                </Button>
                <Button variant="primary" size="sm" pill onClick={handleAnalyze}>
                  Retry
                </Button>
              </div>
            </div>
          </Alert>
        </motion.div>
      )}

      {status === "results" && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="space-y-4"
        >
          {previewUrl && (
            <Card variant="glass" className="p-5">
              <div className="overflow-hidden rounded-xl mb-4">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={previewUrl}
                  alt="Analyzed food"
                  className="w-full max-h-60 object-contain bg-black/20"
                />
              </div>
              <div className="flex justify-end">
                <Button variant="ghost" size="sm" pill onClick={handleReset}>
                  <RotateCcw className="h-3.5 w-3.5" />
                  Try Another Image
                </Button>
              </div>
            </Card>
          )}

          <div className="flex items-center gap-2 text-sm text-primary-secondary">
            <Utensils className="h-4 w-4 text-brand" aria-hidden="true" />
            <span>
              Detected{" "}
              <span className="font-semibold text-primary">{foods.length}</span>{" "}
              food item{foods.length === 1 ? "" : "s"}
            </span>
          </div>

          <div className="space-y-3">
            {foods.map((food, index) => (
              <DetectedFoodCard
                key={`${food.food_name}-${index}`}
                food={food}
                index={index}
                onAddToDiary={handleAddToDiary}
              />
            ))}
          </div>
        </motion.div>
      )}
    </div>
  )
}
