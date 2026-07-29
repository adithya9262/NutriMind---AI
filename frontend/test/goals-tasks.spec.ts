import { test } from '@playwright/test'

test('Goals + Tasks reproduction', async ({ page }) => {
  test.setTimeout(600000)

  // Log ALL relevant API interactions
  page.on('response', resp => {
    const u = resp.url()
    if (u.includes('/api/v1/tasks') || u.includes('/api/v1/goals')) {
      console.log(`[${resp.status()}] ${resp.request().method()} ${u.replace('http://localhost:8000/api/v1', '')}`)
    }
  })
  page.on('requestfailed', req => {
    const u = req.url()
    if (u.includes('/api/v1/tasks') || u.includes('/api/v1/goals')) {
      console.log(`[FAIL] ${req.method()} ${u.replace('http://localhost:8000/api/v1', '')} ${req.failure()?.errorText}`)
    }
  })
  page.on('console', msg => {
    const t = msg.text()
    if (t.includes('Failed') || t.includes('TIMEOUT') || t.includes('Abort') || t.includes('Error')) {
      console.log(`[CONSOLE] ${t}`)
    }
  })

  const uid = Date.now()
  // Register
  await page.goto('/register', { waitUntil: 'networkidle' })
  await page.fill('input[id="register-email"]', `gt_${uid}@example.com`)
  await page.fill('input[id="register-password"]', 'TestPass123!')
  await page.fill('input[id="register-confirm"]', 'TestPass123!')
  await page.click('button[type="submit"]')
  await page.waitForURL('**/dashboard**', { timeout: 30000 })

  // Profile setup
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

  // ==================== GOALS ====================
  console.log('\n===== GOALS =====')

  // Load /goals
  console.log('--- Load /goals ---')
  await page.goto('/goals', { waitUntil: 'networkidle', timeout: 30000 })
  await page.waitForTimeout(5000)
  const gLoad = await page.getByText(/failed to load goals/i).isVisible()
  const gRetry = await page.getByRole('button', { name: /retry/i }).isVisible()
  const gEmpty = await page.getByText(/no goals yet/i).isVisible()
  console.log(`load: fail=${gLoad} retry=${gRetry} empty=${gEmpty}`)

  // Create goal
  console.log('--- Create goal ---')
  const addGoalBtn = page.getByRole('button', { name: /add goal/i })
  if (await addGoalBtn.isVisible()) {
    await addGoalBtn.click()
    await page.waitForTimeout(1000)
    await page.fill('input[id="title"]', 'Test Goal Alpha')
    await page.locator('button:has-text("Create Goal")').click()
    await page.waitForTimeout(3000)
  }
  const gCreated = await page.getByText('Test Goal Alpha').isVisible()
  console.log('created:', gCreated)

  // Hard refresh
  console.log('--- Refresh ---')
  await page.reload({ waitUntil: 'networkidle' })
  await page.waitForTimeout(5000)
  const gRefreshed = await page.getByText('Test Goal Alpha').isVisible()
  console.log('after refresh:', gRefreshed)

  // Edit goal
  console.log('--- Edit goal ---')
  const editBtn = page.getByRole('button', { name: /edit/i }).first()
  if (await editBtn.isVisible()) {
    await editBtn.click()
    await page.waitForTimeout(1000)
    await page.fill('input[id="title"]', '')
    await page.fill('input[id="title"]', 'Test Goal Alpha EDITED')
    await page.locator('button:has-text("Save Changes")').click()
    await page.waitForTimeout(3000)
  }
  const gEdited = await page.getByText('EDITED').isVisible()
  console.log('edited:', gEdited)

  // Delete goal
  console.log('--- Delete goal ---')
  const delBtn = page.getByRole('button', { name: /delete/i }).first()
  if (await delBtn.isVisible()) {
    await delBtn.click()
    await page.waitForTimeout(1000)
    await page.locator('div[role="dialog"] button:has-text("Delete")').click()
    await page.waitForTimeout(3000)
  }
  const gDeleted = await page.getByText(/no goals yet/i).isVisible()
  console.log('after delete empty:', gDeleted)

  // ==================== TASKS ====================
  console.log('\n===== TASKS =====')

  console.log('--- Load /tasks ---')
  await page.goto('/tasks', { waitUntil: 'networkidle', timeout: 30000 })
  await page.waitForTimeout(5000)
  const tLoad = await page.getByText(/failed to load tasks/i).isVisible()
  const tRetry = await page.getByRole('button', { name: /retry/i }).isVisible()
  const tEmpty = await page.getByText(/no tasks yet/i).isVisible()
  console.log(`load: fail=${tLoad} retry=${tRetry} empty=${tEmpty}`)

  // Create task
  console.log('--- Create task ---')
  const addTaskBtn = page.getByRole('button', { name: /add task/i })
  if (await addTaskBtn.isVisible()) {
    await addTaskBtn.click()
    await page.waitForTimeout(1000)
    await page.fill('input[id="task-title"]', 'Test Task Beta')
    await page.fill('input[id="task-description"]', 'Test description')
    await page.locator('button[type="submit"]').click()
    await page.waitForTimeout(5000)
  }
  const tCreated = await page.getByText('Test Task Beta').isVisible()
  console.log('created:', tCreated)

  // Hard refresh
  console.log('--- Refresh ---')
  await page.reload({ waitUntil: 'networkidle' })
  await page.waitForTimeout(5000)
  const tRefreshed = await page.getByText('Test Task Beta').isVisible()
  console.log('after refresh:', tRefreshed)

  // Delete task
  console.log('--- Delete task ---')
  const delTaskBtn = page.getByRole('button', { name: /delete/i }).first()
  if (await delTaskBtn.isVisible()) {
    await delTaskBtn.click()
    await page.waitForTimeout(1000)
    await page.locator('div[role="dialog"] button:has-text("Delete")').click()
    await page.waitForTimeout(3000)
  }
  const tDeleted = await page.getByText(/no tasks yet/i).isVisible()
  console.log('after delete empty:', tDeleted)

  // ==================== 5 HARD REFRESHES ====================
  console.log('\n===== 5 REFRESHES EACH =====')
  for (const path of ['/goals', '/tasks']) {
    for (let i = 1; i <= 5; i++) {
      await page.goto(path, { waitUntil: 'networkidle', timeout: 30000 })
      await page.waitForTimeout(3000)
      const fail = await page.getByText(/failed to load/i).isVisible()
      const retry = await page.getByRole('button', { name: /retry/i }).isVisible()
      const empty = await page.getByText(/no .* yet/i).isVisible()
      console.log(`${path} refresh ${i}: fail=${fail} retry=${retry} empty=${empty}`)
      if (fail || retry) console.log(`  FAIL on ${path} refresh ${i}`)
    }
  }

  console.log('\n===== DONE =====')
})
