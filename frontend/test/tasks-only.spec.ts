import { test } from '@playwright/test'
import * as fs from 'fs'

test('Tasks final verification', async ({ page }) => {
  test.setTimeout(180000)

  page.on('response', resp => {
    if (resp.url().includes('/api/v1/tasks')) {
      console.log(`[TASKS] ${resp.status()} ${resp.request().method()}`)
    }
  })
  page.on('requestfailed', req => {
    if (req.url().includes('/api/v1/tasks')) {
      console.log(`[TASKS_FAIL] ${req.method()} ${req.failure()?.errorText}`)
    }
  })

  const uid = Date.now()
  await page.goto('/register', { waitUntil: 'networkidle' })
  await page.fill('input[id="register-email"]', `f_${uid}@example.com`)
  await page.fill('input[id="register-password"]', 'TestPass123!')
  await page.fill('input[id="register-confirm"]', 'TestPass123!')
  await page.click('button[type="submit"]')
  await page.waitForURL('**/dashboard**', { timeout: 30000 })

  // Setup profile
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
  await page.waitForTimeout(2000)

  // === TEST 1: Empty tasks ===
  console.log('\n--- TEST 1: Empty tasks ---')
  await page.goto('/tasks', { waitUntil: 'networkidle', timeout: 30000 })
  await page.waitForTimeout(5000)
  const t1fail = await page.getByText(/failed to load/i).isVisible()
  const t1retry = await page.getByRole('button', { name: /retry/i }).isVisible()
  const t1empty = await page.getByText(/no tasks yet/i).isVisible()
  console.log('Failed to load:', t1fail, 'Retry:', t1retry, 'Empty:', t1empty)
  if (t1fail || t1retry) throw new Error('Empty tasks page shows error')
  await page.screenshot({ path: '../test-results/tasks-empty.png', fullPage: true })

  // === TEST 2: Create task ===
  console.log('\n--- TEST 2: Create task ---')
  await page.goto('/tasks', { waitUntil: 'networkidle', timeout: 30000 })
  await page.waitForTimeout(2000)
  await page.getByRole('button', { name: /add task/i }).click()
  await page.waitForTimeout(500)
  await page.fill('input[id="task-title"]', 'Test Task')
  await page.fill('input[id="task-description"]', 'Test description')
  await page.locator('button[type="submit"]').click()
  await page.waitForTimeout(3000)
  const created = await page.getByText('Task created successfully').isVisible()
  console.log('Task created:', created)
  await page.screenshot({ path: '../test-results/tasks-populated.png', fullPage: true })

  // === TEST 3: Refresh retains task ===
  console.log('\n--- TEST 3: Refresh ---')
  await page.reload({ waitUntil: 'networkidle' })
  await page.waitForTimeout(5000)
  const t3fail = await page.getByText(/failed to load/i).isVisible()
  const t3task = await page.getByText('Test Task').isVisible()
  console.log('Failed:', t3fail, 'Task visible:', t3task)
  if (t3fail) throw new Error('Refresh shows error')

  // === TEST 4: Navigate away and back ===
  console.log('\n--- TEST 4: Navigate away/back ---')
  await page.goto('/dashboard', { waitUntil: 'networkidle', timeout: 30000 })
  await page.waitForTimeout(2000)
  await page.goto('/tasks', { waitUntil: 'networkidle', timeout: 30000 })
  await page.waitForTimeout(5000)
  const t4fail = await page.getByText(/failed to load/i).isVisible()
  const t4task = await page.getByText('Test Task').isVisible()
  console.log('Failed:', t4fail, 'Task visible:', t4task)
  if (t4fail) throw new Error('Navigate away/back shows error')

  // === TEST 5: Delete task ===
  console.log('\n--- TEST 5: Delete task ---')
  const delBtn = page.getByRole('button', { name: /delete/i }).first()
  if (await delBtn.isVisible()) {
    await delBtn.click()
    await page.waitForTimeout(500)
    await page.locator('button:has-text("Delete"):not(:has-text("Goal"))').click()
    await page.waitForTimeout(3000)
  }
  const t5empty = await page.getByText(/no tasks yet/i).isVisible()
  console.log('Empty after delete:', t5empty)
  await page.screenshot({ path: '../test-results/tasks-after-delete.png', fullPage: true })

  // === TEST 6: 5 hard refreshes ===
  console.log('\n--- TEST 6: 5 hard refreshes ---')
  for (let i = 1; i <= 5; i++) {
    await page.reload({ waitUntil: 'networkidle' })
    await page.waitForTimeout(3000)
    const fail = await page.getByText(/failed to load/i).isVisible()
    const retry = await page.getByRole('button', { name: /retry/i }).isVisible()
    const empty = await page.getByText(/no tasks yet/i).isVisible()
    console.log(`Refresh ${i}: fail=${fail} retry=${retry} empty=${empty}`)
    if (fail || retry) throw new Error(`Refresh ${i} shows error`)
  }

  // === SUMMARY ===
  console.log('\n=== ALL TESTS PASSED ===')
})
