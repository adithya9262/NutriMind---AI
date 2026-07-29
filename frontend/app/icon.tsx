import { ImageResponse } from "next/og"

// Next.js App Router will serve this as /icon (favicon)
export const size = { width: 32, height: 32 }
export const contentType = "image/png"

export default function Icon() {
  return new ImageResponse(
    (
      <div
        style={{
          width: 32,
          height: 32,
          borderRadius: 8,
          background: "#22c55e",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {/* Simple "N" letter mark */}
        <div
          style={{
            color: "#ffffff",
            fontSize: 20,
            fontWeight: 700,
            fontFamily: "sans-serif",
            lineHeight: 1,
          }}
        >
          N
        </div>
      </div>
    ),
    { ...size }
  )
}
