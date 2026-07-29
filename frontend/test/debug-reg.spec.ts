import { test, expect } from '@playwright/test'

test('Debug registration flow', async ({ page }) => {
  test.setTimeout(180000)

  const consoleErrors: string[] = []
  page.on('console', msg => {
    console.log('[CONSOLE]', msg.type(), msg.text())
    if (msg.type() === 'error') console.log('[CONSOLE ERROR]', msg.text())
  })
  page.on('pageerror', err => console.log('[PAGE ERROR]', err.message))

  const uid = Date.now()
  await page.goto('/register', { waitUntil: 'networkidle' })
  await page.waitForTimeout(1000)
  
  await page.fill('#register-email', `debug_${uid}@example.com`)
  await page.fill('#register-password', 'TestPass123!')
  await page.fill('#register-confirm', 'TestPass123!')
  await page.click('button[type="submit"]')
  
  // Wait longer for registration
  try {
    await page.waitForURL(/\/dashboard/, { timeout: 60000 })
    console.log('Reached dashboard!')
  } catch (e) {
    const currentUrl = page.url()
    console.log('Current URL:', currentUrl)
    await page.screenshot({ path: 'debug-reg.png', fullPage: true })
    throw e
  }
  
  await page.waitForTimeout(2000)
  console.log('Final URL:', page.url())
})