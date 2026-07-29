import { test, expect } from '@playwright/test'

test('Weight Tracker form validation', async ({ page }) => {
  test.setTimeout(180000)

  const uid = Date.now()
  await page.goto('/register', { waitUntil: 'networkidle' })
  await page.waitForTimeout(1000)
  await page.fill('#register-email', `weight_${uid}@example.com`)
  await page.fill('#register-password', 'TestPass123!')
  await page.fill('#register-confirm', 'TestPass123!')
  await page.click('button[type="submit"]')
  await page.waitForURL(/\/dashboard/, { timeout: 30000 })
  await page.waitForTimeout(2000)

  await page.goto('/body-weight', { waitUntil: 'networkidle' })
  await page.waitForTimeout(2000)

  // Test 1: Create weight with minimum required fields (date + weight)
  console.log('Test 1: Create weight with minimum fields')
  await page.locator('#bw-logged-date').fill('2026-01-15')
  await page.locator('#bw-weight-kg').fill('70.5')
  await page.locator('button[type="submit"]').click()
  await page.waitForTimeout(2000)

  const created = await page.getByText('70.5 kg').isVisible()
  console.log('Test 1 - Created:', created)
  expect(created).toBe(true)

  // Test 2: Empty weight validation
  console.log('Test 2: Empty weight validation')
  await page.locator('#bw-logged-date').fill('2026-01-16')
  await page.locator('#bw-weight-kg').fill('')
  await page.locator('button[type="submit"]').click()
  await page.waitForTimeout(500)
  
  const weightError = await page.locator('text=/weight is required/i').isVisible()
  console.log('Test 2 - Weight required:', weightError)
  expect(weightError).toBe(true)

  // Test 3: Invalid weight (negative)
  console.log('Test 3: Invalid weight (negative)')
  await page.locator('#bw-weight-kg').fill('-5')
  await page.locator('button[type="submit"]').click()
  await page.waitForTimeout(500)
  
  const negError = await page.locator('text=/between 10 and 700/i').isVisible()
  console.log('Test 3 - Negative weight error:', negError)
  expect(negError).toBe(true)

  // Test 4: Valid weight
  console.log('Test 4: Valid weight')
  await page.locator('#bw-weight-kg').fill('72.0')
  await page.locator('button[type="submit"]').click()
  await page.waitForTimeout(2000)

  // Test 5: Refresh persistence
  console.log('Test 5: Refresh persistence')
  await page.waitForTimeout(3000)
  await page.reload({ waitUntil: 'networkidle' })
  await page.waitForTimeout(3000)
  const afterRefresh = await page.locator('p.mt-1.text-xl.font-bold').filter({ hasText: '70.5 kg' }).isVisible()
  console.log('Test 5 - After refresh:', afterRefresh)
  expect(afterRefresh).toBe(true)

  // Test 6: Delete entry
  console.log('Test 6: Delete entry')
  const deleteBtn = page.locator('button[aria-label*="Delete"]').first()
  if (await deleteBtn.isVisible()) {
    await deleteBtn.click()
    await page.waitForTimeout(500)
    await page.locator('div[role="dialog"] button:has-text("Delete")').first().click()
    await page.waitForTimeout(2000)
    console.log('Test 6 - Delete completed')
  }

  console.log('All weight tests passed!')
})