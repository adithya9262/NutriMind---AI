import { test, expect } from '@playwright/test'

test('Landing page responsive verification', async ({ page }) => {
  test.setTimeout(180000)

  const viewports = [
    { name: '1920x1080', width: 1920, height: 1080 },
    { name: '1366x768', width: 1366, height: 768 },
    { name: '768x1024', width: 768, height: 1024 },
    { name: '375x812', width: 375, height: 812 },
  ]

  for (const vp of viewports) {
    console.log(`Testing ${vp.name}...`)
    await page.setViewportSize({ width: vp.width, height: vp.height })
    await page.goto('http://localhost:3000/', { waitUntil: 'networkidle' })
    await page.waitForTimeout(1000)

    const bodyWidth = await page.evaluate(() => document.body.scrollWidth)
    const viewportWidth = await page.evaluate(() => window.innerWidth)
    
    console.log(`  Body: ${bodyWidth}, Viewport: ${viewportWidth}`)
    
    expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 20)

    // Verify hero is readable
    await expect(page.locator('h1')).toBeVisible()
    await expect(page.locator('h1')).toContainText('Understand Your Nutrition')

    // Verify features section
    await expect(page.locator('#features')).toBeVisible()
    await expect(page.locator('#features h2')).toContainText('Everything You Need')

    // Verify how it works
    await expect(page.locator('#how-it-works')).toBeVisible()
    await expect(page.locator('#how-it-works h2')).toContainText('How It Works')

    // Verify footer
    await expect(page.locator('footer')).toBeVisible()
    await expect(page.locator('footer a[href="/login"]')).toBeVisible()
    await expect(page.locator('footer a[href="/register"]')).toBeVisible()
    
    console.log(`  ${vp.name}: PASS`)
  }

  console.log('All responsive tests PASSED')
})