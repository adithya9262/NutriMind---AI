import { test } from '@playwright/test'

test.setTimeout(300000)

function uuidv4() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = Math.random() * 16 | 0
    return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16)
  })
}

const EMAIL = `retry_${Date.now()}@example.com`
const PASSWORD = 'TestPass123!'

test('reproduce Retry states on Food Diary, Tasks, Weight Tracker', async ({ page }) => {
  const errors: string[] = []
  const apiErrors: Array<{ url: string; status: number; method: string }> = []

  page.on('pageerror', err => errors.push(err.message))
  page.on('console', msg => {
    if (msg.type() === 'error') console.log(`[ERR] ${msg.text()}`)
    if (msg.text().includes('401') || msg.text().includes('500') || msg.text().includes('Failed to load')) {
      console.log(`[CONSOLE_ERR] ${msg.text()}`)
    }
  })

  // Intercept API errors
  await page.route('**/api/v1/**', route => {
    route.continue()
  })
  page.on('response', resp => {
    const url = resp.url()
    if (url.includes('/api/v1/') && (resp.status() >= 400)) {
      apiErrors.push({ url, status: resp.status(), method: resp.request().method() })
      console.log(`[API_ERROR] ${resp.status()} ${resp.request().method()} ${url}`)
    }
  })

  // Register and complete profile
  console.log('=== STEP 1: Register ===')
  await page.goto('/register', { waitUntil: 'networkidle' })
  await page.fill('input[id="register-email"]', EMAIL)
  await page.fill('input[id="register-password"]', PASSWORD)
  await page.fill('input[id="register-confirm"]', PASSWORD)
  await page.click('button[type="submit"]')
  await page.waitForURL('**/dashboard**', { timeout: 30000 })
  console.log('Registered, on dashboard')

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
  console.log('Profile saved')

  // === FOOD DIARY ===
  console.log('\n=== STEP 2: Food Diary ===')
  await page.goto('/nutrition/logs', { waitUntil: 'networkidle', timeout: 30000 })
  await page.waitForTimeout(3000)

  let retryBtn = page.locator('button:has-text("Retry")')
  let hasRetry = await retryBtn.isVisible().catch(() => false)
  console.log(`Food Diary Retry visible: ${hasRetry}`)

  if (hasRetry) {
    // Capture error details before clicking Retry
    const errorText = await page.locator('[role="alert"], .error-state, .text-red-500, .text-destructive').first().textContent().catch(() => 'unknown')
    console.log(`Food Diary error: ${errorText}`)

    // Screenshot the Retry state
    await page.screenshot({ path: '../test-results/food-diary-retry.png', fullPage: true })
    console.log('Captured: food-diary-retry.png')

    // Now click Retry and see what happens
    await retryBtn.click()
    await page.waitForTimeout(3000)
    retryBtn = page.locator('button:has-text("Retry")')
    hasRetry = await retryBtn.isVisible().catch(() => false)
    console.log(`After Retry click - Retry still visible: ${hasRetry}`)
  }

  const foodEmpty = page.locator('text=No entries logged')
  const foodVisible = await foodEmpty.isVisible().catch(() => false)
  console.log(`Food Diary empty state visible: ${foodVisible}`)

  await page.screenshot({ path: '../test-results/food-diary-initial.png', fullPage: true })
  console.log('Captured: food-diary-initial.png')

  // Add food entry
  console.log('\n--- Adding food entry ---')
  await page.fill('input[id*="food-name"], input[placeholder*="food"], input[name="food_name"]', 'Test Meal')
  // Fill in calories
  const calInput = page.locator('input[id*="calories"], input[placeholder*="calories"], input[name*="calories"]').first()
  if (await calInput.isVisible().catch(() => false)) {
    await calInput.fill('500')
  }
  // Click submit
  const submitBtn = page.locator('button[type="submit"]').first()
  if (await submitBtn.isVisible().catch(() => false)) {
    await submitBtn.click()
    await page.waitForTimeout(2000)
  }
  await page.screenshot({ path: '../test-results/food-diary-populated.png', fullPage: true })
  console.log('Captured: food-diary-populated.png')

  // === TASKS ===
  console.log('\n=== STEP 3: Tasks ===')
  await page.goto('/tasks', { waitUntil: 'networkidle', timeout: 30000 })
  await page.waitForTimeout(3000)

  retryBtn = page.locator('button:has-text("Retry")')
  hasRetry = await retryBtn.isVisible().catch(() => false)
  console.log(`Tasks Retry visible: ${hasRetry}`)

  if (hasRetry) {
    const errorText = await page.locator('[role="alert"], .error-state, .text-red-500, .text-destructive').first().textContent().catch(() => 'unknown')
    console.log(`Tasks error: ${errorText}`)
    await page.screenshot({ path: '../test-results/tasks-retry.png', fullPage: true })
    await retryBtn.click()
    await page.waitForTimeout(3000)
    retryBtn = page.locator('button:has-text("Retry")')
    hasRetry = await retryBtn.isVisible().catch(() => false)
    console.log(`After Retry click - Retry still visible: ${hasRetry}`)
  }

  const tasksEmpty = page.locator('text=No tasks yet')
  const tasksVisible = await tasksEmpty.isVisible().catch(() => false)
  console.log(`Tasks empty state visible: ${tasksVisible}`)

  await page.screenshot({ path: '../test-results/tasks-initial.png', fullPage: true })

  // Create task
  console.log('\n--- Creating task ---')
  const createBtn = page.locator('button:has-text("Create"), button:has-text("New Task"), button:has-text("Add Task")').first()
  if (await createBtn.isVisible().catch(() => false)) {
    await createBtn.click()
    await page.waitForTimeout(1000)
  }
  const taskInput = page.locator('input[id*="title"], input[placeholder*="task"], input[name="title"]').first()
  if (await taskInput.isVisible().catch(() => false)) {
    await taskInput.fill('Test task')
    const taskSubmit = page.locator('button[type="submit"]').first()
    if (await taskSubmit.isVisible().catch(() => false)) {
      await taskSubmit.click()
      await page.waitForTimeout(2000)
    }
  }
  await page.screenshot({ path: '../test-results/tasks-populated.png', fullPage: true })

  // === BODY WEIGHT ===
  console.log('\n=== STEP 4: Body Weight ===')
  await page.goto('/body-weight', { waitUntil: 'networkidle', timeout: 30000 })
  await page.waitForTimeout(3000)

  retryBtn = page.locator('button:has-text("Retry")')
  hasRetry = await retryBtn.isVisible().catch(() => false)
  console.log(`Body Weight Retry visible: ${hasRetry}`)

  if (hasRetry) {
    const errorText = await page.locator('[role="alert"], .error-state, .text-red-500, .text-destructive').first().textContent().catch(() => 'unknown')
    console.log(`Body Weight error: ${errorText}`)
    await page.screenshot({ path: '../test-results/weight-retry.png', fullPage: true })
    await retryBtn.click()
    await page.waitForTimeout(3000)
  }

  const weightEmpty = page.locator('text=No weight entries yet')
  const weightVisible = await weightEmpty.isVisible().catch(() => false)
  console.log(`Body Weight empty state visible: ${weightVisible}`)

  await page.screenshot({ path: '../test-results/weight-initial.png', fullPage: true })

  // === SUMMARY ===
  console.log('\n=== SUMMARY ===')
  console.log(`Page errors: ${errors.length}`)
  console.log(`API errors:`)
  for (const ae of apiErrors) {
    console.log(`  ${ae.status} ${ae.method} ${ae.url}`)
  }

  // Wait for manual inspection
  console.log('\n=== BROWSER OPEN FOR MANUAL INSPECTION (30s) ===')
  await page.waitForTimeout(30000)
})
