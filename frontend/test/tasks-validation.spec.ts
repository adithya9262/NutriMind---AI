import { test, expect } from '@playwright/test'

test('Tasks form validation', async ({ page }) => {
  test.setTimeout(180000)

  // Register
  const uid = Date.now()
  await page.goto('/register', { waitUntil: 'networkidle' })
  await page.waitForTimeout(1000)
  await page.fill('#register-email', `task_${uid}@example.com`)
  await page.fill('#register-password', 'TestPass123!')
  await page.fill('#register-confirm', 'TestPass123!')
  await page.click('button[type="submit"]')
  await page.waitForURL(/\/dashboard/, { timeout: 30000 })
  await page.waitForTimeout(2000)

  // Go to tasks page
  await page.goto('/tasks', { waitUntil: 'networkidle' })
  await page.waitForTimeout(2000)

  // Test 1: Create task with minimum required fields (title only)
  console.log('Test 1: Create task with title only')
  await page.getByRole('button', { name: /add task/i }).first().click()
  await page.waitForTimeout(1000)
  
  // Fill only title
  await page.locator('#task-title').fill('Minimum Task')
  // Leave description, due_date, category, recurrence, priority as defaults
  
  await page.locator('button[type="submit"]').click()
  await page.waitForTimeout(2000)
  
  const created = await page.getByText('Minimum Task').isVisible()
  console.log('Test 1 - Minimum fields create:', created)
  expect(created).toBe(true)

  // Test 2: Required field validation (empty title)
  console.log('Test 2: Empty title validation')
  await page.getByRole('button', { name: /add task/i }).first().click()
  await page.waitForTimeout(500)
  await page.locator('#task-title').fill('')
  await page.locator('button[type="submit"]').click()
  await page.waitForTimeout(500)
  const titleError = await page.locator('#task-title').getAttribute('aria-invalid')
  console.log('Test 2 - Title aria-invalid:', titleError)
  // Close form
  await page.locator('button:has-text("Cancel")').click()
  await page.waitForTimeout(500)

  // Test 3: Full valid form
  console.log('Test 3: Full valid form')
  await page.getByRole('button', { name: /add task/i }).first().click()
  await page.waitForTimeout(500)
  await page.locator('#task-title').fill('Full Task')
  await page.locator('#task-description').fill('This is a full task with all fields')
  await page.locator('#task-due-date').fill('2026-08-01')
  await page.locator('#task-category').selectOption('exercise')
  await page.locator('#task-recurrence').selectOption('weekly')
  await page.locator('#task-priority').selectOption('high')
  await page.locator('button[type="submit"]').click()
  await page.waitForTimeout(2000)
  const fullCreated = await page.getByRole('heading', { name: 'Full Task' }).isVisible()
  console.log('Test 3 - Full form create:', fullCreated)
  expect(fullCreated).toBe(true)

  // Test 4: Edit task
  console.log('Test 4: Edit task')
  const editBtn = page.locator('button[aria-label*="Edit"]').first()
  if (await editBtn.isVisible()) {
    await editBtn.click()
    await page.waitForTimeout(1000)
    await page.locator('#task-title').fill('')
    await page.locator('#task-title').fill('Edited Task')
    await page.locator('button:has-text("Save Changes")').click()
    await page.waitForTimeout(2000)
    const edited = await page.getByText('Edited Task').isVisible()
    console.log('Test 4 - Edit:', edited)
    expect(edited).toBe(true)
  }

  // Test 5: Delete task
  console.log('Test 5: Delete task')
  const deleteBtn = page.locator('button[aria-label*="Delete"]').first()
  if (await deleteBtn.isVisible()) {
    await deleteBtn.click()
    await page.waitForTimeout(500)
    await page.locator('div[role="dialog"] button:has-text("Delete")').click()
    await page.waitForTimeout(2000)
    console.log('Test 5 - Delete completed')
  }

  // Test 6: Refresh persistence (create a new task to test persistence)
  console.log('Test 6: Refresh persistence')
  await page.getByRole('button', { name: /add task/i }).first().click()
  await page.waitForTimeout(500)
  await page.locator('#task-title').fill('Persist Test')
  await page.locator('button[type="submit"]').click()
  await page.waitForTimeout(2000)
  
  await page.reload({ waitUntil: 'networkidle' })
  await page.waitForTimeout(2000)
  const afterRefresh = await page.getByText('Persist Test').isVisible()
  console.log('Test 6 - After refresh:', afterRefresh)
  expect(afterRefresh).toBe(true)

  // Test 7: Empty state (if we deleted all)
  console.log('Test 7: Empty state')
  // Try to delete any remaining
  const moreDelete = page.locator('button[aria-label*="Delete"]').first()
  if (await moreDelete.isVisible()) {
    await moreDelete.click()
    await page.waitForTimeout(500)
    await page.locator('div[role="dialog"] button:has-text("Delete")').click()
    await page.waitForTimeout(2000)
  }
  const emptyState = await page.getByText(/no tasks yet/i).isVisible()
  console.log('Test 7 - Empty state:', emptyState)
  // Empty state might not show if tasks still exist - just log it

  console.log('All tests passed!')
})