"use client"

import { Component, type ErrorInfo, type ReactNode } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { AlertTriangle, RefreshCw } from "lucide-react"

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("[ErrorBoundary] Caught error:", error)
    console.error("[ErrorBoundary] Error stack:", error.stack)
    console.error("[ErrorBoundary] Error info:", errorInfo)
  }

  handleReset = () => {
    console.log("[ErrorBoundary] Resetting")
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback
      return (
        <div className="flex min-h-[400px] items-center justify-center p-8">
          <Card className="max-w-md p-8 text-center">
            <div className="mx-auto mb-4 grid h-16 w-16 place-items-center rounded-2xl bg-error-light">
              <AlertTriangle className="h-8 w-8 text-error" />
            </div>
            <h2 className="mb-2 text-xl font-semibold text-primary">Something went wrong</h2>
            <p className="mb-6 text-sm text-primary-secondary">
              {this.state.error?.message || "An unexpected error occurred."}
            </p>
            <Button onClick={this.handleReset}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Try Again
            </Button>
          </Card>
        </div>
      )
    }
    return this.props.children
  }
}
