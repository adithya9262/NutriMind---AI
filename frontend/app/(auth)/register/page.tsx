"use client"

import { useState, type FormEvent } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { motion } from "framer-motion"
import { useAuth } from "@/contexts/auth-context"
import { registerUser } from "@/services/api/auth"
import { setAccessToken } from "@/lib/token-storage"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { FormField } from "@/components/ui/form-field"
import { Alert } from "@/components/ui/alert"
import { Spinner } from "@/components/ui/spinner"
import { Logo } from "@/components/logo"
import { OAuthButtons } from "@/components/auth/oauth-buttons"
import { Divider } from "@/components/auth/divider"
import { Eye, EyeOff, UserPlus } from "lucide-react"

export default function RegisterPage() {
  const router = useRouter()
  const { signInWithGoogle, signInWithApple, refreshSession } = useAuth()

  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)
  const [fieldErrors, setFieldErrors] = useState<{
    email?: string
    password?: string
    confirmPassword?: string
  }>({})

  function validate(): boolean {
    const errors: {
      email?: string
      password?: string
      confirmPassword?: string
    } = {}
    const trimmedEmail = email.trim()
    if (!trimmedEmail) errors.email = "Email is required."
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmedEmail)) errors.email = "Please enter a valid email address."
    if (!password) errors.password = "Password is required."
    else if (password.length < 8) errors.password = "Password must be at least 8 characters."
    else if (password.length > 128) errors.password = "Password must be at most 128 characters."
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
      const result = await registerUser({ email: email.trim().toLowerCase(), password })
      if (!result.success) {
        const msg = (result.error?.message || "").toLowerCase()
        const isOAuthAccount = result.error?.code === "EMAIL_ALREADY_REGISTERED"
        if (msg.includes("already")) {
          setError(isOAuthAccount
            ? "An account with this email already exists. This account was created with Google or Apple. Please sign in with Google or Apple, or use 'Forgot Password' to set a password."
            : "An account with this email already exists. Try signing in.")
        } else {
          setError(result.error?.message || "Registration failed. Please try again.")
        }
      } else if (result.data) {
        // Store the backend token and set a session cookie for the middleware
        setAccessToken(result.data.access_token, "backend")
        document.cookie = `nutrimind_session=1; path=/; max-age=86400; SameSite=Lax`
        await refreshSession()
        router.push("/dashboard?welcome=true")
      }
    } catch {
      setError("An unexpected error occurred. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-background px-4 py-12">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -right-40 -top-40 h-[40rem] w-[40rem] rounded-full bg-brand-light blur-[100px] animate-pulse" />
        <div className="absolute -bottom-40 -left-40 h-[40rem] w-[40rem] rounded-full bg-brand-light blur-[100px] animate-pulse" style={{ animationDelay: '2s' }} />
      </div>

      <div className="relative w-full max-w-md">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-8 flex flex-col items-center text-center"
        >
          <Link href="/" aria-label="NutriMind AI home" className="mb-6">
            <Logo size={36} />
          </Link>
          <h1 className="text-3xl font-semibold tracking-tight text-primary">Create Account</h1>
          <p className="mt-2 text-sm text-primary-secondary">
            Start your precision nutrition journey today.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <div className="rounded-xl border border-[var(--color-border)] bg-surface p-6 shadow-lg sm:p-8">
            <OAuthButtons
              disabled={loading}
              className="mb-5"
              onGoogle={async () => {
                try {
                  await signInWithGoogle()
                } catch {
                  setError("Unable to start Google sign-in. Check your network connection or try again.")
                }
              }}
              onApple={async () => {
                try {
                  await signInWithApple()
                } catch {
                  setError("Unable to start Apple sign-in. Check your network connection or try again.")
                }
              }}
            />

            <Divider className="mb-5">Or create with email</Divider>

            <form onSubmit={handleSubmit} noValidate className="space-y-5">
              {error && (
                <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }}>
                  <Alert variant="error" dismissible onDismiss={() => setError("")}>
                    {error}
                  </Alert>
                </motion.div>
              )}

              <FormField
                label="Email Address"
                required
                error={fieldErrors.email}
                htmlFor="register-email"
              >
                <Input
                  id="register-email"
                  type="email"
                  autoComplete="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={loading}
                />
              </FormField>

              <FormField
                label="Password"
                required
                error={fieldErrors.password}
                htmlFor="register-password"
              >
                <div className="relative">
                  <Input
                    id="register-password"
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
                label="Confirm Password"
                required
                error={fieldErrors.confirmPassword}
                htmlFor="register-confirm"
              >
                <Input
                  id="register-confirm"
                  type={showPassword ? "text" : "password"}
                  autoComplete="new-password"
                  placeholder="Repeat your password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  disabled={loading}
                />
              </FormField>

              <Button type="submit" className="w-full h-11" disabled={loading}>
                {loading ? (
                  <>
                    <Spinner size="sm" className="mr-2" />
                    Creating account...
                  </>
                ) : (
                  <>
                    <UserPlus className="h-4 w-4" />
                    Create Account
                  </>
                )}
              </Button>
            </form>
          </div>
        </motion.div>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="mt-6 text-center text-sm text-primary-secondary"
        >
          Already have an account?{" "}
          <Link
            href="/login"
            className="font-semibold text-brand-primary transition-colors hover:text-brand-hover"
          >
            Sign In
          </Link>
        </motion.p>

        <p className="mt-8 text-center text-xs text-primary-muted">
          © 2026 NutriMind AI. Precision Performance.
        </p>
      </div>
    </div>
  )
}
