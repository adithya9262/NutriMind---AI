import { test, expect } from '@playwright/test'

test('Landing page verification', async ({ page }) => {
  test.setTimeout(120000)

  const consoleErrors: string[] = []
  page.on('console', msg => {
    if (msg.type() === 'error') consoleErrors.push(msg.text())
  })
  page.on('pageerror', err => {
    consoleErrors.push(err.message)
  })

  await page.goto('/', { waitUntil: 'networkidle' })
  await page.waitForTimeout(2000)

  // Check hero
  await expect(page.locator('h1')).toBeVisible()
  const heroText = await page.locator('h1').textContent()
  console.log('Hero:', heroText)
  expect(heroText).toContain('Understand Your Nutrition')

  // Check navbar
  await expect(page.locator('header a[href="#features"]')).toBeVisible()
  await expect(page.locator('header a[href="#how-it-works"]')).toBeVisible()
  await expect(page.locator('header a[href="/login"]')).toBeVisible()
  await expect(page.locator('header a[href="/register"]')).toBeVisible()

  // Check features section
  await expect(page.locator('#features')).toBeVisible()
  await expect(page.locator('#features h2')).toContainText('Everything You Need')

  // Check feature cards (6 expected)
  const featureCards = page.locator('#features .card-hover')
  await expect(featureCards).toHaveCount(6)

  // Check how it works section
  await expect(page.locator('#how-it-works')).toBeVisible()
  await expect(page.locator('#how-it-works h2')).toContainText('How It Works')

  // Check coach demo
  await expect(page.locator('text=AI Nutrition Coach')).toBeVisible()

  // Check CTA band
  await expect(page.locator('text=Start Building Better Nutrition Habits')).toBeVisible()
  await expect(page.locator('text=Bring your nutrition, goals and progress tracking together.')).toBeVisible()

// Check footer
  await expect(page.locator('footer')).toBeVisible()
  await expect(page.locator('footer a[href="#features"]')).toBeVisible()
  await expect(page.locator('footer a[href="#how-it-works"]')).toBeVisible()
  await expect(page.locator('footer a[href="/login"]')).toBeVisible()
  await expect(page.locator('footer a[href="/register"]')).toBeVisible()
  const medicalText = page.locator('footer >> text="Not for medical use"')
  await expect(medicalText).not.toBeVisible() // old text removed
  await expect(page.locator('footer:has-text("informational wellness tools")')).toBeVisible()

  // Check no unsupported claims
  await expect(page.getByText('Genomic Blueprinting')).not.toBeVisible()
  await expect(page.getByText('Biological Age')).not.toBeVisible()
  await expect(page.getByText('Blood Analytics')).not.toBeVisible()
  await expect(page.getByText('Clinical Grade')).not.toBeVisible()
  await expect(page.getByText('Neural Sync')).not.toBeVisible()
  await expect(page.getByText('Cognitive Load')).not.toBeVisible()
  await expect(page.getByText('Metabolic Flux')).not.toBeVisible()
  await expect(page.getByText('longevity')).not.toBeVisible()
  await expect(page.getByText('elite performer')).not.toBeVisible()
  await expect(page.getByText('precision biology')).not.toBeVisible()
  await expect(page.getByText('Backend connected')).not.toBeVisible()

  // Test anchor navigation
  await page.locator('header a[href="#features"]').click()
  await page.waitForTimeout(800)
  const featuresInView = await page.evaluate(() => {
    const el = document.getElementById('features')
    if (!el) return false
    const rect = el.getBoundingClientRect()
    return rect.top >= -200 && rect.top <= window.innerHeight
  })
  expect(featuresInView).toBe(true)

  await page.locator('header a[href="#how-it-works"]').click()
  await page.waitForTimeout(800)
  const howInView = await page.evaluate(() => {
    const el = document.getElementById('how-it-works')
    if (!el) return false
    const rect = el.getBoundingClientRect()
    return rect.top >= -200 && rect.top <= window.innerHeight
  })
  expect(howInView).toBe(true)

  // Test Sign In navigation
  await page.locator('header a[href="/login"]').first().click()
  await page.waitForURL('**/login**', { timeout: 15000 })
  expect(page.url()).toContain('/login')

  // Go back and test Get Started
  await page.goto('/', { waitUntil: 'networkidle' })
  await page.waitForTimeout(500)
  await page.locator('header a[href="/register"]').first().click()
  await page.waitForURL('**/register**', { timeout: 15000 })
  expect(page.url()).toContain('/register')

  // Check console errors
  const filteredErrors = consoleErrors.filter(e => !e.includes('React DevTools') && !e.includes('Download the React DevTools'))
  console.log('Console errors:', filteredErrors)
  expect(filteredErrors.length).toBe(0)

  // Screenshots
  await page.setViewportSize({ width: 1920, height: 1080 })
  await page.goto('/', { waitUntil: 'networkidle' })
  await page.waitForTimeout(2000)
  await page.screenshot({ path: 'landing-full-final.png', fullPage: true })
  await page.screenshot({ path: 'landing-top-final.png', fullPage: false })

  await page.locator('#features').scrollIntoViewIfNeeded()
  await page.waitForTimeout(500)
  await page.screenshot({ path: 'landing-features-final.png', fullPage: true })

  await page.locator('#how-it-works').scrollIntoViewIfNeeded()
  await page.waitForTimeout(500)
  await page.screenshot({ path: 'landing-how-it-works-final.png', fullPage: true })

  const cta = page.locator('text=Start Building Better Nutrition Habits')
  await cta.scrollIntoViewIfNeeded()
  await page.waitForTimeout(500)
  await page.screenshot({ path: 'landing-bottom-final.png', fullPage: true })

  // Mobile
  await page.setViewportSize({ width: 375, height: 812 })
  await page.goto('/', { waitUntil: 'networkidle' })
  await page.waitForTimeout(1000)
  await page.screenshot({ path: 'landing-mobile-final.png', fullPage: true })

  // Check no horizontal overflow on mobile
  const bodyWidth = await page.evaluate(() => document.body.scrollWidth)
  const viewportWidth = await page.evaluate(() => window.innerWidth)
  expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 20)

  console.log('PASSED: Landing page verification')
})