import { test } from '@playwright/test'

test.setTimeout(300000)

const EMAIL = `debug_${Date.now()}@example.com`
const PASSWORD = 'TestPass123!'

test('debug all API responses on Food Diary, Tasks, Weight', async ({ page }) => {
  const captured: Array<{ url: string; status: number; method: string; body: string }> = []

  page.on('response', async resp => {
    const url = resp.url()
    if (url.includes('/api/v1/')) {
      const body = await resp.text().catch(() => 'NO_BODY')
      const status = resp.status()
      const method = resp.request().method()
      console.log(`[${status} ${method}] ${url}`)
      if (body.length < 2000) {
        console.log(`  Body: ${body.substring(0, 500)}`)
      }
      captured.push({ url, status, method, body: body.substring(0, 500) })
    }
  })

  page.on('pageerror', err => console.log(`[PAGE_ERROR] ${err.message}`))
  page.on('console', msg => {
    if (msg.type() === 'error' || msg.type() === 'warning') {
      console.log(`[CONSOLE_${msg.type().toUpperCase()}] ${msg.text()}`)
    }
  })

  // Register
  console.log('=== Registering ===')
  await page.goto('/register', { waitUntil: 'networkidle' })
  await page.fill('input[id="register-email"]', EMAIL)
  await page.fill('input[id="register-password"]', PASSWORD)
  await page.fill('input[id="register-confirm"]', PASSWORD)
  await page.click('button[type="submit"]')
  await page.waitForURL('**/dashboard**', { timeout: 30000 })
  console.log('Registered')

  // Complete settings profile
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

  // Now visit pages one at a time with delays
  console.log('\n=== Visiting Food Diary ===')
  await page.goto('/nutrition/logs', { waitUntil: 'domcontentloaded', timeout: 30000 })
  await page.waitForTimeout(5000)

  // Check what's visible
  const pageContent = await page.locator('body').textContent().catch(() => 'NO_CONTENT')
  const hasRetry = pageContent.includes('Retry')
  const hasEntryForm = pageContent.includes('Add Entry') || pageContent.includes('New Food Entry')
  const hasNoEntries = pageContent.includes('No entries logged')
  console.log(`Page has Retry: ${hasRetry}, EntryForm: ${hasEntryForm}, NoEntries: ${hasNoEntries}`)

  if (hasRetry) {
    const errorEl = page.locator('[role="alert"]').first()
    if (await errorEl.isVisible().catch(() => false)) {
      console.log(`Alert text: ${await errorEl.textContent()}`)
    }
    // Check if there are multiple Retry buttons
    const retryButtons = page.locator('button:has-text("Retry")')
    console.log(`Number of Retry buttons: ${await retryButtons.count()}`)
  }

  await page.screenshot({ path: '../test-results/debug-food-diary.png', fullPage: true })

  console.log('\n=== Visiting Tasks ===')
  await page.goto('/tasks', { waitUntil: 'domcontentloaded', timeout: 30000 })
  await page.waitForTimeout(5000)
  const tasksContent = await page.locator('body').textContent().catch(() => 'NO_CONTENT')
  const tasksRetry = tasksContent.includes('Retry')
  console.log(`Tasks has Retry: ${tasksRetry}`)
  await page.screenshot({ path: '../test-results/debug-tasks.png', fullPage: true })

  console.log('\n=== Visiting Body Weight ===')
  await page.goto('/body-weight', { waitUntil: 'domcontentloaded', timeout: 30000 })
  await page.waitForTimeout(5000)
  const weightContent = await page.locator('body').textContent().catch(() => 'NO_CONTENT')
  const weightRetry = weightContent.includes('Retry')
  console.log(`Weight has Retry: ${weightRetry}`)
  await page.screenshot({ path: '../test-results/debug-weight.png', fullPage: true })
})
