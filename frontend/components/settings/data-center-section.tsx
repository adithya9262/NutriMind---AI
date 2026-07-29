import * as React from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Download, Upload, FileJson, FileText, FileSpreadsheet, File } from "lucide-react"
import { toast } from "sonner"

const EXPORT_FORMATS = [
  { value: "csv", label: "CSV", icon: FileText },
  { value: "xlsx", label: "Excel", icon: FileSpreadsheet },
  { value: "json", label: "JSON", icon: FileJson },
  { value: "pdf", label: "PDF", icon: File },
  { value: "txt", label: "TXT", icon: FileText },
] as const

const IMPORT_FORMATS = [".json", ".csv", ".txt"] as const

export function DataCenterSection() {
  const [isExporting, setIsExporting] = React.useState(false)
  const [isImporting, setIsImporting] = React.useState(false)
  const [exportFormat, setExportFormat] = React.useState<string>("csv")
  const fileInputRef = React.useRef<HTMLInputElement>(null)

  const handleExport = async () => {
    try {
      setIsExporting(true)
      const { getAccessToken } = await import("@/lib/token-storage")
      const token = getAccessToken("backend") || getAccessToken("supabase")

      const baseUrl = process.env.NEXT_PUBLIC_API_URL?.replace(/\/+$/, "") || ""
      const res = await fetch(`${baseUrl}/settings/export?format=${exportFormat}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })

      if (!res.ok) throw new Error("Failed to export data")

      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const disposition = res.headers.get("Content-Disposition") || ""
      const match = disposition.match(/filename="?([^";\n]+)"?/)
      const filename = match ? match[1] : `nutrimind_export_${new Date().toISOString().split("T")[0]}.${exportFormat}`
      const a = document.createElement("a")
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)

      toast.success(`Data exported as ${exportFormat.toUpperCase()}`)
    } catch {
      toast.error("An error occurred during export.")
    } finally {
      setIsExporting(false)
    }
  }

  const handleImportClick = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const ext = "." + file.name.split(".").pop()?.toLowerCase()
    if (!(IMPORT_FORMATS as readonly string[]).includes(ext)) {
      toast.error("Only JSON, CSV, or TXT files are supported.")
      return
    }

    try {
      setIsImporting(true)
      const { getAccessToken } = await import("@/lib/token-storage")
      const token = getAccessToken("backend") || getAccessToken("supabase")

      const formData = new FormData()
      formData.append("file", file)

      const baseUrl = process.env.NEXT_PUBLIC_API_URL?.replace(/\/+$/, "") || ""
      const res = await fetch(`${baseUrl}/settings/import`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => null)
        throw new Error(errData?.message || "Import failed")
      }

      const data = await res.json()
      if (data.success) {
        toast.success(data.message || "Data imported successfully!")
      } else {
        toast.error(data.message || "Import failed.")
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "An error occurred during import.")
    } finally {
      setIsImporting(false)
      if (fileInputRef.current) fileInputRef.current.value = ""
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h3 className="text-xl font-semibold mb-1">Data Center</h3>
        <p className="text-[var(--color-text-muted)]">
          Manage your personal health data, export your history, and import from external sources.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card className="p-6">
          <div className="flex flex-col h-full">
            <div className="flex items-center gap-2 mb-2">
              <Download className="w-5 h-5 text-brand-500" />
              <h4 className="font-semibold text-lg">Export Data</h4>
            </div>
            <p className="text-sm text-[var(--color-text-muted)] mb-6 flex-grow">
              Download all your nutrition logs, weight entries, and goals in your preferred format.
            </p>
            <div className="flex flex-wrap items-center gap-2 justify-end">
              <select
                value={exportFormat}
                onChange={(e) => setExportFormat(e.target.value)}
                className="h-9 rounded-lg border border-border bg-surface px-2.5 text-xs text-primary"
              >
                {EXPORT_FORMATS.map((fmt) => (
                  <option key={fmt.value} value={fmt.value}>{fmt.label}</option>
                ))}
              </select>
              <Button onClick={handleExport} variant="secondary" disabled={isExporting || isImporting}>
                <Download className="w-4 h-4 mr-2" />
                {isExporting ? "Exporting..." : "Export"}
              </Button>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex flex-col h-full">
            <div className="flex items-center gap-2 mb-2">
              <Upload className="w-5 h-5 text-brand-500" />
              <h4 className="font-semibold text-lg">Import Data</h4>
            </div>
            <p className="text-sm text-[var(--color-text-muted)] mb-6 flex-grow">
              Import your data from JSON, CSV, or TXT exports.
            </p>
            <div className="flex justify-end">
              <input type="file" ref={fileInputRef} className="hidden" accept=".json,.csv,.txt" onChange={handleFileChange} />
              <Button onClick={handleImportClick} variant="secondary" disabled={isImporting || isExporting}>
                <Upload className="w-4 h-4 mr-2" />
                {isImporting ? "Importing..." : "Import"}
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}
