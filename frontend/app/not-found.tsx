import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Leaf, Home } from "lucide-react"

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="text-center max-w-md">
        <div className="mx-auto mb-6 p-4 rounded-2xl bg-brand-light w-fit">
          <Leaf className="h-8 w-8 text-brand" aria-hidden="true" />
        </div>
        <h1 className="text-6xl font-bold text-primary">404</h1>
        <p className="mt-2 text-lg font-semibold text-primary">Page not found</p>
        <p className="mt-1 text-sm text-primary-secondary">
          The page you&apos;re looking for doesn&apos;t exist or has been moved.
        </p>
        <Link href="/dashboard">
          <Button className="mt-6">
            <Home className="h-4 w-4" />
            Back to home
          </Button>
        </Link>
      </div>
    </div>
  )
}
