"use client"

import { useState, type FormEvent } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { motion } from "framer-motion"
import { useAuth } from "@/contexts/auth-context"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { FormField } from "@/components/ui/form-field"
import { Alert } from "@/components/ui/alert"
import { Card } from "@/components/ui/card"
import { Logo } from "@/components/logo"
import { ArrowLeft, Lock, Eye, EyeOff, CheckCircle } from "lucide-react"

export default function ResetPasswordPage() {
  const router = useRouter()
  const { updatePassword } = useAuth()

  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [fieldErrors, setFieldErrors] = useState<{
    password?: string
    confirmPassword?: string
  }>({})

  function validate(): boolean {
    const errors: { password?: string; confirmPassword?: string } = {}
    if (!password) errors.password = "Password is required."
    else if (password.length < 8) errors.password = "Password must be at least 8 characters."
    if (password !== confirmPassword) errors.confirmPassword = "Passwords do not match."
    setFieldErrors(errors)
    return Object.keys(errors).length === 0
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError("")
    if (!validate()) return

    setLoading(true)
    try {
      const errMsg = await updatePassword(password)
      if (errMsg) {
        setError(errMsg)
      } else {
        setSuccess(true)
        setTimeout(() => router.push("/login"), 3000)
      }
    } catch {
      setError("An unexpected error occurred. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background py-12 px-4">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-80 h-80 rounded-full bg-brand-light blur-3xl" />
          <div className="absolute -bottom-40 -left-40 w-80 h-80 rounded-full bg-brand-light blur-3xl" />
        </div>
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-md relative text-center"
        >
          <Card className="p-8 sm:p-10">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-success-light">
              <CheckCircle className="h-8 w-8 text-success" />
            </div>
            <h2 className="text-xl font-bold text-primary">Password Updated</h2>
            <p className="text-sm text-primary-secondary mt-2">
              Your security key has been reset successfully. Redirecting to login...
            </p>
            <Link
              href="/login"
              className="inline-flex items-center gap-2 mt-6 text-sm font-medium text-brand-primary hover:text-brand-hover transition-colors"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to sign in
            </Link>
          </Card>
        </motion.div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background py-12 px-4">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 rounded-full bg-brand-light blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 rounded-full bg-brand-light blur-3xl" />
      </div>

      <div className="w-full max-w-md relative">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-8 flex flex-col items-center text-center"
        >
          <Link href="/" aria-label="NutriMind AI home" className="mb-6">
            <Logo size={36} />
          </Link>
          <h1 className="text-3xl font-semibold tracking-tight text-primary">Set New Security Key</h1>
          <p className="mt-2 max-w-sm text-sm text-primary-secondary">
            Enter your new password below.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <Card className="p-6 sm:p-8">
            <form onSubmit={handleSubmit} noValidate className="space-y-5">
              {error && (
                <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }}>
                  <Alert variant="error">{error}</Alert>
                </motion.div>
              )}

              <FormField
                label="New Security Key"
                required
                error={fieldErrors.password}
                htmlFor="reset-password"
              >
                <div className="relative">
                  <Input
                    id="reset-password"
                    type={showPassword ? "text" : "password"}
                    autoComplete="new-password"
                    placeholder="At least 8 characters"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    disabled={loading}
                    className="pr-11"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((v) => !v)}
                    aria-label={showPassword ? "Hide password" : "Show password"}
                    aria-pressed={showPassword}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-primary-muted transition-colors hover:text-primary"
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </FormField>

              <FormField
                label="Confirm Security Key"
                required
                error={fieldErrors.confirmPassword}
                htmlFor="reset-confirm"
              >
                <Input
                  id="reset-confirm"
                  type={showPassword ? "text" : "password"}
                  autoComplete="new-password"
                  placeholder="Repeat your new security key"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  disabled={loading}
                />
              </FormField>

              <Button type="submit" className="w-full h-11" disabled={loading}>
                {loading ? (
                  <>Updating security key...</>
                ) : (
                  <>
                    <Lock className="h-4 w-4" />
                    Update Security Key
                  </>
                )}
              </Button>
            </form>
          </Card>
        </motion.div>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="mt-6 text-center"
        >
          <Link
            href="/login"
            className="inline-flex items-center gap-2 text-sm font-medium text-brand hover:text-brand-hover transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to sign in
          </Link>
        </motion.p>
      </div>
    </div>
  )
}
