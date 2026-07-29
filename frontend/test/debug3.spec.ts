import { test } from '@playwright/test'

test.setTimeout(300000)

const EMAIL = `debug3_${Date.now()}@example.com`
const PASSWORD = 'TestPass123!'

test('direct fetch from browser context', async ({ page }) => {
  // Capture ALL API responses
  page.on('response', async resp => {
    if (resp.url().includes('/api/v1/')) {
      console.log(`[RESP ${resp.status()}] ${resp.request().method()} ${resp.url()} ${resp.request().failure()?.errorText || ''}`)
    }
  })
  
  page.on('console', msg => {
    console.log(`[BROWSER_${msg.type()}] ${msg.text()}`)
  })

  // Register 
  await page.goto('/register', { waitUntil: 'networkidle' })
  await page.fill('input[id="register-email"]', EMAIL)
  await page.fill('input[id="register-password"]', PASSWORD)
  await page.fill('input[id="register-confirm"]', PASSWORD)
  await page.click('button[type="submit"]')
  await page.waitForURL('**/dashboard**', { timeout: 30000 })
  
  // Profile  
  await page.goto('/settings?tab=profile', { waitUntil: 'networkidle' })
  await page.waitForTimeout(2000)
  await page.fill('input[id="settings-dob"]', '1990-06-15')
  await page.selectOption('select[id="settings-sex"]', 'male')
  await page.fill('input[id="settings-height"]', '175')
  await page.fill('input[id="settings-weight"]', '80')
  await page.selectOption('select[id="settings-activity"]', 'moderately_active')
  await page.selectOption('select[id="settings-goal"]', 'maintain_weight')
  await page.fill('input[id="settings-water"]', '2500')
  await page.fill('input[id="settings-sleep"]', '8')
  await page.fill('input[id="settings-cals"]', '2400')
  await page.fill('input[id="settings-protein"]', '150')
  await page.click('button[type="submit"]')
  await page.waitForTimeout(3000)

  // Now manually fetch tasks endpoint from browser context
  console.log('\n=== DIRECT FETCH TEST ===')
  const result = await page.evaluate(async () => {
    const token = localStorage.getItem('backend_access_token')
    if (!token) return { error: 'no token' }

    const results: any[] = []
    const apiBase = 'http://localhost:8000/api/v1'
    
    // Method 1: Direct fetch with abort timeout
    try {
      const controller1 = new AbortController()
      const timeoutId = setTimeout(() => controller1.abort(), 5000)
      const resp = await fetch(`${apiBase}/tasks`, {
        method: 'GET',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        signal: controller1.signal
      })
      clearTimeout(timeoutId)
      results.push({ method: 'direct', status: resp.status, ok: resp.ok })
      const text = await resp.text()
      results.push({ method: 'direct_body', body: text.substring(0, 200) })
    } catch (err: any) {
      results.push({ method: 'direct', error: err.message, name: err.name })
    }

    return results
  })

  console.log('Fetch results:', JSON.stringify(result, null, 2))
  
  await page.screenshot({ path: '../test-results/debug3.png', fullPage: true })
  await page.waitForTimeout(5000)
})
