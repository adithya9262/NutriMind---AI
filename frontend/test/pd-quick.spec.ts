import { test, expect } from '@playwright/test'
import path from 'path'
import fs from 'fs'

const EMAIL = `qa_pd_quick_${Date.now()}@example.com`
const PASSWORD = 'TestPass123!'
const UID = Date.now()

test('Quick PD regression', async ({ page }) => {
  test.setTimeout(300000)

  // === REGISTER ===
  console.log('=== REGISTER ===')
  await page.goto('/register', { waitUntil: 'networkidle', timeout: 30000 })
  await page.waitForTimeout(500)
  await page.fill('input[id="register-email"]', EMAIL)
  await page.fill('input[id="register-password"]', PASSWORD)
  await page.fill('input[id="register-confirm"]', PASSWORD)
  await page.click('button[type="submit"]')
  await page.waitForURL('**/dashboard**', { timeout: 30000 })
  console.log('Registered')

  // === LANDING ===
  console.log('=== LANDING ===')
  await page.goto('/', { waitUntil: 'networkidle', timeout: 30000 })
  await page.waitForTimeout(500)
  const landingOk = await page.getByText('NutriMind').first().isVisible()
  console.log(`Landing loads: ${landingOk}`)
  const bodyText = await page.textContent('body')
  expect(bodyText).toContain('NutriMind')

  // === DASHBOARD ===
  console.log('=== DASHBOARD ===')
  await page.goto('/dashboard', { waitUntil: 'networkidle', timeout: 30000 })
  await page.waitForTimeout(2000)
  const permSkeleton = await page.locator('[class*="animate-pulse"], [class*="skeleton"]').first().isVisible().catch(() => false)
  const permRetry = await page.getByText(/retry/i).first().isVisible().catch(() => false)
  console.log(`Perm skeleton: ${permSkeleton}, Perm retry: ${permRetry}`)
  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight))
  await page.waitForTimeout(500)
  await page.evaluate(() => window.scrollTo(0, 0))
  console.log('Dashboard scrolled')

  // === GOALS CRUD (Create / Edit / Refresh / Delete) ===
  console.log('=== GOALS ===')
  await page.goto('/goals', { waitUntil: 'networkidle', timeout: 30000 })
  await page.waitForTimeout(1500)
  expect(await page.getByText(/failed to load goals/i).isVisible()).toBe(false)
  console.log('Goals loads OK')

  const goalTitle = `QA_GOAL_${UID}`
  const editedTitle = `QA_GOAL_EDITED_${UID}`

  // --- CREATE ---
  const addBtn = page.getByRole('button', { name: /add goal/i })
  await expect(addBtn.first()).toBeVisible({ timeout: 5000 })
  await addBtn.first().click()
  await page.waitForTimeout(500)
  const titleInput = page.locator('input[id="title"]')
  await expect(titleInput).toBeVisible({ timeout: 5000 })
  await titleInput.fill(goalTitle)
  await page.getByRole('button', { name: 'Create Goal' }).click()
  await page.waitForTimeout(2000)
  const goalVisible = await page.getByText(goalTitle).isVisible()
  console.log(`Create: ${goalVisible}`)
  expect(goalVisible).toBe(true)

  // --- EDIT ---
  const editBtn = page.getByRole('button', { name: new RegExp(`edit ${goalTitle}`, 'i') })
  await expect(editBtn.first()).toBeVisible({ timeout: 5000 })
  await editBtn.first().click()
  await page.waitForTimeout(500)
  await expect(titleInput).toBeVisible({ timeout: 5000 })
  await titleInput.fill(editedTitle)
  await page.getByRole('button', { name: 'Save Changes' }).click()
  await page.waitForTimeout(2000)
  const editedVisible = await page.getByText(editedTitle).isVisible()
  console.log(`Edit: ${editedVisible}`)
  expect(editedVisible).toBe(true)

  // --- HARD REFRESH PERSISTENCE ---
  await page.reload({ waitUntil: 'networkidle' })
  await page.waitForTimeout(2000)
  const persisted = await page.getByText(editedTitle).isVisible()
  console.log(`Refresh persistence: ${persisted}`)
  expect(persisted).toBe(true)

  // --- DELETE ---
  const deleteBtn = page.getByRole('button', { name: new RegExp(`delete ${editedTitle}`, 'i') })
  await expect(deleteBtn.first()).toBeVisible({ timeout: 5000 })
  await deleteBtn.first().click()
  await page.waitForTimeout(500)
  // Confirm delete dialog
  const confirmDelete = page.getByRole('button', { name: 'Delete' })
  await expect(confirmDelete).toBeVisible({ timeout: 5000 })
  await confirmDelete.click()
  await page.waitForTimeout(2000)
  const deleted = await page.getByText(editedTitle).isVisible()
  console.log(`Delete: ${!deleted}`)
  expect(deleted).toBe(false)

  // === TASKS CRUD ===
  console.log('=== TASKS ===')
  await page.goto('/tasks', { waitUntil: 'networkidle', timeout: 30000 })
  await page.waitForTimeout(1500)
  expect(await page.getByText(/failed to load tasks/i).isVisible()).toBe(false)
  console.log('Tasks loads OK')

  const taskTitle = `QA_TASK_${UID}`
  const tAddBtn = page.getByRole('button', { name: /add task/i })
  if (await tAddBtn.isVisible()) {
    await tAddBtn.click()
    await page.waitForTimeout(500)
    const tInp = page.locator('input[id="task-title"]')
    if (await tInp.isVisible()) {
      await tInp.fill(taskTitle)
      await page.locator('button[type="submit"]').click()
      await page.waitForTimeout(2000)
      const created = await page.getByText(taskTitle).isVisible()
      console.log(`Task created: ${created}`)
    }
  }

  await page.goto('/tasks', { waitUntil: 'networkidle', timeout: 30000 })
  await page.waitForTimeout(1000)
  const zeroErr = await page.getByText(/failed to load tasks/i).isVisible()
  console.log(`Zero state (no error): ${!zeroErr}`)

  // === FOOD DIARY ===
  console.log('=== FOOD DIARY ===')
  await page.goto('/nutrition', { waitUntil: 'networkidle', timeout: 30000 })
  await page.waitForTimeout(1500)
  const fdOk = !(await page.getByText(/failed to load/i).isVisible().catch(() => true))
  console.log(`Food diary loads: ${fdOk}`)

  // === WEIGHT ===
  console.log('=== WEIGHT ===')
  await page.goto('/body-weight', { waitUntil: 'networkidle', timeout: 30000 })
  await page.waitForTimeout(1500)
  const wtOk = !(await page.getByText(/failed to load/i).isVisible().catch(() => true))
  console.log(`Weight tracker loads: ${wtOk}`)

  const wtAdd = page.getByRole('button', { name: /add weight|log weight/i })
  if (await wtAdd.isVisible()) {
    await wtAdd.click()
    await page.waitForTimeout(500)
    const wtInput = page.locator('input[id="weight"]')
    if (await wtInput.isVisible()) {
      await wtInput.fill('75.5')
      await page.locator('button[type="submit"]').click()
      await page.waitForTimeout(2000)
      console.log('Weight entry created')
    }
  }

  // === SETTINGS ===
  console.log('=== SETTINGS ===')
  await page.goto('/settings', { waitUntil: 'networkidle', timeout: 30000 })
  await page.waitForTimeout(1500)
  const stOk = !(await page.getByText(/failed to load/i).isVisible().catch(() => true))
  console.log(`Settings loads: ${stOk}`)

  // === IMPORT THROUGH UI ===
  console.log('=== IMPORT ===')
  await page.goto('/settings?tab=data-center', { waitUntil: 'networkidle', timeout: 30000 })
  await page.waitForTimeout(1500)

  const csvPath = path.join(process.cwd(), `test-pd-${UID}.csv`)
  fs.writeFileSync(csvPath, 'Task,pending,UI_IMPORT_test\nTask,completed,UI_IMPORT_completed\nBodyWeight,2024-07-01,76.0 kg\n', 'utf-8')

  const fileInput = page.locator('input[type="file"]')
  await fileInput.setInputFiles(csvPath)
  await page.waitForTimeout(4000)

  const impOk = await page.getByText(/imported|success/i).isVisible()
  console.log(`Import success toast: ${impOk}`)
  try { fs.unlinkSync(csvPath) } catch {}

  // === POST-IMPORT ===
  console.log('=== POST-IMPORT ===')

  const healthResp = await page.request.get('http://localhost:8000/api/v1/health')
  console.log(`Health after import: ${healthResp.status()}`)

  await page.goto('/tasks', { waitUntil: 'networkidle', timeout: 30000 })
  await page.waitForTimeout(2000)
  const tAfter = await page.getByText(/failed to load tasks/i).isVisible()
  console.log(`Tasks post-import error: ${tAfter}`)

  await page.reload({ waitUntil: 'networkidle' })
  await page.waitForTimeout(2000)
  const tRefresh = await page.getByText(/failed to load tasks/i).isVisible()
  console.log(`Tasks hard refresh error: ${tRefresh}`)

  await page.goto('/goals', { waitUntil: 'networkidle', timeout: 30000 })
  await page.waitForTimeout(2000)
  const gAfter = await page.getByText(/failed to load goals/i).isVisible()
  console.log(`Goals post-import error: ${gAfter}`)

  await page.reload({ waitUntil: 'networkidle' })
  await page.waitForTimeout(2000)
  const gRefresh = await page.getByText(/failed to load goals/i).isVisible()
  console.log(`Goals hard refresh error: ${gRefresh}`)

  await page.goto('/body-weight', { waitUntil: 'networkidle', timeout: 30000 })
  await page.waitForTimeout(1500)
  const wtAfter = await page.getByText(/failed to load/i).isVisible()
  console.log(`Weight post-import error: ${wtAfter}`)

  // === RESPONSIVE ===
  console.log('=== RESPONSIVE ===')
  await page.setViewportSize({ width: 1366, height: 768 })
  await page.goto('/dashboard', { waitUntil: 'networkidle', timeout: 30000 })
  await page.waitForTimeout(1000)
  const dHScroll = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)
  console.log(`Desktop h-scroll: ${dHScroll}`)

  await page.setViewportSize({ width: 375, height: 812 })
  for (const route of ['/', '/dashboard', '/tasks']) {
    await page.goto(route, { waitUntil: 'networkidle', timeout: 30000 })
    await page.waitForTimeout(1000)
    const mHScroll = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)
    if (mHScroll) console.log(`  Mobile scroll overflow on ${route}`)
  }
  console.log('Responsive done')

  console.log('\n=== REGRESSION VERIFICATION COMPLETE ===')
})
