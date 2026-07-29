import { Leaf } from "lucide-react"

export default function Loading() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="text-center">
        <div className="mx-auto mb-4 p-3 rounded-2xl gradient-brand animate-pulse-soft w-fit">
          <Leaf className="h-6 w-6 text-white" aria-hidden="true" />
        </div>
        <p className="text-sm text-primary-secondary">Loading...</p>
      </div>
    </div>
  )
}
