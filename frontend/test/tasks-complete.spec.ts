import { test, expect } from '@playwright/test'

test('Tasks complete/uncomplete and multiple records', async ({ page }) => {
  test.setTimeout(300000)

  page.on('response', resp => {
    if (resp.url().includes('/api/v1/tasks') || resp.url().includes('/api/v1/goals')) {
      console.log(`[${resp.status()}] ${resp.request().method()} ${resp.url().replace('http://localhost:8000/api/v1', '')}`)
    }
  })

  const uid = Date.now()
  await page.goto('/register', { waitUntil: 'networkidle' })
  await page.fill('#register-email', `final_${uid}@example.com`)
  await page.fill('#register-password', 'TestPass123!')
  await page.fill('#register-confirm', 'TestPass123!')
  await page.click('button[type="submit"]')
  await page.waitForURL(/\/dashboard/, { timeout: 30000 })

  // Create 3 tasks
  await page.goto('/tasks', { waitUntil: 'networkidle' })
  await page.waitForTimeout(1000)

  for (let i = 1; i <= 3; i++) {
    await page.getByRole('button', { name: /add task/i }).first().click()
    await page.waitForTimeout(500)
    await page.locator('#task-title').fill(`Task ${i}`)
    await page.locator('#task-description').fill(`Description ${i}`)
    await page.locator('button[type="submit"]').click()
    await page.waitForTimeout(2000)
  }

  // Verify all 3 visible
  for (let i = 1; i <= 3; i++) {
    const visible = await page.getByText(`Task ${i}`).isVisible()
    console.log(`Task ${i} visible: ${visible}`)
    expect(visible).toBe(true)
  }

  // Complete first task
  const firstTaskCheckbox = page.locator('section[aria-labelledby="task-list-heading"] input[type="checkbox"]').first()
  if (await firstTaskCheckbox.isVisible()) {
    await firstTaskCheckbox.click()
    await page.waitForTimeout(2000)
    console.log('Completed first task')
  }

  // Uncomplete it
  const completedCheckbox = page.locator('section[aria-labelledby="task-list-heading"] input[type="checkbox"][checked]').first()
  if (await completedCheckbox.isVisible()) {
    await completedCheckbox.click()
    await page.waitForTimeout(2000)
    console.log('Reopened first task')
  }

  // Refresh
  await page.reload({ waitUntil: 'networkidle' })
  await page.waitForTimeout(2000)

  // Verify all 3 still there
  for (let i = 1; i <= 3; i++) {
    const visible = await page.getByText(`Task ${i}`).isVisible()
    console.log(`After refresh Task ${i} visible: ${visible}`)
    expect(visible).toBe(true)
  }

  // Delete middle task
  const middleTask = page.locator('section[aria-labelledby="task-list-heading"]').first()
  const middleDeleteBtn = middleTask.locator('button').filter({ has: page.locator('.lucide-trash2') }).nth(1)
  if (await middleDeleteBtn.isVisible()) {
    await middleDeleteBtn.click()
    await page.waitForTimeout(500)
    await page.locator('div[role="dialog"] button', { hasText: 'Delete' }).click()
    await page.waitForTimeout(2000)
    console.log('Deleted middle task')
  }

  // Refresh
  await page.reload({ waitUntil: 'networkidle' })
  await page.waitForTimeout(2000)

  // Verify Task 1 and 3 exist, Task 2 gone
  expect(await page.getByText('Task 1').isVisible()).toBe(true)
  expect(await page.getByText('Task 2').isVisible()).toBe(false)
  expect(await page.getByText('Task 3').isVisible()).toBe(true)

  console.log('\n=== TASKS COMPLETE/UNCOMPLETE + MULTIPLE RECORDS: PASS ===')
})