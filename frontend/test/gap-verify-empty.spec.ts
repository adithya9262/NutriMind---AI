import { test, expect } from '@playwright/test'

function uuidv4() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = Math.random() * 16 | 0
    return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16)
  })
}

const TEST_EMAIL = `gap_empty_${Date.now()}@example.com`
const TEST_PASSWORD = 'TestPass123!'

test('vertical gap verification empty state', async ({ page }) => {
  await page.setViewportSize({ width: 1366, height: 768 })

  // Register new user (incomplete profile)
  await page.goto('/register', { waitUntil: 'networkidle' })
  await page.fill('input[id="register-email"]', TEST_EMAIL)
  await page.fill('input[id="register-password"]', TEST_PASSWORD)
  await page.fill('input[id="register-confirm"]', TEST_PASSWORD)
  await page.click('button[type="submit"]')
  await page.waitForURL('**/dashboard**', { timeout: 30000 })
  await page.waitForTimeout(3000)

  const measure = await page.evaluate(() => {
    const getY = (selector) => {
      const el = document.querySelector(selector)
      if (!el) return null
      return Math.round(el.getBoundingClientRect().bottom)
    }
    const onboarding = getY('.lg\\:col-span-2 > div') || getY('.lg\\:col-span-2')
    // Find the "Recent Nutritional Log" element using text content
    let recentLogY = null
    const cards = document.querySelectorAll('.card-hover')
    for (const card of cards) {
      const h3 = card.querySelector('h3')
      if (h3 && h3.textContent?.includes('Recent Nutritional Log')) {
        recentLogY = Math.round(card.getBoundingClientRect().y)
        break
      }
    }
    return {
      onboardingBottom: onboarding,
      recentLogY: recentLogY
    }
  })
  
  console.log('MEASUREMENTS:', measure)
  await page.screenshot({ path: 'test-results/dashboard-stateA-empty.png', fullPage: true })
})
