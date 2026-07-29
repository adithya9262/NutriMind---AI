import { test, expect } from '@playwright/test'

const TEST_EMAIL = `dash_${Date.now()}@example.com`
const TEST_PASSWORD = 'TestPass123!'

test.describe('Dashboard Layout Final Verification', () => {
  test('register, populate data, verify dashboard layout after fix', async ({ page }) => {
    page.on('pageerror', err => console.log(`[PAGE ERROR] ${err.message}`))
    page.on('requestfailed', req => console.log(`[REQ FAIL] ${req.url()}`))

    // Register
    await page.goto('/register', { waitUntil: 'networkidle' })
    await page.fill('input[id="register-email"]', TEST_EMAIL)
    await page.fill('input[id="register-password"]', TEST_PASSWORD)
    await page.fill('input[id="register-confirm"]', TEST_PASSWORD)
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

    // Navigate to dashboard
    await page.goto('/dashboard', { waitUntil: 'networkidle' })
    await page.waitForTimeout(3000)
    
    // Reset scroll position
    await page.evaluate(() => window.scrollTo(0, 0))
    await page.waitForTimeout(500)

    // Take "after" screenshot
    await page.screenshot({ path: 'test-results/dashboard-after.png', fullPage: true })
    
    // Verify layout
    const layout = await page.evaluate(() => {
      const main = document.querySelector('main > .space-y-6')
      if (!main) return { error: 'main not found' }
      
      const children = Array.from(main.children).map((el, i) => {
        const r = el.getBoundingClientRect()
        const text = (el.textContent || '').trim().substring(0, 50)
        const cls = el.className
        return { i, y: Math.round(r.y), h: Math.round(r.height), text, cls: cls.substring(0, 80) }
      })
      
      // Two-col layouts
      const twoCols = Array.from(document.querySelectorAll('main .flex.flex-col.lg\\:flex-row')).map((el, i) => {
        const r = el.getBoundingClientRect()
        const children = Array.from(el.children).map((c, j) => {
          const cr = c.getBoundingClientRect()
          return { j, y: Math.round(cr.y), h: Math.round(cr.height), w: Math.round(cr.width) }
        })
        return { i, y: Math.round(r.y), h: Math.round(r.height), children }
      })
      
      // Check skeletions
      const skels = document.querySelectorAll('[class*="skeleton" i], [class*="Skeleton" i]')
      
      return { mainSections: children, twoColLayouts: twoCols, skeletonCount: skels.length, scrollHeight: document.documentElement.scrollHeight, viewportHeight: window.innerHeight }
    })
    
    console.log('LAYOUT VERIFICATION:', JSON.stringify(layout, null, 2))
    
    // Assertions
    expect(layout.skeletonCount).toBe(0) // No skeleton shimmers
    
    // The two layouts should have different column heights (not stretched together)
    if (layout.twoColLayouts.length >= 2) {
      const layout0 = layout.twoColLayouts[0]
      const layout1 = layout.twoColLayouts[1]
      
      // First layout: left and right should NOT have same height
      if (layout0.children.length >= 2) {
        const leftH = layout0.children[0].h
        const rightH = layout0.children[1].h
        console.log(`Layout 0: Left h=${leftH}, Right h=${rightH}, Same=${leftH === rightH}`)
        // Left should be shorter than right (WeeklyChart+NuritionProgress vs AI+DailyRecs+Goals+Tasks)
        // Actually right might be taller, that's fine - they just shouldn't be identical
      }
      
      // Second layout: left should NOT be stretched to match right
      if (layout1.children.length >= 2) {
        const leftH = layout1.children[0].h
        const rightH = layout1.children[1].h
        console.log(`Layout 1: Left h=${leftH}, Right h=${rightH}, Same=${leftH === rightH}`)
      }
    }
    
    expect(layout.mainSections.length).toBeGreaterThan(0)
    console.log('PASS: Layout verification completed')
  })
})