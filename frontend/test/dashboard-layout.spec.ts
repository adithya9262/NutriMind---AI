import { test, expect } from '@playwright/test'

const TEST_EMAIL = `dash_${Date.now()}@example.com`
const TEST_PASSWORD = 'TestPass123!'

test.describe('Dashboard Layout Visual Inspection', () => {
  test('register, populate data, inspect dashboard', async ({ page }) => {
    page.on('console', msg => {
      if (msg.type() === 'error') console.log(`[ERR] ${msg.text()}`)
    })
    page.on('pageerror', err => console.log(`[PAGE ERROR] ${err.message}`))
    page.on('requestfailed', req => console.log(`[REQ FAIL] ${req.url()}`))

    // STEP 1: Register
    await page.goto('/register', { waitUntil: 'networkidle' })
    await page.fill('input[id="register-email"]', TEST_EMAIL)
    await page.fill('input[id="register-password"]', TEST_PASSWORD)
    await page.fill('input[id="register-confirm"]', TEST_PASSWORD)
    await page.click('button[type="submit"]')
    await page.waitForURL('**/dashboard**', { timeout: 30000 })
    console.log('URL after register:', page.url())

    // STEP 2: Go to settings/profile
    await page.goto('/settings?tab=profile', { waitUntil: 'networkidle' })
    await page.waitForTimeout(2000)

    // Fill profile form using known IDs
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
    await page.fill('input[id="settings-carbs"]', '250')
    await page.fill('input[id="settings-fat"]', '70')

    // Submit
    await page.click('button[type="submit"]')
    await page.waitForTimeout(3000)
    await page.screenshot({ path: 'test-results/settings-submitted.png', fullPage: true })
    console.log('Profile saved')

    // STEP 3: Log nutrition data via API
    const authCookie = await page.evaluate(() => {
      const token = localStorage.getItem('nutrimind_access_token_backend')
      return token
    })
    console.log('Auth token present:', !!authCookie)

    // Add nutrition logs via API
    const apiBase = 'http://localhost:8000/api/v1'
    const headers = { 'Authorization': `Bearer ${authCookie}`, 'Content-Type': 'application/json' }

    const foods = [
      { meal_type: 'breakfast', food_name: 'Oatmeal with Berries', calories_kcal: 350, protein_g: 12, carbohydrate_g: 55, fat_g: 5 },
      { meal_type: 'lunch', food_name: 'Grilled Chicken Salad', calories_kcal: 450, protein_g: 40, carbohydrate_g: 15, fat_g: 12 },
      { meal_type: 'dinner', food_name: 'Salmon with Vegetables', calories_kcal: 550, protein_g: 45, carbohydrate_g: 20, fat_g: 18 },
      { meal_type: 'snack', food_name: 'Protein Shake', calories_kcal: 250, protein_g: 30, carbohydrate_g: 10, fat_g: 3 },
    ]
    for (const food of foods) {
      const body = JSON.stringify({
        logged_date: new Date().toISOString().split('T')[0],
        meal_type: food.meal_type,
        food_name: food.food_name,
        serving_description: '1 serving',
        calories_kcal: food.calories_kcal,
        protein_g: food.protein_g,
        carbohydrate_g: food.carbohydrate_g,
        fat_g: food.fat_g
      })
      try {
        const res = await page.evaluate(async (args) => {
          const r = await fetch(args.url, { method: 'POST', headers: args.headers, body: args.body })
          return r.status
        }, { url: `${apiBase}/nutrition-logs`, headers, body })
        console.log(`  Added food: ${food.food_name} -> ${res}`)
      } catch (e) {
        console.log(`  Failed: ${food.food_name} -> ${e}`)
      }
    }

    // Add body weight via API
    try {
      const bwBody = JSON.stringify({ logged_date: new Date().toISOString().split('T')[0], weight_kg: 80 })
      const bwRes = await page.evaluate(async (args) => {
        const r = await fetch(args.url, { method: 'POST', headers: args.headers, body: args.body })
        return r.status
      }, { url: `${apiBase}/body-weights`, headers, body: bwBody })
      console.log(`  Added body weight -> ${bwRes}`)
    } catch (e) {
      console.log(`  Body weight failed: ${e}`)
    }

    // STEP 4: Navigate to dashboard
    await page.goto('/dashboard', { waitUntil: 'networkidle' })
    await page.waitForTimeout(5000)

    await page.screenshot({ path: 'test-results/dashboard-before.png', fullPage: true })
    console.log('')
    console.log('=== DASHBOARD LAYOUT ANALYSIS ===')
    console.log('scrollHeight:', await page.evaluate(() => document.documentElement.scrollHeight))
    console.log('clientHeight:', await page.evaluate(() => document.documentElement.clientHeight))

    // Get all direct children of main > div.space-y-6
    console.log('')
    console.log('=== MAIN SECTIONS ===')
    const mainSections = await page.evaluate(() => {
      const container = document.querySelector('main > .space-y-6')
      if (!container) return 'NOT FOUND'
      return Array.from(container.children).map(el => {
        const rect = el.getBoundingClientRect()
        const text = (el.textContent || '').trim().substring(0, 60)
        return { tag: el.tagName, cls: el.className.substring(0, 80), y: rect.y, h: rect.height, text }
      })
    })
    console.log(JSON.stringify(mainSections, null, 2))

    // Analyze left column
    console.log('')
    console.log('=== LEFT COLUMN (flex-1) ===')
    const leftCol = await page.evaluate(() => {
      const el = document.querySelector('div.flex-1.min-w-0')
      if (!el) return 'NOT FOUND'
      const rect = el.getBoundingClientRect()
      const children = Array.from(el.children).map((c, i) => {
        const cr = c.getBoundingClientRect()
        const t = (c.textContent || '').trim().substring(0, 40)
        return { i, tag: c.tagName, cls: c.className.substring(0, 60), y: cr.y, h: cr.height, text: t }
      })
      return { x: rect.x, y: rect.y, w: rect.width, h: rect.height, children }
    })
    console.log(JSON.stringify(leftCol, null, 2))

    // Analyze right column
    console.log('')
    console.log('=== RIGHT COLUMN (w-80) ===')
    const rightCol = await page.evaluate(() => {
      const els = document.querySelectorAll('div.w-full.lg\\:w-80')
      return Array.from(els).map((el, i) => {
        const rect = el.getBoundingClientRect()
        const children = Array.from(el.children).map((c, j) => {
          const cr = c.getBoundingClientRect()
          const t = (c.textContent || '').trim().substring(0, 40)
          return { j, cls: c.className.substring(0, 60), y: cr.y, h: cr.height, text: t }
        })
        return { i, x: rect.x, y: rect.y, w: rect.width, h: rect.height, children }
      })
    })
    console.log(JSON.stringify(rightCol, null, 2))

    // Check for empty cards
    console.log('')
    console.log('=== ALL CARDS & SKELETONS ===')
    const elements = await page.evaluate(() => {
      const cards = document.querySelectorAll('[class*="card" i], [class*="Card" i]')
      const cardInfo = Array.from(cards).map(el => {
        const r = el.getBoundingClientRect()
        const t = (el.textContent || '').trim()
        return { cls: el.className.substring(0, 50), y: r.y, h: r.height, textLen: t.length, text: t.substring(0, 30) }
      }).filter(c => c.h > 80)

      const skeletons = document.querySelectorAll('[class*="skeleton" i]')
      const skelInfo = Array.from(skeletons).map(el => ({
        cls: el.className,
        rect: el.getBoundingClientRect()
      }))

      return { cards: cardInfo, skeletons: skelInfo }
    })
    console.log('Cards > 80px:', JSON.stringify(elements.cards, null, 2))
    console.log('Skeletons:', JSON.stringify(elements.skeletons, null, 2))

    // Check two-col layouts
    console.log('')
    console.log('=== TWO-COL LAYOUTS ===')
    const twoCol = await page.evaluate(() => {
      const layouts = document.querySelectorAll('div.flex.flex-col.lg\\:flex-row.gap-6')
      return Array.from(layouts).map((l, i) => {
        const r = l.getBoundingClientRect()
        const children = Array.from(l.children).map((c, j) => {
          const cr = c.getBoundingClientRect()
          const t = (c.textContent || '').trim().substring(0, 40)
          return { j, cls: c.className.substring(0, 60), y: cr.y, h: cr.height, w: cr.width, text: t }
        })
        return { i, y: r.y, h: r.height, w: r.width, children }
      })
    })
    console.log(JSON.stringify(twoCol, null, 2))

    // Check the module grid (daily budget + module cards)
    console.log('')
    console.log('=== 12-COL GRID ===')
    const grid12 = await page.evaluate(() => {
      const grid = document.querySelector('div.grid.gap-6.lg\\:grid-cols-12')
      if (!grid) return 'NOT FOUND'
      const r = grid.getBoundingClientRect()
      const children = Array.from(grid.children).map((c, i) => {
        const cr = c.getBoundingClientRect()
        const t = (c.textContent || '').trim().substring(0, 40)
        const style = window.getComputedStyle(c)
        return { i, y: cr.y, h: cr.height, w: cr.width, text: t }
      })
      return { y: r.y, h: r.height, w: r.width, children }
    })
    console.log(JSON.stringify(grid12, null, 2))
  })
})