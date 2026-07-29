import { test, expect } from '@playwright/test'
import path from 'path'

test('CSV Import breaks Tasks/Goals - reproduce sequence', async ({ page }) => {
  test.setTimeout(300000)
  
  // Capture all API responses
  const apiCalls: { method: string; path: string; status: number; body?: string }[] = []
  page.on('response', async resp => {
    const u = resp.url()
    if (u.includes('/api/v1/')) {
      const entry = { method: resp.request().method(), path: u.replace('http://localhost:8000/api/v1', ''), status: resp.status() }
      try { entry.body = await resp.text() } catch(e) {}
      apiCalls.push(entry)
      console.log(`[${entry.status}] ${entry.method} ${entry.path}`)
      if (entry.body) console.log(`  BODY: ${entry.body.slice(0,500)}`)
    }
  })
  page.on('requestfailed', req => {
    const u = req.url()
    if (u.includes('/api/v1/')) {
      console.log(`[FAIL] ${req.method()} ${u.replace('http://localhost:8000/api/v1', '')} ${req.failure()?.errorText}`)
    }
  })
  page.on('console', msg => {
    const t = msg.text()
    if (t.includes('Failed') || t.includes('Error') || t.includes('Abort') || t.includes('token') || t.includes('auth')) {
      console.log(`[CONSOLE] ${t}`)
    }
  })

  const uid = Date.now()
  
  // 1. REGISTER NEW USER
  console.log('\n=== REGISTER ===')
  await page.goto('/register', { waitUntil: 'networkidle' })
  await page.fill('input[id="register-email"]', `qa_${uid}@example.com`)
  await page.fill('input[id="register-password"]', 'TestPass123!')
  await page.fill('input[id="register-confirm"]', 'TestPass123!')
  await page.click('button[type="submit"]')
  await page.waitForURL('**/dashboard**', { timeout: 30000 })
  console.log('Registered and logged in')

  // 2. PROFILE SETUP (required for some features)
  console.log('\n=== PROFILE SETUP ===')
  await page.goto('/settings?tab=profile', { waitUntil: 'networkidle' })
  await page.waitForTimeout(1000)
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

  // 3. CHECK TASKS BEFORE IMPORT
  console.log('\n=== TASKS BEFORE IMPORT ===')
  await page.goto('/tasks', { waitUntil: 'networkidle', timeout: 30000 })
  await page.waitForTimeout(3000)
  await page.screenshot({ path: path.join(process.cwd(), 'tasks-before-import.png'), fullPage: true })
  const tasksLoadErr = await page.getByText(/failed to load tasks/i).isVisible()
  const tasksRetry = await page.getByRole('button', { name: /retry/i }).isVisible()
  const tasksEmpty = await page.getByText(/no tasks yet/i).isVisible()
  console.log(`Tasks load: error=${tasksLoadErr} retry=${tasksRetry} empty=${tasksEmpty}`)
  expect(tasksLoadErr).toBe(false)
  expect(tasksRetry).toBe(false)

  // 3. CHECK GOALS BEFORE IMPORT
  console.log('\n=== GOALS BEFORE IMPORT ===')
  await page.goto('/goals', { waitUntil: 'networkidle', timeout: 30000 })
  await page.waitForTimeout(3000)
  await page.screenshot({ path: path.join(process.cwd(), 'goals-before-import.png'), fullPage: true })
  const goalsLoadErr = await page.getByText(/failed to load goals/i).isVisible()
  const goalsRetry = await page.getByRole('button', { name: /retry/i }).isVisible()
  const goalsEmpty = await page.getByText(/no goals yet/i).isVisible()
  console.log(`Goals load: error=${goalsLoadErr} retry=${goalsRetry} empty=${goalsEmpty}`)
  expect(goalsLoadErr).toBe(false)
  expect(goalsRetry).toBe(false)

  // 4. GO TO SETTINGS -> DATA CENTER -> IMPORT CSV
  console.log('\n=== IMPORT CSV ===')
  await page.goto('/settings?tab=data-center', { waitUntil: 'networkidle' })
  await page.waitForTimeout(2000)
  
  const fileInput = page.locator('input[type="file"]')
  await fileInput.setInputFiles(path.join(process.cwd(), 'test-import.csv'))
  await page.waitForTimeout(5000) // wait for import
  
  await page.screenshot({ path: path.join(process.cwd(), 'import-csv-result.png'), fullPage: true })
  
  // Check for toast messages
  const toastSuccess = await page.getByText(/imported/i).isVisible()
  const toastError = await page.getByText(/error/i).isVisible()
  console.log(`Import: success=${toastSuccess} error=${toastError}`)

  // 5. CHECK BACKEND HEALTH
  console.log('\n=== BACKEND HEALTH AFTER IMPORT ===')
  const healthResp = await page.request.get('http://localhost:8000/api/v1/health')
  console.log(`Health: ${healthResp.status()} - ${await healthResp.text()}`)

  // 6. CHECK TASKS AFTER IMPORT
  console.log('\n=== TASKS AFTER IMPORT ===')
  await page.goto('/tasks', { waitUntil: 'networkidle', timeout: 30000 })
  await page.waitForTimeout(3000)
  await page.screenshot({ path: path.join(process.cwd(), 'tasks-after-import.png'), fullPage: true })
  const tasksLoadErr2 = await page.getByText(/failed to load tasks/i).isVisible()
  const tasksRetry2 = await page.getByRole('button', { name: /retry/i }).isVisible()
  const tasksEmpty2 = await page.getByText(/no tasks yet/i).isVisible()
  console.log(`Tasks after import: error=${tasksLoadErr2} retry=${tasksRetry2} empty=${tasksEmpty2}`)

  // 7. CHECK GOALS AFTER IMPORT
  console.log('\n=== GOALS AFTER IMPORT ===')
  await page.goto('/goals', { waitUntil: 'networkidle', timeout: 30000 })
  await page.waitForTimeout(3000)
  await page.screenshot({ path: path.join(process.cwd(), 'goals-after-import.png'), fullPage: true })
  const goalsLoadErr2 = await page.getByText(/failed to load goals/i).isVisible()
  const goalsRetry2 = await page.getByRole('button', { name: /retry/i }).isVisible()
  const goalsEmpty2 = await page.getByText(/no goals yet/i).isVisible()
  console.log(`Goals after import: error=${goalsLoadErr2} retry=${goalsRetry2} empty=${goalsEmpty2}`)

  // 8. HARD REFRESH BOTH
  console.log('\n=== HARD REFRESH ===')
  await page.reload({ waitUntil: 'networkidle' })
  await page.waitForTimeout(3000)
  const tasksAfterRefresh = await page.getByText(/failed to load tasks/i).isVisible()
  const tasksRetryAfter = await page.getByRole('button', { name: /retry/i }).isVisible()
  console.log(`Tasks after refresh: error=${tasksAfterRefresh} retry=${tasksRetryAfter}`)

  await page.goto('/goals', { waitUntil: 'networkidle' })
  await page.waitForTimeout(3000)
  const goalsAfterRefresh = await page.getByText(/failed to load goals/i).isVisible()
  const goalsRetryAfter = await page.getByRole('button', { name: /retry/i }).isVisible()
  console.log(`Goals after refresh: error=${goalsAfterRefresh} retry=${goalsRetryAfter}`)

  // 9. TRY RETRY BUTTON IF PRESENT
  if (await tasksRetry2) {
    console.log('\n=== CLICK RETRY ON TASKS ===')
    await page.getByRole('button', { name: /retry/i }).click()
    await page.waitForTimeout(3000)
    const tasksAfterRetry = await page.getByText(/failed to load tasks/i).isVisible()
    const tasksRetryAfterRetry = await page.getByRole('button', { name: /retry/i }).isVisible()
    console.log(`Tasks after retry: error=${tasksAfterRetry} retry=${tasksAfterRetry}`)
  }

  if (await goalsRetry2) {
    console.log('\n=== CLICK RETRY ON GOALS ===')
    await page.getByRole('button', { name: /retry/i }).click()
    await page.waitForTimeout(3000)
    const goalsAfterRetry = await page.getByText(/failed to load goals/i).isVisible()
    const goalsRetryAfterRetry = await page.getByRole('button', { name: /retry/i }).isVisible()
    console.log(`Goals after retry: error=${goalsAfterRetry} retry=${goalsRetryAfterRetry}`)
  }

  // 10. TRY TASKS CRUD AFTER IMPORT
  console.log('\n=== TASK CRUD AFTER IMPORT ===')
  await page.goto('/tasks', { waitUntil: 'networkidle' })
  await page.waitForTimeout(2000)
  
  const addTaskBtn = page.getByRole('button', { name: /add task/i })
  if (await addTaskBtn.isVisible()) {
    await addTaskBtn.click()
    await page.waitForTimeout(1000)
    await page.fill('input[id="task-title"]', 'QA Task Post-Import')
    await page.fill('input[id="task-description"]', 'Created after CSV import')
    await page.locator('button[type="submit"]').click()
    await page.waitForTimeout(3000)
    const taskCreated = await page.getByText('QA Task Post-Import').isVisible()
    console.log(`Task create after import: ${taskCreated}`)
  }

  // 11. TRY GOALS CRUD AFTER IMPORT
  console.log('\n=== GOAL CRUD AFTER IMPORT ===')
  await page.goto('/goals', { waitUntil: 'networkidle' })
  await page.waitForTimeout(2000)
  
  const addGoalBtn = page.getByRole('button', { name: /add goal/i })
  if (await addGoalBtn.isVisible()) {
    await addGoalBtn.click()
    await page.waitForTimeout(1000)
    await page.fill('input[id="title"]', 'QA Goal Post-Import')
    await page.locator('button:has-text("Create Goal")').click()
    await page.waitForTimeout(3000)
    const goalCreated = await page.getByText('QA Goal Post-Import').isVisible()
    console.log(`Goal create after import: ${goalCreated}`)
  }

  console.log('\n=== API CALLS SUMMARY ===')
  apiCalls.forEach(c => console.log(`[${c.status}] ${c.method} ${c.path}`))
  
  console.log('\n=== DONE ===')
})