import { test, expect } from '@playwright/test'

test('Landing page screenshots', async ({ page }) => {
  test.setTimeout(120000)

  await page.goto('http://localhost:3000/', { waitUntil: 'networkidle' })
  await page.waitForTimeout(2000)

  // Full page
  await page.screenshot({ path: 'landing-full-final.png', fullPage: true })

  // Top/hero
  await page.screenshot({ path: 'landing-top-final.png', fullPage: false })

  // Features
  const features = page.locator('#features')
  await features.scrollIntoViewIfNeeded()
  await page.waitForTimeout(500)
  const featuresBox = await features.boundingBox()
  if (featuresBox) {
    await page.screenshot({ path: 'landing-features-final.png', clip: { x: 0, y: featuresBox.y - 100, width: 1920, height: featuresBox.height + 200 } })
  }

  // How it works
  const how = page.locator('#how-it-works')
  await how.scrollIntoViewIfNeeded()
  await page.waitForTimeout(500)
  const howBox = await how.boundingBox()
  if (howBox) {
    await page.screenshot({ path: 'landing-how-it-works-final.png', clip: { x: 0, y: howBox.y - 100, width: 1920, height: howBox.height + 200 } })
  }

  // Bottom CTA
  const cta = page.locator('text=Start Building Better Nutrition Habits')
  await cta.scrollIntoViewIfNeeded()
  await page.waitForTimeout(500)
  const ctaBox = await cta.boundingBox()
  if (ctaBox) {
    await page.screenshot({ path: 'landing-bottom-final.png', clip: { x: 0, y: ctaBox.y - 100, width: 1920, height: 600 } })
  }
})