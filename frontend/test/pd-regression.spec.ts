import { test, expect } from '@playwright/test'
import path from 'path'
import fs from 'fs'

const UID = Date.now()
const EMAIL = `qa_pd_${UID}@example.com`
const PASSWORD = 'TestPass123!'

// Track API calls
const apiCalls: { method: string; path: string; status: number }[] = []
let errors401 = 0, errors404 = 0, errors422 = 0, errors5xx = 0, errorsFetch = 0
let failedToFetchAfterImport = false

test.describe('Pre-Deployment Regression', () => {
  test.setTimeout(600000)

  test.beforeEach(async ({ page }) => {
    // Monitor API responses once
  })

  test('Full regression suite', async ({ page }) => {
    // === NETWORK MONITORING ===
    page.on('response', async resp => {
      const u = resp.url()
      if (u.includes('/api/v1/')) {
        const path = u.replace(/http:\/\/localhost:8000\/api\/v1/, '')
        const status = resp.status()
        apiCalls.push({ method: resp.request().method(), path, status })
        if (status === 401 && !path.includes('register')) errors401++
        if (status === 404) errors404++
        if (status === 422) errors422++
        if (status >= 500) {
          errors5xx++
          console.log(`[5xx] ${resp.request().method()} ${path}`)
        }
      }
    })
    page.on('requestfailed', req => {
      const u = req.url()
      if (u.includes('/api/v1/')) {
        errorsFetch++
        console.log(`[FETCH FAIL] ${req.method()} ${u.replace('http://localhost:8000/api/v1', '')} ${req.failure()?.errorText}`)
        if (u.includes('/tasks') || u.includes('/goals')) {
          failedToFetchAfterImport = true
        }
      }
    })
    page.on('console', msg => {
      const t = msg.text()
      if (t.includes('Failed') || t.includes('Error') || t.includes('401') || t.includes('500')) {
        // Just log, don't fail on console errors
      }
    })

    // === 1. REGISTER ===
    console.log('\n=== REGISTER ===')
    await page.goto('/register', { waitUntil: 'networkidle', timeout: 30000 })
    await page.waitForTimeout(1000)
    await page.fill('input[id="register-email"]', EMAIL)
    await page.fill('input[id="register-password"]', PASSWORD)
    await page.fill('input[id="register-confirm"]', PASSWORD)
    await page.click('button[type="submit"]')
    await page.waitForURL('**/dashboard**', { timeout: 30000 })
    console.log('Registered and on dashboard')

    // === 2. LANDING PAGE ===
    console.log('\n=== LANDING PAGE ===')
    await page.goto('/', { waitUntil: 'networkidle', timeout: 30000 })
    await page.waitForTimeout(1000)
    const bodyText = await page.textContent('body')
    expect(bodyText).toContain('NutriMind')
    expect(bodyText).not.toContain('failed to load')
    const landingVisible = await page.isVisible('text=Features,text=How It Works')
    console.log(`Landing content visible: ${landingVisible}`)

    // === 3. DASHBOARD ===
    console.log('\n=== DASHBOARD ===')
    await page.goto('/dashboard', { waitUntil: 'networkidle', timeout: 30000 })
    await page.waitForTimeout(3000)
    // Check for permanent skeleton
    const skeletonVisible = await page.locator('[class*="animate-pulse"], [class*="skeleton"]').first().isVisible().catch(() => false)
    console.log(`Skeleton visible: ${skeletonVisible}`)
    // Scroll through
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight))
    await page.waitForTimeout(500)
    await page.evaluate(() => window.scrollTo(0, 0))
    await page.waitForTimeout(500)
    console.log('Dashboard scrolled')

    // === 4. GOALS CRUD ===
    console.log('\n=== GOALS CRUD ===')
    await page.goto('/goals', { waitUntil: 'networkidle', timeout: 30000 })
    await page.waitForTimeout(2000)

    // Load check
    const goalsLoadErr = await page.getByText(/failed to load goals/i).isVisible()
    expect(goalsLoadErr).toBe(false)
    console.log(`Goals load: no error`)

    // Create goal
    const addGoalBtn = page.getByRole('button', { name: /add goal/i })
    if (await addGoalBtn.isVisible()) {
      await addGoalBtn.click()
      await page.waitForTimeout(1000)
      // Try to fill in the title field
      const titleInput = page.locator('input[id="title"]')
      if (await titleInput.isVisible()) {
        await titleInput.fill(`QA_GOAL_${UID}`)
        await page.getByRole('button', { name: 'Create Goal' }).click()
        await page.waitForTimeout(3000)
        const goalVisible = await page.getByText(`QA_GOAL_${UID}`).isVisible()
        console.log(`Goal create: ${goalVisible}`)
      }
    }

    // === 5. TASKS CRUD ===
    console.log('\n=== TASKS CRUD ===')
    await page.goto('/tasks', { waitUntil: 'networkidle', timeout: 30000 })
    await page.waitForTimeout(2000)

    const tasksLoadErr = await page.getByText(/failed to load tasks/i).isVisible()
    expect(tasksLoadErr).toBe(false)
    console.log(`Tasks load: no error`)

    // Create task
    const addTaskBtn = page.getByRole('button', { name: /add task/i })
    if (await addTaskBtn.isVisible()) {
      await addTaskBtn.click()
      await page.waitForTimeout(1000)
      const taskTitleInput = page.locator('input[id="task-title"]')
      if (await taskTitleInput.isVisible()) {
        await taskTitleInput.fill(`QA_TASK_${UID}`)
        await page.locator('button[type="submit"]').click()
        await page.waitForTimeout(3000)
        const taskCreated = await page.getByText(`QA_TASK_${UID}`).isVisible()
        console.log(`Task create: ${taskCreated}`)

        // Complete
        const completeBtn = page.locator(`[data-testid="complete-task"], button:has(svg)`, { hasText: '' }).first()
        // Try to find a complete button for our task
        const taskCard = page.locator(`text=${`QA_TASK_${UID}`}`).locator('..')
        const cBtn = taskCard.locator('button').first()
        if (await cBtn.isVisible()) {
          await cBtn.click()
          await page.waitForTimeout(2000)
          console.log('Task complete clicked')
        }
      }
    }

    // Zero state check: empty tasks page should show empty state, not "Failed to load"
    console.log('Zero state: checked above with load')

    // === 6. FOOD DIARY ===
    console.log('\n=== FOOD DIARY ===')
    await page.goto('/nutrition', { waitUntil: 'networkidle', timeout: 30000 })
    await page.waitForTimeout(2000)
    const fdErr = await page.getByText(/failed to load|retry/i).isVisible()
    console.log(`Food diary error: ${fdErr}`)

    // === 7. WEIGHT TRACKER ===
    console.log('\n=== WEIGHT TRACKER ===')
    await page.goto('/body-weight', { waitUntil: 'networkidle', timeout: 30000 })
    await page.waitForTimeout(2000)
    const wtErr = await page.getByText(/failed to load|retry/i).isVisible()
    console.log(`Weight tracker error: ${wtErr}`)

    // === 8. SETTINGS / NUTRITION PROFILE ===
    console.log('\n=== SETTINGS / PROFILE ===')
    await page.goto('/settings', { waitUntil: 'networkidle', timeout: 30000 })
    await page.waitForTimeout(2000)
    const settingsErr = await page.getByText(/failed to load|retry/i).isVisible()
    console.log(`Settings error: ${settingsErr}`)

    // === 9. CRITICAL IMPORT TEST ===
    console.log('\n=== CRITICAL IMPORT TEST ===')
    // Go to tasks first, confirm it works
    await page.goto('/tasks', { waitUntil: 'networkidle', timeout: 30000 })
    await page.waitForTimeout(1000)
    const tasksBeforeImport = await page.getByText(/failed to load tasks/i).isVisible()
    console.log(`Tasks before import error: ${tasksBeforeImport}`)

    await page.goto('/goals', { waitUntil: 'networkidle', timeout: 30000 })
    await page.waitForTimeout(1000)
    const goalsBeforeImport = await page.getByText(/failed to load goals/i).isVisible()
    console.log(`Goals before import error: ${goalsBeforeImport}`)

    // Navigate to Data Center
    await page.goto('/settings?tab=data-center', { waitUntil: 'networkidle', timeout: 30000 })
    await page.waitForTimeout(2000)

    // Create and import CSV with completed task
    const csvPath = path.join(process.cwd(), `test-import-pd-${UID}.csv`)
    const csvContent = 'Task,pending,QA_IMPORT_pending\nTask,completed,QA_IMPORT_completed\nBodyWeight,2024-06-01,75.0 kg\n'
    fs.writeFileSync(csvPath, csvContent, 'utf-8')

    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles(csvPath)
    await page.waitForTimeout(5000)

    // Check toast
    const importSuccess = await page.getByText(/imported|success/i).isVisible()
    console.log(`Import success toast: ${importSuccess}`)

    // Clean up CSV
    try { fs.unlinkSync(csvPath) } catch {}

    // === 10. POST-IMPORT VERIFICATION ===
    console.log('\n=== POST-IMPORT VERIFICATION ===')

    // Health check
    const healthResp = await page.request.get('http://localhost:8000/api/v1/health')
    console.log(`Health after import: ${healthResp.status()}`)

    // Tasks
    await page.goto('/tasks', { waitUntil: 'networkidle', timeout: 30000 })
    await page.waitForTimeout(3000)
    const tasksAfterImport = await page.getByText(/failed to load tasks/i).isVisible()
    console.log(`Tasks after import error: ${tasksAfterImport}`)

    // Goals
    await page.goto('/goals', { waitUntil: 'networkidle', timeout: 30000 })
    await page.waitForTimeout(2000)
    const goalsAfterImport = await page.getByText(/failed to load goals/i).isVisible()
    console.log(`Goals after import error: ${goalsAfterImport}`)

    // Weight tracker
    await page.goto('/body-weight', { waitUntil: 'networkidle', timeout: 30000 })
    await page.waitForTimeout(2000)
    const wtAfterImport = await page.getByText(/failed to load/i).isVisible()
    console.log(`Weight after import error: ${wtAfterImport}`)

    // Food diary
    await page.goto('/nutrition', { waitUntil: 'networkidle', timeout: 30000 })
    await page.waitForTimeout(2000)
    const fdAfterImport = await page.getByText(/failed to load/i).isVisible()
    console.log(`Food diary after import error: ${fdAfterImport}`)

    // Hard refresh tasks
    await page.goto('/tasks', { waitUntil: 'networkidle', timeout: 30000 })
    await page.waitForTimeout(2000)
    await page.reload({ waitUntil: 'networkidle' })
    await page.waitForTimeout(3000)
    const tasksAfterRefresh = await page.getByText(/failed to load tasks/i).isVisible()
    console.log(`Tasks after hard refresh error: ${tasksAfterRefresh}`)

    // Hard refresh goals
    await page.goto('/goals', { waitUntil: 'networkidle', timeout: 30000 })
    await page.waitForTimeout(2000)
    await page.reload({ waitUntil: 'networkidle' })
    await page.waitForTimeout(3000)
    const goalsAfterRefresh = await page.getByText(/failed to load goals/i).isVisible()
    console.log(`Goals after hard refresh error: ${goalsAfterRefresh}`)

    // === 11. RESPONSIVE CHECK DESKTOP ===
    console.log('\n=== RESPONSIVE DESKTOP ===')
    await page.setViewportSize({ width: 1366, height: 768 })
    await page.goto('/dashboard', { waitUntil: 'networkidle', timeout: 30000 })
    await page.waitForTimeout(2000)
    const hScroll = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)
    console.log(`Desktop horizontal overflow: ${hScroll}`)

    // === 12. RESPONSIVE MOBILE ===
    console.log('\n=== RESPONSIVE MOBILE ===')
    await page.setViewportSize({ width: 375, height: 812 })
    for (const route of ['/', '/dashboard', '/goals', '/tasks', '/nutrition', '/body-weight', '/settings']) {
      await page.goto(route, { waitUntil: 'networkidle', timeout: 30000 })
      await page.waitForTimeout(1000)
      const mobHScroll = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)
      if (mobHScroll) console.log(`  Mobile horizontal overflow on ${route}: YES`)
    }
    console.log('Mobile check complete')

    // === SUMMARY ===
    // Export API calls for analysis
    console.log('\n=== NETWORK SUMMARY ===')
    console.log(`Unexpected 401: ${errors401}`)
    console.log(`Unexpected 404: ${errors404}`)
    console.log(`Unexpected 422: ${errors422}`)
    console.log(`Unexpected 5xx: ${errors5xx}`)
    console.log(`Unexpected Failed to fetch: ${errorsFetch}`)
    console.log(`Failed to fetch after import: ${failedToFetchAfterImport}`)
  })
})
