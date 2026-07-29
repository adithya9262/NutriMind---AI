import { test, expect } from '@playwright/test'

test('Goals form validation bug reproduction - detailed', async ({ page }) => {
  test.setTimeout(120000)

  const uid = Date.now()
  
  // Register new user
  await page.goto('/register', { waitUntil: 'networkidle' })
  await page.waitForTimeout(1000)
  await page.fill('#register-email', `test_${uid}@example.com`)
  await page.fill('#register-password', 'TestPass123!')
  await page.fill('#register-confirm', 'TestPass123!')
  await page.click('button[type="submit"]')
  await page.waitForURL(/\/dashboard/, { timeout: 30000 })
  await page.waitForTimeout(2000)

  // Go to goals page
  await page.goto('/goals', { waitUntil: 'networkidle' })
  await page.waitForTimeout(2000)

  // Log all API requests/responses
  page.on('request', request => {
    if (request.url().includes('/api/v1/goals')) {
      console.log('>>> REQUEST:', request.method(), request.url())
      console.log('>>> REQUEST BODY:', request.postData())
    }
  })

  page.on('response', async (response) => {
    const url = response.url()
    if (url.includes('/api/v1/goals')) {
      console.log(`[${response.status()}] ${response.request().method()} ${url}`)
      const body = await response.text()
      console.log('Response:', body)
    }
  })

  page.on('requestfailed', request => {
    const url = request.url()
    if (url.includes('/api/v1/goals')) {
      console.log(`[FAIL] ${request.method()} ${url} ${request.failure()?.errorText}`)
    }
  })

  // Open the create goal form
  const addGoalBtn = page.getByRole('button', { name: /add goal/i })
  if (await addGoalBtn.isVisible()) {
    await addGoalBtn.click()
    await page.waitForTimeout(1000)
  }

  // Fill the form with the exact data from the bug report
  console.log('Filling form...')
  await page.locator('#goal_type').selectOption('weight_loss')
  await page.fill('input[id="title"]', '1 pound in 1 week')
  await page.fill('#description', 'loss weight 1 pound')
  await page.fill('#start_date', '2026-07-21')
  await page.fill('#end_date', '2026-07-28')
  await page.fill('#weekly_target', '1')
  await page.fill('#target_calories', '2000')
  await page.fill('#target_protein_g', '150')
  await page.fill('#target_carbs_g', '250')
  await page.fill('#target_fats_g', '65')
  await page.fill('#target_water_ml', '2000')
  
  console.log('Submitting form...')
  await page.locator('button:has-text("Create Goal")').click()
  await page.waitForTimeout(3000)

  // Check if goal was created or error shown
  const errorVisible = await page.getByText(/failed to load goals|retry|error/i).isVisible().catch(() => false)
  const createdVisible = await page.getByText('1 pound in 1 week').isVisible().catch(() => false)
  
  console.log('Error visible:', errorVisible)
  console.log('Goal created visible:', createdVisible)

  // Check if form errors are shown
  const formErrors = await page.locator('.text-error, .text-red, [role="alert"]').allTextContents()
  console.log('Form errors:', formErrors)

  // Take screenshot
  await page.screenshot({ path: 'goals-test-result.png', fullPage: true })
})