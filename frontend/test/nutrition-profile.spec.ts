import { test, expect } from '@playwright/test'

test('Nutrition Profile form validation', async ({ page }) => {
  test.setTimeout(180000)

  const uid = Date.now()
  await page.goto('/register', { waitUntil: 'networkidle' })
  await page.waitForTimeout(1000)
  await page.fill('#register-email', `profile_${uid}@example.com`)
  await page.fill('#register-password', 'TestPass123!')
  await page.fill('#register-confirm', 'TestPass123!')
  await page.click('button[type="submit"]')
  await page.waitForURL(/\/dashboard/, { timeout: 30000 })
  await page.waitForTimeout(2000)

  await page.goto('/nutrition', { waitUntil: 'networkidle' })
  await page.waitForTimeout(2000)

  // Click "Edit" button to open the form
  const editBtn = page.getByRole('button', { name: 'Edit' })
  if (await editBtn.isVisible()) {
    await editBtn.click()
    await page.waitForTimeout(1000)
  }

  // Test 1: Create empty profile (submit without filling any fields)
  console.log('Test 1: Create empty profile')
  await page.locator('button[type="submit"]').click()
  await page.waitForTimeout(2000)
  
  const emptyCreated = await page.locator('text=/profile.*saved|profile.*updated|profile.*created/i').isVisible()
  console.log('Test 1 - Empty profile create:', emptyCreated)

  // Test 2: Fill required fields for calculations
  console.log('Test 2: Fill required fields for calculations')
  // Re-open edit form if needed
  const editBtn2 = page.getByRole('button', { name: 'Edit' })
  if (await editBtn2.isVisible()) {
    await editBtn2.click()
    await page.waitForTimeout(500)
  }
  
  await page.locator('#np-date-of-birth').fill('2000-01-01')
  await page.locator('#np-biological-sex').selectOption('male')
  await page.locator('#np-height').fill('180')
  await page.locator('#np-weight').fill('80')
  await page.locator('#np-activity-level').selectOption('moderately_active')
  await page.locator('#np-goal').selectOption('maintain_weight')
  await page.locator('button:has-text("Save Changes")').click()
  await page.waitForTimeout(2000)

  const profileCreated = await page.locator('text=/profile.*saved|profile.*updated|profile.*created/i').isVisible()
  console.log('Test 2 - Profile with calculations:', profileCreated)

  // Test 3: Invalid height
  console.log('Test 3: Invalid height')
  const editBtn3 = page.getByRole('button', { name: 'Edit' })
  if (await editBtn3.isVisible()) {
    await editBtn3.click()
    await page.waitForTimeout(500)
  }
  await page.locator('#np-height').fill('40')
  await page.locator('button:has-text("Save Changes")').click()
  await page.waitForTimeout(500)
  
  const heightError = await page.locator('text=/height must be between 50 and 300/i').isVisible()
  console.log('Test 3 - Height error:', heightError)
  expect(heightError).toBe(true)

  // Fix and save
  await page.locator('#np-height').fill('180')
  await page.locator('button:has-text("Save Changes")').click()
  await page.waitForTimeout(2000)

  // Test 4: Invalid weight (negative)
  console.log('Test 4: Invalid weight')
  const editBtn4 = page.getByRole('button', { name: 'Edit' })
  if (await editBtn4.isVisible()) {
    await editBtn4.click()
    await page.waitForTimeout(500)
  }
  await page.locator('#np-weight').fill('-5')
  await page.locator('button:has-text("Save Changes")').click()
  await page.waitForTimeout(500)

  const weightError = await page.locator('text=/weight must be between 10 and 700/i').isVisible()
  console.log('Test 4 - Weight error:', weightError)
  expect(weightError).toBe(true)

  // Fix and save
  await page.locator('#np-weight').fill('80')
  await page.locator('button:has-text("Save Changes")').click()
  await page.waitForTimeout(2000)

  // Test 5: Refresh persistence
  console.log('Test 5: Refresh persistence')
  await page.reload({ waitUntil: 'networkidle' })
  await page.waitForTimeout(2000)
  const afterRefresh = await page.locator('text=/80\\.0 kg/').isVisible()
  console.log('Test 5 - After refresh:', afterRefresh)
  expect(afterRefresh).toBe(true)

  console.log('All tests passed!')
})