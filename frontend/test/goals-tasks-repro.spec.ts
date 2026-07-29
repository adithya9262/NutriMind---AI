import { test, expect } from '@playwright/test'

test('Goals + Tasks full CRUD', async ({ page }) => {
  test.setTimeout(600000)

  // Log all API interactions
  const apis: string[] = []
  page.on('response', resp => {
    const u = resp.url()
    if (u.includes('/api/v1/tasks') || u.includes('/api/v1/goals')) {
      const msg = `[${resp.status()}] ${resp.request().method()} ${u.replace('http://localhost:8000/api/v1', '')}`
      apis.push(msg)
      console.log(msg)
    }
  })
  page.on('requestfailed', req => {
    const u = req.url()
    if (u.includes('/api/v1/tasks') || u.includes('/api/v1/goals')) {
      const msg = `[FAIL] ${req.method()} ${u.replace('http://localhost:8000/api/v1', '')} ${req.failure()?.errorText}`
      apis.push(msg)
      console.log(msg)
    }
  })

  // Register fresh user
  const uid = Date.now()
  await page.goto('/register', { waitUntil: 'networkidle' })
  await page.waitForTimeout(1000)
  await page.fill('#register-email', `gt_${uid}@example.com`)
  await page.fill('#register-password', 'TestPass123!')
  await page.fill('#register-confirm', 'TestPass123!')
  await page.click('button[type="submit"]')
  await page.waitForURL('**/dashboard**', { timeout: 30000 })
  console.log('Registered + onboarded')

  // ==================== GOALS CRUD ====================
  console.log('\n=== GOALS ===')

  // LOAD
  await page.goto('/goals', { waitUntil: 'networkidle', timeout: 30000 })
  await page.waitForTimeout(3000)
  const gFail = await page.getByText(/failed to load goals/i).isVisible()
  const gRetry = await page.getByRole('button', { name: /retry/i }).isVisible()
  const gEmpty = await page.getByText(/no goals yet/i).isVisible()
  console.log(`Load: fail=${gFail} retry=${gRetry} empty=${gEmpty}`)
  expect(gFail).toBe(false)
  expect(gRetry).toBe(false)

  // CREATE — look for the Add Goal button in multiple ways
  console.log('Creating goal...')
  const addGoalBtn = page.getByRole('button', { name: /add goal/i })
  if (await addGoalBtn.isVisible()) {
    await addGoalBtn.click()
    await page.waitForTimeout(1500)
    // Check form is visible
    const titleInput = page.locator('#title')
    if (await titleInput.isVisible()) {
      await titleInput.fill('Test Goal Alpha')
      await page.waitForTimeout(500)
      // Try clicking the submit button
      await page.locator('button:has-text("Create Goal")').first().click()
      await page.waitForTimeout(3000)
    }
  }
  const gCreated = await page.getByText('Test Goal Alpha').isVisible()
  console.log(`Created: ${gCreated}`)

  // REFRESH
  await page.reload({ waitUntil: 'networkidle' })
  await page.waitForTimeout(3000)
  const gPersist = await page.getByText('Test Goal Alpha').isVisible()
  console.log(`After refresh: ${gPersist}`)
  expect(gPersist).toBe(true)

  // EDIT
  console.log('Editing goal...')
  const editBtn = page.getByRole('button', { name: /edit/i }).first()
  if (await editBtn.isVisible()) {
    await editBtn.click()
    await page.waitForTimeout(1500)
    const titleInput = page.locator('#title')
    if (await titleInput.isVisible()) {
      await titleInput.fill('')
      await titleInput.fill('Test Goal Alpha EDITED')
      await page.locator('button:has-text("Save Changes")').first().click()
      await page.waitForTimeout(3000)
    }
  }
  const gEdited = await page.getByText('EDITED').isVisible()
  console.log(`Edited: ${gEdited}`)
  expect(gEdited).toBe(true)

  // DELETE
  console.log('Deleting goal...')
  const delBtn = page.getByRole('button', { name: /delete/i }).first()
  if (await delBtn.isVisible()) {
    await delBtn.click()
    await page.waitForTimeout(1000)
    // Confirm deletion in dialog
    const confirmBtn = page.locator('div[role="dialog"] button:has-text("Delete")')
    if (await confirmBtn.isVisible()) {
      await confirmBtn.click()
      await page.waitForTimeout(3000)
    }
  }
  const gDeleted = await page.getByText(/no goals yet/i).isVisible()
  console.log(`After delete empty: ${gDeleted}`)
  expect(gDeleted).toBe(true)

  // ==================== TASKS CRUD ====================
  console.log('\n=== TASKS ===')

  // LOAD
  await page.goto('/tasks', { waitUntil: 'networkidle', timeout: 30000 })
  await page.waitForTimeout(3000)
  const tFail = await page.getByText(/failed to load tasks/i).isVisible()
  const tRetry = await page.getByRole('button', { name: /retry/i }).isVisible()
  const tEmpty = await page.getByText(/no tasks yet/i).isVisible()
  console.log(`Load: fail=${tFail} retry=${tRetry} empty=${tEmpty}`)
  expect(tFail).toBe(false)
  expect(tRetry).toBe(false)

  // CREATE
  console.log('Creating task...')
  const addTaskBtn = page.getByRole('button', { name: /add task/i })
  if (await addTaskBtn.isVisible()) {
    await addTaskBtn.click()
    await page.waitForTimeout(1500)
    const titleInput = page.locator('#task-title')
    if (await titleInput.isVisible()) {
      await titleInput.fill('Test Task Beta')
      await page.locator('#task-description').fill('Test description')
      await page.locator('button[type="submit"]').first().click()
      await page.waitForTimeout(5000)
    }
  }
  const tCreated = await page.getByText('Test Task Beta').isVisible()
  console.log(`Created: ${tCreated}`)

  // REFRESH
  await page.reload({ waitUntil: 'networkidle' })
  await page.waitForTimeout(3000)
  const tPersist = await page.getByText('Test Task Beta').isVisible()
  console.log(`After refresh: ${tPersist}`)
  expect(tPersist).toBe(true)

  // DELETE
  console.log('Deleting task...')
  const delTaskBtn = page.getByRole('button', { name: /delete/i }).first()
  if (await delTaskBtn.isVisible()) {
    await delTaskBtn.click()
    await page.waitForTimeout(1000)
    const confirmBtn = page.locator('div[role="dialog"] button:has-text("Delete")')
    if (await confirmBtn.isVisible()) {
      await confirmBtn.click()
      await page.waitForTimeout(3000)
    }
  }
  const tDeleted = await page.getByText(/no tasks yet/i).isVisible()
  console.log(`After delete empty: ${tDeleted}`)
  expect(tDeleted).toBe(true)

  // 5 HARD REFRESHES
  console.log('\n=== 5 REFRESHES EACH ===')
  for (const path of ['/goals', '/tasks']) {
    for (let i = 1; i <= 5; i++) {
      await page.goto(path, { waitUntil: 'networkidle', timeout: 30000 })
      await page.waitForTimeout(3000)
      const fail = await page.getByText(/failed to load/i).isVisible()
      const retry = await page.getByRole('button', { name: /retry/i }).isVisible()
      const empty = await page.getByText(/no (goals|tasks) yet/i).isVisible()
      console.log(`${path} #${i}: fail=${fail} retry=${retry} empty=${empty}`)
      if (fail || retry) console.log(`  **** FAIL on ${path} #${i}`)
    }
  }

  // NAV MIGRATION
  console.log('\n=== Navigation ===')
  for (const pair of [['/goals', '/tasks'], ['/tasks', '/goals']]) {
    for (const path of pair) {
      await page.goto(path, { waitUntil: 'networkidle', timeout: 30000 })
      await page.waitForTimeout(3000)
      const fail = await page.getByText(/failed to load/i).isVisible()
      const retry = await page.getByRole('button', { name: /retry/i }).isVisible()
      if (fail || retry) console.log(`  **** FAIL on ${path} after ${pair[0]} -> ${pair[1]}`)
    }
  }

  console.log('\n===== SUMMARY =====')
  console.log(`Failed fetch: ${apis.filter(a => a.startsWith('[FAIL]')).length}`)
  console.log(`Timeout: ${apis.filter(a => a.includes('TIMEOUT')).length}`)
  console.log(`Unexpected 401: ${apis.filter(a => a.startsWith('[401]')).length}`)
  console.log(`Unexpected 404: ${apis.filter(a => a.startsWith('[404]')).length}`)
  console.log(`Unexpected 5xx: ${apis.filter(a => /^\[5\d\d\]/.test(a)).length}`)
  console.log('PASS CONDITIONS:')
  console.log(`  Goals load:       PASS`)
  console.log(`  Goals create:     ${gCreated ? 'PASS' : 'FAIL'}`)
  console.log(`  Goals edit:       ${gEdited ? 'PASS' : 'FAIL'}`)
  console.log(`  Goals delete:     ${gDeleted ? 'PASS' : 'FAIL'}`)
  console.log(`  Goals refresh:    ${gPersist ? 'PASS' : 'FAIL'}`)
  console.log(`  Tasks load:       PASS`)
  console.log(`  Tasks create:     ${tCreated ? 'PASS' : 'FAIL'}`)
  console.log(`  Tasks refresh:    ${tPersist ? 'PASS' : 'FAIL'}`)
  console.log(`  Tasks delete:     ${tDeleted ? 'PASS' : 'FAIL'}`)
  console.log(`  Failed fetch:     ${apis.filter(a => a.startsWith('[FAIL]')).length}`)
  console.log(`  Timed out:        ${apis.filter(a => a.includes('TIMEOUT')).length}`)
  console.log(`  Unexpected 401:   ${apis.filter(a => a.startsWith('[401]')).length}`)
  console.log(`  Unexpected 404:   ${apis.filter(a => a.startsWith('[404]')).length}`)
  console.log(`  Unexpected 5xx:   ${apis.filter(a => /^\[5\d\d\]/.test(a)).length}`)
})
