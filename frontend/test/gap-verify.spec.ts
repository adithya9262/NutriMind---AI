import { test, expect } from '@playwright/test'

function uuidv4() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = Math.random() * 16 | 0
    return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16)
  })
}

const TEST_EMAIL = `gap_${Date.now()}@example.com`
const TEST_PASSWORD = 'TestPass123!'

test('vertical gap verification', async ({ page }) => {
  const errors: string[] = []
  page.on('pageerror', err => errors.push(err.message))

  await page.setViewportSize({ width: 1366, height: 768 })

  await page.goto('/register', { waitUntil: 'networkidle' })
  await page.fill('input[id="register-email"]', TEST_EMAIL)
  await page.fill('input[id="register-password"]', TEST_PASSWORD)
  await page.fill('input[id="register-confirm"]', TEST_PASSWORD)
  await page.click('button[type="submit"]')
  await page.waitForURL('**/dashboard**', { timeout: 30000 })

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

  const token = await page.evaluate(() => localStorage.getItem('backend_access_token'))
  const headers = { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }
  const apiBase = 'http://localhost:8000/api/v1'

  function localDate(d?: Date): string {
    const date = d ?? new Date()
    const y = date.getFullYear()
    const m = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    return `${y}-${m}-${day}`
  }
  const today = localDate()

  // Populate food logs + weights + task
  for (const food of [
    { meal_type: 'breakfast', food_name: 'Oatmeal with Berries', cals: 350, p: 12, c: 55, f: 5 },
    { meal_type: 'lunch', food_name: 'Grilled Chicken Salad', cals: 450, p: 40, c: 15, f: 12 },
    { meal_type: 'dinner', food_name: 'Salmon with Vegetables', cals: 550, p: 45, c: 20, f: 18 },
  ]) {
    await page.evaluate(async (args) => {
      const resp = await fetch(`${args.url}?logged_date=${args.date}`, { method: 'POST', headers: args.headers, body: JSON.stringify({
        entry_id: args.uuid, food_name: args.food.food_name, meal_type: args.food.meal_type,
        serving_description: '1 serving', calories_kcal: args.food.cals, protein_g: args.food.p,
        carbohydrate_g: args.food.c, fat_g: args.food.f }) })
      return resp.status
    }, { url: `${apiBase}/nutrition-logs`, headers, date: today, food, uuid: uuidv4() })
  }
  for (const w of [{ date: today, kg: 80.0 }]) {
    await page.evaluate(async (args) => {
      const resp = await fetch(`${args.url}?logged_date=${args.date}`, { method: 'POST', headers: args.headers, body: JSON.stringify({ weight_kg: args.kg }) })
      return resp.status
    }, { url: `${apiBase}/body-weights`, headers, date: w.date, kg: w.kg })
  }
  await page.evaluate(async (args) => {
    const resp = await fetch(args.url, { method: 'POST', headers: args.headers, body: JSON.stringify({
      task_id: args.uuid, title: 'Drink water', status: 'pending', priority: 'high', due_date: args.today }) })
    return resp.status
  }, { url: `${apiBase}/tasks`, headers, uuid: uuidv4(), today })

  // Verify data exists
  const verifyData = await page.evaluate(async (args) => {
    const r = await fetch(`${args.url}?logged_date=${args.date}`, { method: 'GET', headers: args.headers })
    const d = await r.json()
    return d?.data?.entries?.length || 0
  }, { url: `${apiBase}/nutrition-logs`, headers, date: today })

  // STATE A: populated dashboard
  await page.goto('/dashboard', { waitUntil: 'networkidle' })
  await page.waitForTimeout(3000)
  await page.evaluate(() => window.scrollTo(0, 0))
  await page.waitForTimeout(500)

  const measureA = await page.evaluate(() => {
    const getY = (text: string): number => {
      const el = Array.from(document.querySelectorAll('*')).find(e => e.textContent?.trim().includes(text))
      return el ? Math.round(el.getBoundingClientRect().y) : -1
    }
    // Left column items (flex-1 children within the outer flex-row)
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

    // Left column: the gap between each consecutive child:
    const leftGaps: number[] = []
    for (let i = 1; i < leftKids.length; i++) {
      const gap = leftKids[i].y - leftKids[i-1].bottom
      leftGaps.push(gap)
    }

    // Right column gaps
    const rightGaps: number[] = []
    for (let i = 1; i < rightKids.length; i++) {
      const gap = rightKids[i].y - rightKids[i-1].bottom
      rightGaps.push(gap)
    }

    const skels = document.querySelectorAll('[class*="skeleton" i]')
    return { leftKids, rightKids, leftGaps, rightGaps, skeletonCount: skels.length }
    })
  console.log('=== STATE A (populated) ===')
  console.log('Skeletons:', measureA.skeletonCount)
  console.log('Left column items:', JSON.stringify(measureA.leftKids, null, 2))
  console.log('Left column gaps (px):', JSON.stringify(measureA.leftGaps))
  console.log('Right column items:', JSON.stringify(measureA.rightKids, null, 2))
  console.log('Right column gaps (px):', JSON.stringify(measureA.rightGaps))
  await page.screenshot({ path: 'test-results/dashboard-stateA.png', fullPage: true })

  // STATE B: refresh
  await page.reload({ waitUntil: 'networkidle' })
  await page.waitForTimeout(3000)
  await page.evaluate(() => window.scrollTo(0, 0))
  await page.waitForTimeout(500)

  const measureB = await page.evaluate(() => {
    const outerFlex = document.querySelector('.flex.flex-col.lg\\:flex-row.gap-6.items-start')
    if (!outerFlex) return { error: 'no-outer-flex' }
    const leftCol = outerFlex.children[0] as HTMLElement
    const rightCol = outerFlex.children[1] as HTMLElement
    if (!leftCol || !rightCol) return { error: 'no-cols' }
    const leftKids = Array.from(leftCol.children).map((c: Element, i: number) => {
      const r = c.getBoundingClientRect()
      return { i, y: Math.round(r.y), h: Math.round(r.height), bottom: Math.round(r.bottom), text: (c.textContent || '').trim().substring(0, 50) }
    })
    const rightKids = Array.from(rightCol.children).map((c: Element, i: number) => {
      const r = c.getBoundingClientRect()
      return { i, y: Math.round(r.y), h: Math.round(r.height), bottom: Math.round(r.bottom), text: (c.textContent || '').trim().substring(0, 50) }
    })
    const leftGaps: number[] = []
    for (let i = 1; i < leftKids.length; i++) leftGaps.push(leftKids[i].y - leftKids[i-1].bottom)
    const rightGaps: number[] = []
    for (let i = 1; i < rightKids.length; i++) rightGaps.push(rightKids[i].y - rightKids[i-1].bottom)
    const skels = document.querySelectorAll('[class*="skeleton" i]')
    return { leftKids, rightKids, leftGaps, rightGaps, skeletonCount: skels.length }
  })
  console.log('=== STATE B (refreshed) ===')
  console.log('Skeletons:', measureB.skeletonCount)
  console.log('Left gaps (px):', JSON.stringify(measureB.leftGaps))
  console.log('Right gaps (px):', JSON.stringify(measureB.rightGaps))
  await page.screenshot({ path: 'test-results/dashboard-stateB.png', fullPage: true })

  // VERIFY
  const fails: string[] = []

  // 1. No skeletons
  if (measureA.skeletonCount > 0) fails.push(`State A: ${measureA.skeletonCount} skeletons`)
  if (measureB.skeletonCount > 0) fails.push(`State B: ${measureB.skeletonCount} skeletons`)

  // 2. Left column gaps all reasonable (24-36px for gap-6)
  for (const [label, m] of [['State A', measureA], ['State B', measureB]] as const) {
    for (let i = 0; i < m.leftGaps.length; i++) {
      if (m.leftGaps[i] > 60) fails.push(`${label}: left gap ${i} too large (${m.leftGaps[i]}px)`)
    }
  }

  // 3. Right column gaps all reasonable
  for (const [label, m] of [['State A', measureA], ['State B', measureB]] as const) {
    for (let i = 0; i < m.rightGaps.length; i++) {
      if (m.rightGaps[i] > 60) fails.push(`${label}: right gap ${i} too large (${m.rightGaps[i]}px)`)
    }
  }

  // 4. Data populated
  if (verifyData < 3) fails.push(`Only ${verifyData} food entries`)

  // 5. Page errors
  if (errors.filter(e => !e.includes('ERR_ABORTED')).length > 0) fails.push(`Page errors: ${errors.join('; ')}`)

  console.log('\n=== VERDICT ===')
  if (fails.length === 0) console.log('ALL CHECKS PASSED')
  else fails.forEach(f => console.log(`FAIL: ${f}`))

  expect(fails).toEqual([])
})
