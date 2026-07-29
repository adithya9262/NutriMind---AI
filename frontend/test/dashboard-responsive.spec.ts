import { test, expect } from '@playwright/test'

test.describe('Dashboard Responsive Check', () => {
  test('check responsive layout at 1366x768 and 375x812', async ({ context }) => {
    const page = await context.newPage()
    
    page.on('pageerror', err => console.log(`[PAGE ERROR] ${err.message}`))
    page.on('console', msg => {
      if (msg.type() === 'error') console.log(`[ERR] ${msg.text()}`)
    })

    // 1366x768 desktop viewport
    await page.setViewportSize({ width: 1366, height: 768 })
    const email = `resp_${Date.now()}@example.com`
    
    // Register
    await page.goto('/register', { waitUntil: 'networkidle' })
    await page.fill('input[id="register-email"]', email)
    await page.fill('input[id="register-password"]', 'TestPass123!')
    await page.fill('input[id="register-confirm"]', 'TestPass123!')
    await page.click('button[type="submit"]')
    await page.waitForURL('**/dashboard**', { timeout: 30000 })

    // Fill profile
    await page.goto('/settings?tab=profile', { waitUntil: 'networkidle' })
    await page.waitForTimeout(2000)
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
    await page.waitForTimeout(3000)

    // Desktop check
    await page.goto('/dashboard', { waitUntil: 'networkidle' })
    await page.waitForTimeout(3000)
    
    const desktop = await page.evaluate(() => {
      const html = document.documentElement
      return {
        scrollWidth: html.scrollWidth,
        clientWidth: html.clientWidth,
        overflowX: window.getComputedStyle(html).overflowX,
        hasOverflow: html.scrollWidth > html.clientWidth,
      }
    })
    console.log('Desktop (1366x768):', JSON.stringify(desktop))
    expect(desktop.hasOverflow).toBe(false)
    
    // Mobile check
    await page.setViewportSize({ width: 375, height: 812 })
    await page.waitForTimeout(1000)
    
    const mobile = await page.evaluate(() => {
      const html = document.documentElement
      return {
        scrollWidth: html.scrollWidth,
        clientWidth: html.clientWidth,
        overflowX: window.getComputedStyle(html).overflowX,
        hasOverflow: html.scrollWidth > html.clientWidth,
      }
    })
    console.log('Mobile (375x812):', JSON.stringify(mobile))
    expect(mobile.hasOverflow).toBe(false)
    
    console.log('PASS: No horizontal overflow detected')
  })
})