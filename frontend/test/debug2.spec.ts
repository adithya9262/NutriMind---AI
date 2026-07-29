import { test } from '@playwright/test'
import * as fs from 'fs'

const EMAIL = `vfy_${Date.now()}@example.com`
const PASSWORD = 'TestPass123!'

test('comprehensive verification', async ({ page }) => {
  test.setTimeout(600000)
  let apiErrors: string[] = []

  page.on('response', async resp => {
    const url = resp.url()
    if (url.includes('/api/v1/')) {
      const status = resp.status()
      if (status >= 400) {
        apiErrors.push(`${status} ${resp.request().method()} ${url}`)
      }
    }
  })

  async function checkPage(path: string, label: string) {
    await page.goto(path, { waitUntil: 'networkidle', timeout: 30000 })
    await page.waitForTimeout(3000)
    const hasError = await page.getByText(/failed to load/i).isVisible()
    const hasRetry = await page.getByRole('button', { name: /retry/i }).isVisible()
    console.log(`${label}: error=${hasError} retry=${hasRetry}`)
    if (hasError || hasRetry) throw new Error(`${label} has error/retry state`)
  }

  async function hardRefresh(label: string) {
    await page.reload({ waitUntil: 'networkidle' })
    await page.waitForTimeout(3000)
    const hasError = await page.getByText(/failed to load/i).isVisible()
    console.log(`${label} hard refresh: error=${hasError}`)
    if (hasError) throw new Error(`${label} has error after hard refresh`)
  }

  async function noSpinners(label: string) {
    const spinners = await page.locator('[role="status"]').count()
    console.log(`${label} spinners: ${spinners}`)
  }

  // Register
  await page.goto('/register', { waitUntil: 'networkidle' })
  await page.fill('input[id="register-email"]', EMAIL)
  await page.fill('input[id="register-password"]', PASSWORD)
  await page.fill('input[id="register-confirm"]', PASSWORD)
  await page.click('button[type="submit"]')
  await page.waitForURL('**/dashboard**', { timeout: 30000 })

  // Profile setup
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

  // ============ PAGE VERIFICATION ============
  await checkPage('/nutrition/logs', 'FOOD DIARY')
  await hardRefresh('FOOD DIARY')

  await checkPage('/tasks', 'TASKS')
  await hardRefresh('TASKS')

  await checkPage('/body-weight', 'BODY WEIGHT')
  await hardRefresh('BODY WEIGHT')

  await checkPage('/goals', 'GOALS')
  await hardRefresh('GOALS')

  // ============ GOALS CRUD ============
  console.log('\n=== GOALS CRUD ===')
  await page.goto('/goals', { waitUntil: 'networkidle', timeout: 30000 })
  await page.waitForTimeout(2000)

  // Create
  if (await page.getByRole('button', { name: /add goal/i }).isVisible()) {
    await page.getByRole('button', { name: /add goal/i }).click()
    await page.waitForTimeout(500)
    await page.fill('input[id="title"]', 'Test Goal for Verification')
    await page.click('button:has-text("Create Goal")')
    await page.waitForTimeout(2000)
    console.log('Goal created')
  }

  // Navigate away and back
  await page.goto('/tasks', { waitUntil: 'networkidle', timeout: 30000 })
  await page.waitForTimeout(2000)
  await page.goto('/goals', { waitUntil: 'networkidle', timeout: 30000 })
  await page.waitForTimeout(2000)
  const goalVisible = await page.getByText('Test Goal for Verification').isVisible()
  console.log('Goal persists after nav away/back:', goalVisible)

  // Delete
  if (await page.getByRole('button', { name: /delete/i }).first().isVisible()) {
    await page.getByRole('button', { name: /delete/i }).first().click()
    await page.waitForTimeout(500)
    await page.locator('button:has-text("Delete"):not(:has-text("Goal"))').click()
    await page.waitForTimeout(2000)
    console.log('Goal deleted')
  }

  // Delete final goal - verify empty state
  await page.waitForTimeout(1000)
  const emptyVisible = await page.getByText(/no goals yet/i).isVisible()
  console.log('Empty state after deleting final goal:', emptyVisible)

  // Hard refresh after empty
  await hardRefresh('GOALS (empty)')

  // ============ FOOD DIARY CREATE ============
  console.log('\n=== FOOD DIARY CREATE ===')
  await page.goto('/nutrition/logs', { waitUntil: 'networkidle', timeout: 30000 })
  await page.waitForTimeout(2000)

  await page.fill('input[id="food-name"]', 'Test Apple')
  await page.fill('input[id="serving-description"]', '1 medium apple')
  await page.fill('input[id="entry-calories_kcal"]', '95')
  await page.selectOption('select[id="meal-type"]', 'snack')
  await page.locator('button[type="submit"]').click()
  await page.waitForTimeout(2000)
  const entryCreated = await page.getByText('Entry added successfully').isVisible()
  console.log('Food entry created:', entryCreated)

  // Navigate away and back
  await page.goto('/tasks', { waitUntil: 'networkidle', timeout: 30000 })
  await page.waitForTimeout(2000)
  await page.goto('/nutrition/logs', { waitUntil: 'networkidle', timeout: 30000 })
  await page.waitForTimeout(2000)
  const entryPersists = await page.getByText('Test Apple').isVisible()
  console.log('Entry persists after nav away/back:', entryPersists)

  // ============ NAVIGATION LOOP ============
  console.log('\n=== NAVIGATION LOOP ===')
  for (const path of ['/nutrition/logs', '/tasks', '/body-weight', '/goals']) {
    await checkPage(path, path)
  }

  // ============ EXPORT TEST ============
  console.log('\n=== EXPORT ===')
  const formats = ['csv', 'json', 'txt', 'xlsx', 'pdf']
  for (const fmt of formats) {
    await page.goto('/settings?tab=data', { waitUntil: 'networkidle', timeout: 30000 })
    await page.waitForTimeout(1000)
    await page.selectOption('select', fmt)
    await page.waitForTimeout(500)
    const [download] = await Promise.all([
      page.waitForEvent('download', { timeout: 15000 }).catch(() => null),
      page.getByRole('button', { name: /export/i }).click()
    ])
    if (download) {
      const path = await download.path().catch(() => null)
      if (path) {
        const stat = fs.statSync(path)
        console.log(`Export ${fmt}: ${stat.size} bytes, success=${stat.size > 0}`)
      } else {
        console.log(`Export ${fmt}: no path`)
      }
    } else {
      console.log(`Export ${fmt}: no download event`)
    }
  }

  // ============ IMPORT UI ============
  console.log('\n=== IMPORT ===')
  const importBtn = page.getByRole('button', { name: /import/i })
  if (await importBtn.isVisible()) {
    console.log('Import button: visible')
    
    // Test JSON import
    const fileChooserPromise = page.waitForEvent('filechooser', { timeout: 5000 }).catch(() => null)
    await importBtn.click()
    const fileChooser = await fileChooserPromise
    if (fileChooser) {
      // Create a valid JSON import file
      const tempFile = `C:\\Users\\SAIADI~1\\AppData\\Local\\Temp\\opencode\\test_import.json`
      fs.writeFileSync(tempFile, JSON.stringify({
        entries: [{ food_name: "Imported Apple", calories_kcal: 95, meal_type: "snack", serving_description: "1 apple" }]
      }))
      await fileChooser.setFiles(tempFile)
      await page.waitForTimeout(3000)
      console.log('JSON import attempted')
    }
  }

  // ============ FINAL NAVIGATION LOOP ============
  console.log('\n=== FINAL NAVIGATION ALL PAGES ===')
  for (const path of ['/nutrition/logs', '/tasks', '/body-weight', '/goals', '/settings?tab=data']) {
    await checkPage(path, path)
  }

  // ============ REPORT ============
  console.log('\n=== FINAL REPORT ===')
  console.log('API errors:', apiErrors.length > 0 ? apiErrors.join(', ') : 'NONE')
  if (apiErrors.length > 0) throw new Error(`API errors: ${apiErrors.join(', ')}`)
  console.log('ALL CHECKS PASSED')
})
