import { test, expect } from '@playwright/test'

function uuidv4() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = Math.random() * 16 | 0
    return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16)
  })
}

const TEST_EMAIL = `pop_${Date.now()}@example.com`
const TEST_PASSWORD = 'TestPass123!'

test.describe('Dashboard Layout — Populated Data Verification', () => {
  test('populate data, verify layout (columns, skeletons, gaps) on populated dashboard', async ({ page }) => {
    const errors: string[] = []
    page.on('pageerror', err => errors.push(err.message))

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
    const apiErrors: string[] = []

    const foods = [
      { meal_type: 'breakfast', food_name: 'Oatmeal with Berries', cals: 350, p: 12, c: 55, f: 5 },
      { meal_type: 'lunch', food_name: 'Grilled Chicken Salad', cals: 450, p: 40, c: 15, f: 12 },
      { meal_type: 'dinner', food_name: 'Salmon with Vegetables', cals: 550, p: 45, c: 20, f: 18 },
      { meal_type: 'snack', food_name: 'Protein Shake', cals: 250, p: 30, c: 10, f: 3 },
      { meal_type: 'breakfast', food_name: 'Scrambled Eggs & Toast', cals: 320, p: 22, c: 25, f: 14 },
    ]
    for (const food of foods) {
      const r = await page.evaluate(async (args) => {
        const resp = await fetch(`${args.url}?logged_date=${args.date}`, { method: 'POST', headers: args.headers, body: JSON.stringify({
          entry_id: args.uuid, food_name: args.food.food_name, meal_type: args.food.meal_type,
          serving_description: '1 serving', calories_kcal: args.food.cals, protein_g: args.food.p,
          carbohydrate_g: args.food.c, fat_g: args.food.f }) })
        return resp.status
      }, { url: `${apiBase}/nutrition-logs`, headers, date: today, food, uuid: uuidv4() })
      if (r !== 201) apiErrors.push(`Food ${food.food_name}: ${r}`)
    }

    for (const w of [
      { date: localDate(new Date(Date.now() - 172800000)), kg: 81.5 },
      { date: localDate(new Date(Date.now() - 86400000)), kg: 80.8 },
      { date: today, kg: 80.0 },
    ]) {
      const r = await page.evaluate(async (args) => {
        const resp = await fetch(`${args.url}?logged_date=${args.date}`, { method: 'POST', headers: args.headers, body: JSON.stringify({ weight_kg: args.kg }) })
        return resp.status
      }, { url: `${apiBase}/body-weights`, headers, date: w.date, kg: w.kg })
      if (r !== 201) apiErrors.push(`Weight ${w.date}: ${r}`)
    }

    const taskRes = await page.evaluate(async (args) => {
      const resp = await fetch(args.url, { method: 'POST', headers: args.headers, body: JSON.stringify({
        task_id: args.uuid, title: 'Drink 8 glasses of water', status: 'pending', priority: 'high', due_date: args.today }) })
      return resp.status
    }, { url: `${apiBase}/tasks`, headers, uuid: uuidv4(), today })
    if (taskRes >= 400) apiErrors.push(`Task: ${taskRes}`)

    // STATE A — populated dashboard first load
    await page.goto('/dashboard', { waitUntil: 'networkidle' })
    await page.waitForTimeout(3000)
    await page.evaluate(() => window.scrollTo(0, 0))
    await page.waitForTimeout(500)
    await page.screenshot({ path: 'test-results/dashboard-stateA.png', fullPage: true })

    const stateA = await page.evaluate(() => {
      const main = document.querySelector('main > .space-y-6')
      if (!main) return {}
      const children = Array.from(main.children).map((el, i) => {
        const r = el.getBoundingClientRect()
        return { i, y: Math.round(r.y), h: Math.round(r.height), text: (el.textContent || '').trim().substring(0, 60) }
      })
      const twoCols = Array.from(document.querySelectorAll('main .flex.flex-col.lg\\:flex-row.gap-6')).map((el, i) => {
        const r = el.getBoundingClientRect()
        const kids = Array.from(el.children).map((c, j) => {
          const cr = c.getBoundingClientRect()
          return { j, y: Math.round(cr.y), h: Math.round(cr.height) }
        })
        return { i, y: Math.round(r.y), h: Math.round(r.height), kids }
      })
      const skels = document.querySelectorAll('[class*="skeleton" i], [class*="Skeleton" i]')
      const recentLogIdx = children.findIndex(c => c.text.includes('Recent Nutritional'))
      const gapBeforeLog = (recentLogIdx > 0 && children[recentLogIdx - 1].h > 0)
        ? children[recentLogIdx].y - (children[recentLogIdx - 1].y + children[recentLogIdx - 1].h) : 0
      return { children, twoCols, skeletonCount: skels.length, gapBeforeLog }
    })

    // STATE B — after refresh
    await page.reload({ waitUntil: 'networkidle' })
    await page.waitForTimeout(3000)
    await page.evaluate(() => window.scrollTo(0, 0))
    await page.waitForTimeout(500)
    await page.screenshot({ path: 'test-results/dashboard-stateB.png', fullPage: true })

    const stateB = await page.evaluate(() => {
      const main = document.querySelector('main > .space-y-6')
      if (!main) return {}
      const twoCols = Array.from(document.querySelectorAll('main .flex.flex-col.lg\\:flex-row.gap-6')).map((el, i) => {
        const r = el.getBoundingClientRect()
        const kids = Array.from(el.children).map((c, j) => {
          const cr = c.getBoundingClientRect()
          return { j, y: Math.round(cr.y), h: Math.round(cr.height) }
        })
        return { i, y: Math.round(r.y), h: Math.round(r.height), kids }
      })
      const skels = document.querySelectorAll('[class*="skeleton" i], [class*="Skeleton" i]')
      return { twoCols, skeletonCount: skels.length }
    })

    // Verify data exists
    const verifyData = await page.evaluate(async (args) => {
      const r = await fetch(`${args.url}?logged_date=${args.date}`, { method: 'GET', headers: args.headers })
      const data = await r.json()
      return { entryCount: data?.data?.entries?.length || 0 }
    }, { url: `${apiBase}/nutrition-logs`, headers, date: today })

    const fails: string[] = []
    if (stateA.skeletonCount > 0) fails.push(`State A: ${stateA.skeletonCount} skeletons`)
    if (stateB.skeletonCount > 0) fails.push(`State B: ${stateB.skeletonCount} skeletons`)
    for (const [label, st] of [['State A', stateA], ['State B', stateB]] as const) {
      for (let t = 0; t < st.twoCols.length; t++) {
        const tc = st.twoCols[t]
        if (tc.kids.length >= 2 && tc.kids[0].h > 0 && tc.kids[1].h > 0 && tc.kids[0].h === tc.kids[1].h) {
          fails.push(`${label}: layout ${t} columns same height (${tc.kids[0].h}px)`)
        }
      }
    }
    if (stateA.gapBeforeLog > 300) fails.push(`State A: large gap (${stateA.gapBeforeLog}px)`)
    if (stateA.gapBeforeLog < 0) fails.push(`State A: gap calc error (${stateA.gapBeforeLog}px)`)
    if (verifyData.entryCount === 0) fails.push(`Zero entries for ${today}`)
    if (apiErrors.length > 0) fails.push(`API errors: ${apiErrors.join('; ')}`)
    const pageErrors = errors.filter(e => !e.includes('ERR_ABORTED'))
    if (pageErrors.length > 0) fails.push(`Page errors: ${pageErrors.join('; ')}`)

    expect(fails).toEqual([])
  })
})
