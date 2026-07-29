import { test, expect } from '@playwright/test'

test('Debug goal create - trace handler execution', async ({ page }) => {
  test.setTimeout(120000)

  // Log all console messages
  page.on('console', msg => {
    console.log(`[CONSOLE] ${msg.type()}: ${msg.text()}`)
  })
  page.on('pageerror', err => console.log(`[PAGE ERROR] ${err.message}`))

  // Log network
  page.on('response', resp => {
    if (resp.url().includes('/api/v1/goals')) {
      console.log(`[NET] [${resp.status()}] ${resp.request().method()} ${resp.url().replace('http://localhost:8000/api/v1', '')}`)
    }
  })
  page.on('requestfailed', req => {
    if (req.url().includes('/api/v1/goals')) {
      console.log(`[FAIL] ${req.method()} ${req.url().replace('http://localhost:8000/api/v1', '')} ${req.failure()?.errorText}`)
    }
  })

  const uid = Date.now()
  await page.goto('/register', { waitUntil: 'networkidle' })
  await page.fill('#register-email', `dbg_${uid}@example.com`)
  await page.fill('#register-password', 'TestPass123!')
  await page.fill('#register-confirm', 'TestPass123!')
  await page.click('button[type="submit"]')
  await page.waitForURL(/\/dashboard/, { timeout: 30000 })

  await page.goto('/goals', { waitUntil: 'networkidle' })
  await page.waitForTimeout(2000)

  // Click Add Goal
  const addBtn = page.getByRole('button', { name: /add goal/i })
  await expect(addBtn.first()).toBeVisible()
  await addBtn.first().click()
  await page.waitForTimeout(1500)

  // Fill form
  const titleInput = page.locator('#title')
  await expect(titleInput).toBeVisible()
  await titleInput.fill('Debug Goal Trace')
  await page.waitForTimeout(500)

  // Invoke handler directly
  const result = await page.locator('button', { hasText: 'Create Goal' }).evaluate(async (el) => {
    const fiberKey = Object.keys(el).find(k => k.startsWith('__reactFiber'))
    const propsKey = Object.keys(el).find(k => k.startsWith('__reactProps'))
    
    if (!fiberKey || !propsKey) return { error: 'No fiber or props found' }
    
    const fiber = el[fiberKey]
    const props = el[propsKey]
    
    if (props && props.onClick) {
      try {
        console.log('[EVAL] Calling props.onClick')
        await props.onClick()
        return { success: true, source: 'props.onClick' }
      } catch (e) {
        console.error('[EVAL] props.onClick error:', e)
        return { error: `props.onClick: ${e.message}` }
      }
    }
    
    if (fiber && fiber.memoizedProps && fiber.memoizedProps.onClick) {
      try {
        console.log('[EVAL] Calling fiber.memoizedProps.onClick')
        await fiber.memoizedProps.onClick()
        return { success: true, source: 'fiber.memoizedProps.onClick' }
      } catch (e) {
        return { error: `fiber onClick: ${e.message}` }
      }
    }
    
    return { error: 'No onClick handler found' }
  })

  console.log('Direct handler call result:', result)

  // Wait for any async operations
  await page.waitForTimeout(5000)

  // Check if goal appears
  const goalVisible = await page.getByText('Debug Goal Trace').isVisible()
  console.log('Goal visible after handler:', goalVisible)

  // Also check for any error state
  const errorVisible = await page.getByText(/failed to create|error/i).isVisible()
  console.log('Error visible:', errorVisible)
  
  // Check createStatus
  const createSuccessVisible = await page.getByText('Goal created successfully').isVisible()
  console.log('Success toast visible:', createSuccessVisible)
})