"use client"

import { useState, type FormEvent } from "react"
import { motion } from "framer-motion"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { FormField } from "@/components/ui/form-field"
import { Alert } from "@/components/ui/alert"
import { Spinner } from "@/components/ui/spinner"
import { AlertTriangle, Check, Download, Save, Trash2, X } from "lucide-react"
import * as settingsApi from "@/services/api/settings"
import { createClient } from "@/lib/supabase/client"

interface SecuritySectionProps {
  onUpdatePassword: (password: string) => Promise<string | null>
  onLogout: () => void
  onNavigateToLogin: () => void
}

export function SecuritySection({ onUpdatePassword, onLogout, onNavigateToLogin }: SecuritySectionProps) {
  const [currentPassword, setCurrentPassword] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [passwordError, setPasswordError] = useState<string | null>(null)
  const [passwordSuccess, setPasswordSuccess] = useState(false)
  const [passwordSubmitting, setPasswordSubmitting] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [deleteSubmitting, setDeleteSubmitting] = useState(false)
  const [deleteError, setDeleteError] = useState<string | null>(null)
  const [exporting, setExporting] = useState(false)
  const [exportFormat, setExportFormat] = useState<"csv" | "xlsx" | "json" | "pdf" | "txt">("csv")
  const [exportError, setExportError] = useState<string | null>(null)

  async function handlePasswordChange(e: FormEvent) {
    e.preventDefault()
    setPasswordError(null)
    setPasswordSuccess(false)

    if (!currentPassword) {
      setPasswordError("Current password is required.")
      return
    }
    if (newPassword.length < 8) {
      setPasswordError("New password must be at least 8 characters.")
      return
    }
    if (newPassword !== confirmPassword) {
      setPasswordError("New passwords do not match.")
      return
    }

    setPasswordSubmitting(true)
    const err = await onUpdatePassword(newPassword)
    setPasswordSubmitting(false)

    if (err) {
      setPasswordError(err)
    } else {
      setPasswordSuccess(true)
      setCurrentPassword("")
      setNewPassword("")
      setConfirmPassword("")
      setTimeout(() => setPasswordSuccess(false), 4000)
    }
  }

  async function handleExportData() {
    setExporting(true)
    setExportError(null)
    try {
      await settingsApi.exportData(exportFormat)
    } catch {
      setExportError("Failed to export data.")
    } finally {
      setExporting(false)
    }
  }

  async function handleDeleteAccount() {
    setDeleteSubmitting(true)
    setDeleteError(null)
    try {
      await settingsApi.deleteAccount()
      const supabase = createClient()
      await supabase.auth.signOut()
      onLogout()
      onNavigateToLogin()
    } catch {
      setDeleteError("Failed to delete account. Please try again.")
      setDeleteSubmitting(false)
    }
  }

  return (
    <div className="space-y-6">
      <Card className="p-6 space-y-5">
        <div>
          <h3 className="text-base font-semibold text-primary">Change Password</h3>
          <p className="text-sm text-primary-secondary mt-0.5">Update your account password</p>
        </div>

        {passwordSuccess && (
          <Alert variant="success" dismissible onDismiss={() => setPasswordSuccess(false)}>
            Password updated successfully.
          </Alert>
        )}
        {passwordError && (
          <Alert variant="error" dismissible onDismiss={() => setPasswordError(null)}>
            {passwordError}
          </Alert>
        )}

        <form onSubmit={handlePasswordChange} className="space-y-4">
          <FormField label="Current Password" htmlFor="current-password">
            <Input id="current-password" type="password" placeholder="Enter current password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} />
          </FormField>
          <FormField label="New Password" htmlFor="new-password">
            <Input id="new-password" type="password" placeholder="At least 8 characters" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
          </FormField>
          <FormField label="Confirm New Password" htmlFor="confirm-password">
            <Input id="confirm-password" type="password" placeholder="Repeat new password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} />
          </FormField>
          <Button type="submit" disabled={passwordSubmitting}>
            {passwordSubmitting ? <Spinner size="sm" /> : <Save className="h-4 w-4" />}
            Update Password
          </Button>
        </form>
      </Card>

      <Card className="p-6 space-y-5">
        <div>
          <h3 className="text-base font-semibold text-primary">Data & Account</h3>
          <p className="text-sm text-primary-secondary mt-0.5">Export or delete your account data</p>
        </div>

        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-primary">Export Data</p>
            <p className="text-xs text-primary-secondary">Download your data in CSV, Excel, JSON, PDF, or TXT format</p>
          </div>
          <div className="flex items-center gap-2">
            <select
              value={exportFormat}
              onChange={(e) => setExportFormat(e.target.value as "csv" | "xlsx" | "json" | "pdf" | "txt")}
              className="h-9 rounded-lg border border-border bg-surface px-2.5 text-xs text-primary"
            >
              <option value="csv">CSV</option>
              <option value="xlsx">Excel</option>
              <option value="json">JSON</option>
              <option value="pdf">PDF</option>
              <option value="txt">TXT</option>
            </select>
            <Button variant="secondary" onClick={handleExportData} disabled={exporting}>
              {exporting ? <Spinner size="sm" /> : <Download className="h-4 w-4" />}
              Export
            </Button>
          </div>
        </div>
        {exportError && (
          <Alert variant="error" dismissible onDismiss={() => setExportError(null)}>
            {exportError}
          </Alert>
        )}

        <div className="border-t border-border pt-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-error">Delete Account</p>
              <p className="text-xs text-primary-secondary">Permanently delete your account and all data</p>
            </div>
            <Button variant="danger" onClick={() => setShowDeleteConfirm(true)}>
              <Trash2 className="h-4 w-4" />
              Delete
            </Button>
          </div>
        </div>
      </Card>

      {showDeleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="w-full max-w-md"
          >
            <Card className="p-6 space-y-4">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-full bg-error-light flex items-center justify-center">
                  <AlertTriangle className="h-5 w-5 text-error" />
                </div>
                <div>
                  <h3 className="text-base font-semibold text-primary">Delete Account</h3>
                  <p className="text-sm text-primary-secondary">This action cannot be undone.</p>
                </div>
              </div>

              <p className="text-sm text-primary-secondary">
                All your profile data, goals, nutrition logs, and personal information will be permanently deleted.
              </p>

              {deleteError && (
                <Alert variant="error" dismissible onDismiss={() => setDeleteError(null)}>
                  {deleteError}
                </Alert>
              )}

              <div className="flex gap-3 justify-end">
                <Button variant="secondary" onClick={() => { setShowDeleteConfirm(false); setDeleteError(null) }}>
                  <X className="h-4 w-4" />
                  Cancel
                </Button>
                <Button variant="danger" onClick={handleDeleteAccount} disabled={deleteSubmitting}>
                  {deleteSubmitting ? <Spinner size="sm" /> : <Check className="h-4 w-4" />}
                  Confirm Delete
                </Button>
              </div>
            </Card>
          </motion.div>
        </div>
      )}
    </div>
  )
}
