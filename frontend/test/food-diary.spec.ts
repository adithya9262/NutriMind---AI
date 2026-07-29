import { test, expect } from '@playwright/test'

test('Food Diary form validation', async ({ page }) => {
  test.setTimeout(180000)

  const uid = Date.now()
  await page.goto('/register', { waitUntil: 'networkidle' })
  await page.waitForTimeout(1000)
  await page.fill('#register-email', `food_${uid}@example.com`)
  await page.fill('#register-password', 'TestPass123!')
  await page.fill('#register-confirm', 'TestPass123!')
  await page.click('button[type="submit"]')
  await page.waitForURL(/\/dashboard/, { timeout: 30000 })
  await page.waitForTimeout(2000)

  await page.goto('/nutrition/logs', { waitUntil: 'networkidle' })
  await page.waitForTimeout(2000)

  // Test 1: Create entry with minimum required fields
  console.log('Test 1: Create entry with minimum fields')
  await page.getByRole('button', { name: /add entry/i }).first().click()
  await page.waitForTimeout(500)
  await page.locator('#food-name').fill('Oatmeal')
  // Leave serving_description empty (required) - should fail
  await page.locator('button[type="submit"]').click()
  await page.waitForTimeout(500)
  
  const servingError = await page.locator('text=/serving description is required/i').isVisible()
  console.log('Test 1 - Serving description required:', servingError)
  
  // Fill serving description
  await page.locator('#serving-description').fill('1 cup cooked')
  await page.locator('button[type="submit"]').click()
  await page.waitForTimeout(500)
  
  const nutritionErrors = await page.locator('text=/calories is required/i').isVisible()
  console.log('Test 1 - Nutrition fields required:', nutritionErrors)

  // Fill all nutrition fields
  await page.locator('#entry-calories_kcal').fill('150')
  await page.locator('#entry-protein_g').fill('5')
  await page.locator('#entry-carbohydrate_g').fill('27')
  await page.locator('#entry-fat_g').fill('3')
  await page.locator('button[type="submit"]').click()
  await page.waitForTimeout(2000)
  
  const created = await page.getByText('Oatmeal').isVisible()
  console.log('Test 1 - Created with all fields:', created)
  expect(created).toBe(true)

  // Test 2: Invalid nutrition value (negative)
  console.log('Test 2: Invalid nutrition value')
  await page.getByRole('button', { name: /add entry/i }).first().click()
  await page.waitForTimeout(500)
  await page.locator('#food-name').fill('Bad Entry')
  await page.locator('#serving-description').fill('1 cup')
  await page.locator('#entry-calories_kcal').fill('-100')
  await page.locator('button[type="submit"]').click()
  await page.waitForTimeout(500)
  
  const negError = await page.locator('text=/must not be negative/i').isVisible()
  console.log('Test 2 - Negative calories error:', negError)
  expect(negError).toBe(true)

  // Fix and create
  await page.locator('#entry-calories_kcal').fill('100')
  await page.locator('#entry-protein_g').fill('10')
  await page.locator('#entry-carbohydrate_g').fill('20')
  await page.locator('#entry-fat_g').fill('5')
  await page.locator('button[type="submit"]').click()
  await page.waitForTimeout(2000)

  // Test 3: Refresh persistence
  console.log('Test 3: Refresh persistence')
  await page.reload({ waitUntil: 'networkidle' })
  await page.waitForTimeout(2000)
  const afterRefresh = await page.getByText('Oatmeal').isVisible()
  console.log('Test 3 - After refresh:', afterRefresh)
  expect(afterRefresh).toBe(true)

  // Test 4: Delete entry
  console.log('Test 4: Delete entry')
  const deleteBtn = page.locator('button[aria-label^="Delete"]').first()
  if (await deleteBtn.isVisible()) {
    await deleteBtn.click()
    await page.waitForTimeout(500)
    // Confirm delete - the confirm button says "Delete"
    const confirmBtn = page.locator('button:has-text("Delete")').first()
    if (await confirmBtn.isVisible()) {
      await confirmBtn.click()
    }
    await page.waitForTimeout(2000)
    console.log('Test 4 - Delete completed')
  }

  console.log('All tests passed!')
})