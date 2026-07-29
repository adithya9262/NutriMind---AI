"use client"

import { useState, type FormEvent } from "react"
import Link from "next/link"
import { motion } from "framer-motion"
import { useAuth } from "@/contexts/auth-context"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { FormField } from "@/components/ui/form-field"
import { Alert } from "@/components/ui/alert"
import { Card } from "@/components/ui/card"
import { Logo } from "@/components/logo"
import { ArrowLeft, Send, MailCheck } from "lucide-react"

export default function ForgotPasswordPage() {
  const { resetPassword } = useAuth()
  const [email, setEmail] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)
  const [sent, setSent] = useState(false)
  const [fieldError, setFieldError] = useState<string | undefined>()

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError("")
    setFieldError(undefined)

    if (!email.trim()) {
      setFieldError("Email is required.")
      return
    }

    setLoading(true)

    try {
      const errMsg = await resetPassword(email.trim())
      if (errMsg) {
        setError(errMsg)
      } else {
        setSent(true)
      }
    } catch {
      setError("An unexpected error occurred. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  if (sent) {
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
              <MailCheck className="h-8 w-8 text-success" />
            </div>
            <h2 className="text-xl font-bold text-primary">Check your email</h2>
            <p className="text-sm text-primary-secondary mt-2">
              If an account exists for <strong className="text-primary">{email}</strong>,
              you will receive a password reset link shortly.
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
          <h1 className="text-3xl font-semibold tracking-tight text-primary">Reset Password</h1>
          <p className="mt-2 max-w-sm text-sm text-primary-secondary">
            Enter your email address and we&apos;ll send you a link to reset your password.
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
                label="Email"
                required
                error={fieldError}
                htmlFor="reset-email"
              >
                <Input
                  id="reset-email"
                  type="email"
                  autoComplete="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={loading}
                />
              </FormField>

              <Button type="submit" className="w-full h-11" disabled={loading}>
                {loading ? (
                  <>Sending reset link...</>
                ) : (
                  <>
                    <Send className="h-4 w-4" />
                    Send reset link
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
