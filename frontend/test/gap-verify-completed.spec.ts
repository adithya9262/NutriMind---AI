import { test, expect } from '@playwright/test'

const TEST_EMAIL = `gap_completed_${Date.now()}@example.com`
const TEST_PASSWORD = 'TestPass123!'

test('vertical gap verification completed state', async ({ page }) => {
  await page.setViewportSize({ width: 1366, height: 768 })

  // Register
  await page.goto('/register', { waitUntil: 'networkidle' })
  await page.fill('input[id="register-email"]', TEST_EMAIL)
  await page.fill('input[id="register-password"]', TEST_PASSWORD)
  await page.fill('input[id="register-confirm"]', TEST_PASSWORD)
  await page.click('button[type="submit"]')
  await page.waitForURL('**/dashboard**', { timeout: 30000 })

  // Complete profile
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

  // Go back to dashboard WITHOUT adding data
  await page.goto('/dashboard', { waitUntil: 'networkidle' })
  await page.waitForTimeout(3000)

  const measure = await page.evaluate(() => {
    const outerFlex = document.querySelector('.flex.flex-col.lg\\:flex-row.gap-6.items-start')
    if (!outerFlex) return { error: 'no-outer-flex' }
    const leftCol = outerFlex.children[0] as HTMLElement
    const rightCol = outerFlex.children[1] as HTMLElement
    if (!leftCol || !rightCol) return { error: 'no-cols' }

    const leftKids = Array.from(leftCol.children).map((c: Element, i: number) => {
      const r = c.getBoundingClientRect()
      return { i, tag: c.tagName, y: Math.round(r.y), h: Math.round(r.height), bottom: Math.round(r.bottom), text: (c.textContent || '').trim().substring(0, 50) }
    })
    const rightKids = Array.from(rightCol.children).map((c: Element, i: number) => {
      const r = c.getBoundingClientRect()
      return { i, tag: c.tagName, y: Math.round(r.y), h: Math.round(r.height), bottom: Math.round(r.bottom), text: (c.textContent || '').trim().substring(0, 50) }
    })

    const leftGaps: number[] = []
    for (let i = 1; i < leftKids.length; i++) leftGaps.push(leftKids[i].y - leftKids[i-1].bottom)

    return { leftKids, rightKids, leftGaps }
  })
  
  console.log('MEASUREMENTS:', JSON.stringify(measure, null, 2))
  await page.screenshot({ path: 'test-results/dashboard-stateB-profile-only.png', fullPage: true })
})
