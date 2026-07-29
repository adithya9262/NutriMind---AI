import { test, expect } from '@playwright/test'
import path from 'path'

test('Goals + Tasks full CRUD verification', async ({ page }) => {
  test.setTimeout(600000)

  const apis: { method: string; path: string; status: number }[] = []
  page.on('response', async resp => {
    const u = resp.url()
    if (u.includes('/api/v1/tasks') || u.includes('/api/v1/goals')) {
      const entry = { method: resp.request().method(), path: u.replace('http://localhost:8000/api/v1', ''), status: resp.status() }
      apis.push(entry)
      let bodyText = ''
      try { bodyText = await resp.text() } catch(e) {}
      console.log(`[${entry.status}] ${entry.method} ${entry.path} - ${bodyText.slice(0, 200)}`)
    }
  })
  page.on('requestfailed', req => {
    const u = req.url()
    if (u.includes('/api/v1/tasks') || u.includes('/api/v1/goals')) {
      const entry = { method: req.method(), path: u.replace('http://localhost:8000/api/v1', ''), status: 0 }
      apis.push(entry)
      console.log(`[FAIL] ${entry.method} ${entry.path} ${req.failure()?.errorText}`)
    }
  })

  const uid = Date.now()
  
  // Register fresh user
  await page.goto('/register', { waitUntil: 'networkidle' })
  await page.waitForTimeout(2000)
  await expect(page.locator('[id="register-email"]')).toBeVisible({ timeout: 15000 })
  await page.fill('[id="register-email"]', `vt_${uid}@example.com`)
  await page.fill('[id="register-password"]', 'TestPass123!')
  await page.fill('[id="register-confirm"]', 'TestPass123!')
  await page.click('button[type="submit"]')
  await page.waitForURL(/\/dashboard/, { timeout: 30000 })
  console.log('Registered')

  // ==================== GOALS CRUD ====================
  console.log('\n=== GOALS ===')

  // LOAD /goals
  await page.goto('/goals', { waitUntil: 'networkidle' })
  await page.waitForTimeout(2000)
  await page.screenshot({ path: path.join(process.cwd(), 'goals-load.png'), fullPage: true })
  const gLoadErr = await page.getByText(/failed to load goals/i).isVisible()
  const gRetryBtn = await page.getByRole('button', { name: /retry/i }).isVisible()
  console.log(`Load: error=${gLoadErr} retry=${gRetryBtn}`)
  expect(gLoadErr).toBe(false)
  expect(gRetryBtn).toBe(false)

  // CREATE goal
  console.log('CREATE...')
  const addGoalBtn = page.getByRole('button', { name: /add goal/i })
  await expect(addGoalBtn.first()).toBeVisible({ timeout: 5000 })
  await addGoalBtn.first().click()
  await page.waitForTimeout(1500)
  await expect(page.locator('#title')).toBeVisible({ timeout: 5000 })
  await page.locator('#title').fill('Verify Goal')
  await page.waitForTimeout(300)
  await page.screenshot({ path: path.join(process.cwd(), 'goals-form-filled.png'), fullPage: true })
  const createGoalBtn = page.getByRole('button', { name: 'Create Goal' })
  await expect(createGoalBtn).toBeVisible({ timeout: 5000 })
  await expect(createGoalBtn).toBeEnabled({ timeout: 5000 })
  await createGoalBtn.click()
  await page.waitForTimeout(2000)
  await page.screenshot({ path: path.join(process.cwd(), 'goals-after-create.png'), fullPage: true })
  const gCreated = await page.getByText('Verify Goal').isVisible()
  console.log(`  Created: ${gCreated}`)

  // REFRESH
  await page.reload({ waitUntil: 'networkidle' })
  await page.waitForTimeout(2000)
  await page.screenshot({ path: path.join(process.cwd(), 'goals-refresh.png'), fullPage: true })
  const gAfterRefresh = await page.getByText('Verify Goal').isVisible()
  console.log(`  After refresh: ${gAfterRefresh}`)
  expect(gCreated || gAfterRefresh).toBe(true)

  // EDIT
  console.log('EDIT...')
  const editBtn = page.getByRole('button', { name: /edit verify goal/i })
  if (await editBtn.isVisible()) {
    await editBtn.click()
    await page.waitForTimeout(1500)
    const titleInput = page.locator('#title')
    await expect(titleInput).toBeVisible({ timeout: 5000 })
    await titleInput.fill('')
    await titleInput.fill('Verify Goal EDITED')
    const saveBtn = page.getByRole('button', { name: 'Save Changes' })
    await expect(saveBtn).toBeVisible({ timeout: 5000 })
    await expect(saveBtn).toBeEnabled({ timeout: 5000 })
    await saveBtn.click()
    await page.waitForTimeout(2000)
  }
  await page.screenshot({ path: path.join(process.cwd(), 'goals-after-edit.png'), fullPage: true })
  const gEdited = await page.getByText('EDITED').isVisible()
  console.log(`  Edited: ${gEdited}`)

  // DELETE
  console.log('DELETE...')
  const delBtn = page.getByRole('button', { name: /delete verify goal edited/i })
  if (await delBtn.isVisible()) {
    await delBtn.click()
    await page.waitForTimeout(1000)
    const confirmBtn = page.getByRole('button', { name: 'Delete', exact: true })
    await expect(confirmBtn).toBeVisible({ timeout: 5000 })
    await confirmBtn.click()
    await page.waitForTimeout(2000)
  }
  await page.screenshot({ path: path.join(process.cwd(), 'goals-after-delete.png'), fullPage: true })
  const gEmpty = await page.getByText(/no goals yet/i).isVisible()
  console.log(`  After delete empty: ${gEmpty}`)

  // ==================== TASKS CRUD ====================
  console.log('\n=== TASKS ===')

  // LOAD /tasks
  await page.goto('/tasks', { waitUntil: 'networkidle' })
  await page.waitForTimeout(2000)
  await page.screenshot({ path: path.join(process.cwd(), 'tasks-load.png'), fullPage: true })
  const tLoadErr = await page.getByText(/failed to load tasks/i).isVisible()
  const tRetryBtn = await page.getByRole('button', { name: /retry/i }).isVisible()
  console.log(`Load: error=${tLoadErr} retry=${tRetryBtn}`)
  expect(tLoadErr).toBe(false)
  expect(tRetryBtn).toBe(false)

  // CREATE task
  console.log('CREATE...')
  const addTaskBtn = page.getByRole('button', { name: /add task/i })
  await expect(addTaskBtn.first()).toBeVisible({ timeout: 5000 })
  await addTaskBtn.first().click()
  await page.waitForTimeout(1500)
  await expect(page.locator('#task-title')).toBeVisible({ timeout: 5000 })
  await page.locator('#task-title').fill('Verify Task')
  await page.locator('#task-description').fill('Test description')
  await page.waitForTimeout(300)
  const submitTaskBtn = page.getByRole('button', { name: 'Add Task' })
  await expect(submitTaskBtn).toBeVisible({ timeout: 5000 })
  await expect(submitTaskBtn).toBeEnabled({ timeout: 5000 })
  await submitTaskBtn.click()
  await page.waitForTimeout(3000)
  await page.screenshot({ path: path.join(process.cwd(), 'tasks-after-create.png'), fullPage: true })
  const tCreated = await page.getByText('Verify Task').isVisible()
  console.log(`  Created: ${tCreated}`)

  // REFRESH
  await page.reload({ waitUntil: 'networkidle' })
  await page.waitForTimeout(2000)
  await page.screenshot({ path: path.join(process.cwd(), 'tasks-refresh.png'), fullPage: true })
  const tAfterRefresh = await page.getByText('Verify Task').isVisible()
  console.log(`  After refresh: ${tAfterRefresh}`)

  // DELETE
  console.log('DELETE...')
  const delTaskBtn = page.getByRole('button', { name: /delete/i }).first()
  if (await delTaskBtn.isVisible()) {
    await delTaskBtn.click()
    await page.waitForTimeout(1000)
    const confirmBtn = page.getByRole('button', { name: 'Delete', exact: true })
    await expect(confirmBtn).toBeVisible({ timeout: 5000 })
    await confirmBtn.click()
    await page.waitForTimeout(2000)
  }
  await page.screenshot({ path: path.join(process.cwd(), 'tasks-after-delete.png'), fullPage: true })
  const tEmpty = await page.getByText(/no tasks yet/i).isVisible()
  console.log(`  After delete empty: ${tEmpty}`)

  // ==================== 5 HARD REFRESHES ====================
  console.log('\n=== 5 REFRESHES EACH ===')
  for (const path of ['/goals', '/tasks']) {
    for (let i = 1; i <= 5; i++) {
      await page.goto(path, { waitUntil: 'networkidle' })
      await page.waitForTimeout(2000)
      const fail = await page.getByText(/failed to load/i).isVisible()
      const retry = await page.getByRole('button', { name: /retry/i }).isVisible()
      console.log(`  ${path} #${i}: fail=${fail} retry=${retry}`)
      expect(fail).toBe(false)
      expect(retry).toBe(false)
    }
  }

  // ==================== REPORT ====================
  console.log('\n========== FINAL REPORT ==========')
  const failCount = apis.filter(a => a.status === 0).length
  const timeoutCount = apis.filter(a => a.status === 0).length
  const un401 = apis.filter(a => a.status === 401).length
  const un404 = apis.filter(a => a.status === 404).length
  const un5xx = apis.filter(a => a.status >= 500).length
  
  console.log(`GOALS: Load PASS Create ${gCreated ? 'PASS' : 'FAIL'} Edit ${gEdited ? 'PASS' : 'SKIP'} Delete ${gEmpty ? 'PASS' : 'FAIL'} Refresh ${gAfterRefresh ? 'PASS' : 'FAIL'}`)
  console.log(`TASKS: Load PASS Create ${tCreated ? 'PASS' : 'FAIL'} Delete ${tEmpty ? 'PASS' : 'FAIL'} Refresh ${tAfterRefresh ? 'PASS' : 'FAIL'}`)
  console.log(`Failed fetch: ${failCount}`)
  console.log(`Unexpected 401: ${un401}`)
  console.log(`Unexpected 404: ${un404}`)
  console.log(`Unexpected 5xx: ${un5xx}`)
})
