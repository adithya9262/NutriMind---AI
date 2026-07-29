import { test } from '@playwright/test'

test.setTimeout(300000)

function localDate(d?: Date): string {
  const date = d ?? new Date()
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

test('find the actual vertical gap on dashboard', async ({ page }) => {
  await page.setViewportSize({ width: 1366, height: 768 })

  const errors: string[] = []
  page.on('pageerror', err => { errors.push(err.message); console.log(`[PAGE ERROR] ${err.message}`) })
  page.on('console', msg => { if (msg.type() === 'error') console.log(`[ERR] ${msg.text()}`) })

  const email = `findgap_${Date.now()}@example.com`
  const password = 'TestPass123!'

  // 1. Register
  console.log('Registering...')
  await page.goto('/register', { waitUntil: 'networkidle' })
  // Debug the form
  console.log('Page URL:', page.url())
  // Check for visible errors
  const pageText = await page.locator('body').textContent()
  if (pageText && (pageText.includes('error') || pageText.includes('Error'))) {
    console.log('PAGE CONTAINS ERROR TEXT')
  }
  // Check input fields exist
  const emailInput = page.locator('input[id="register-email"]')
  console.log('Email input exists:', await emailInput.isVisible())
  await page.fill('input[id="register-email"]', email)
  await page.fill('input[id="register-password"]', password)
  await page.fill('input[id="register-confirm"]', password)
  // Log button info
  const submitBtn = page.locator('button[type="submit"]')
  console.log('Submit button exists:', await submitBtn.isVisible())
  console.log('Submit button text:', await submitBtn.textContent())
  await submitBtn.click()
  console.log('Clicked submit, waiting for navigation...')
  await page.waitForURL('**/dashboard**', { timeout: 30000 })
  console.log('URL after register:', page.url())
  await page.waitForTimeout(1000)
  console.log('Registered, on dashboard')

  // 2. Complete profile
  console.log('Completing profile...')
  await page.goto('/settings?tab=profile', { waitUntil: 'domcontentloaded' })
  await page.waitForTimeout(1500)
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
  await page.waitForTimeout(2000)
  console.log('Profile saved')

  // 3. Get token for API calls — WAIT for backend_access_token specifically (supabase token rejected by backend)
  const token = await page.evaluate(() => {
    return new Promise<string | null>(resolve => {
      let attempts = 0
      const check = () => {
        const t = localStorage.getItem('backend_access_token')
        if (t) resolve(t)
        else if (++attempts < 60) setTimeout(check, 500)
        else resolve(null)
      }
      check()
    })
  })
  console.log(`Token: ${token ? 'YES' : 'NO'}`)
  if (!token) { console.log('NO TOKEN - aborting'); return }
  const headers = { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }
  const apiBase = 'http://localhost:8000/api/v1'
  const today = localDate()

  // 4. Add nutrition data
  const foods = [
    { meal_type: 'breakfast', food_name: 'Oatmeal', cals: 400, p: 12, c: 55, f: 5 },
    { meal_type: 'lunch', food_name: 'Chicken Rice', cals: 650, p: 40, c: 65, f: 12 },
  ]
  for (const food of foods) {
    const r = await page.evaluate(async ({ u, h, d, f }) => {
      const resp = await fetch(`${u}/nutrition-logs?logged_date=${d}`, {
        method: 'POST', headers: h,
        body: JSON.stringify({
          entry_id: crypto.randomUUID(), food_name: f.food_name,
          meal_type: f.meal_type, serving_description: '1 serving',
          calories_kcal: f.cals, protein_g: f.p,
          carbohydrate_g: f.c, fat_g: f.f
        })
      })
      return resp.status
    }, { u: apiBase, h: headers, d: today, f: food })
    console.log(`  Food ${food.food_name}: ${r}`)
  }

  // 5. Add body weight
  for (const w of [
    { date: localDate(new Date(Date.now() - 86400000)), kg: 71.5 },
    { date: today, kg: 71.0 },
  ]) {
    const r = await page.evaluate(async ({ u, h, d, w }) => {
      const resp = await fetch(`${u}/body-weights?logged_date=${d}`, {
        method: 'POST', headers: h,
        body: JSON.stringify({ weight_kg: w.kg })
      })
      return resp.status
    }, { u: apiBase, h: headers, d: w.date, w })
    console.log(`  Weight ${w.date}: ${r}`)
  }

  // NO goals, NO tasks — this is the specific combination user reports
  console.log('STATE: Profile complete, nutrition=populated, weight=populated, goals=empty, tasks=empty')

  // 6. Now load the dashboard with BROWSER VISIBLE
  await page.goto('/dashboard', { waitUntil: 'domcontentloaded' })
  console.log('Dashboard loaded. Waiting for data to settle...')
  
  // Wait for skeletons to disappear
  await page.waitForTimeout(3000)
  try {
    await page.waitForFunction(() => {
      const skels = document.querySelectorAll('[class*="animate-shimmer"]')
      return skels.length === 0
    }, { timeout: 10000 })
  } catch {}
  await page.waitForTimeout(1000)
  console.log('Dashboard stable. Starting measurements...')

  // ================================
  // PHASE 1: MEASURE EVERYTHING
  // ================================
  console.log('\n=== FULL PAGE GEOMETRY ANALYSIS ===')
  const pageAnalysis = await page.evaluate(() => {
    const main = document.querySelector('main')
    if (!main) return { error: 'no main element' }
    
    const mainClasses = main.className
    const mainRect = main.getBoundingClientRect()
    
    // Document
    const docH = document.documentElement.scrollHeight
    const docW = document.documentElement.scrollWidth
    const vpH = window.innerHeight
    
    // Get ALL children of main
    const mainChildren = Array.from(main.children).map((el, i) => {
      const r = el.getBoundingClientRect()
      const cs = window.getComputedStyle(el)
      return {
        i, tag: el.tagName,
        cls: el.className.substring(0, 100),
        y: Math.round(r.y), h: Math.round(r.height), bottom: Math.round(r.bottom),
        display: cs.display,
        gap: cs.gap,
      }
    })

    // Find the main space-y-6 container
    const container = document.querySelector('main > .space-y-6') || main.querySelector('.space-y-6')
    if (!container) return { error: 'no space-y-6', mainChildren, docH, vpH }
    
    const containerRect = container.getBoundingClientRect()
    
    const kids: any[] = Array.from(container.children).map((el, i) => {
      const r = el.getBoundingClientRect()
      const cs = window.getComputedStyle(el)
      const t = (el.textContent || '').trim().substring(0, 80)
      // Recursively get child info for complex containers
      const directChildren = Array.from(el.children).map((c, j) => {
        const cr = c.getBoundingClientRect()
        const ccs = window.getComputedStyle(c)
        return {
          j, tag: c.tagName,
          cls: c.className.substring(0, 80),
          y: Math.round(cr.y), h: Math.round(cr.height), bottom: Math.round(cr.bottom),
          display: ccs.display,
          hasVisibleText: (c.textContent || '').trim().length > 0,
          isFlexContainer: ccs.display.includes('flex'),
          isGridContainer: ccs.display.includes('grid'),
        }
      })
      return {
        i, tag: el.tagName,
        cls: el.className.substring(0, 100),
        y: Math.round(r.y), h: Math.round(r.height), bottom: Math.round(r.bottom),
        display: cs.display,
        flexDirection: cs.flexDirection,
        text: t,
        children: directChildren,
      }
    })

    // Compute gaps between consecutive main children
    const gaps: number[] = []
    for (let i = 1; i < kids.length; i++) {
      gaps.push(kids[i].y - kids[i-1].bottom)
    }

    return { docH, docW, vpH, mainClasses, containerY: Math.round(containerRect.y), kids, gaps }
  })

  console.log('\n=== PAGE ANALYSIS ===')
  console.log(`Document height: ${pageAnalysis.docH}, Viewport height: ${pageAnalysis.vpH}`)
  console.log(`Main sections (${pageAnalysis.kids.length}):`)
  for (const kid of pageAnalysis.kids) {
    console.log(`  [${kid.i}] ${kid.text.substring(0, 60)} | y=${kid.y} h=${kid.h} bottom=${kid.bottom} | display=${kid.display}`)
    if (kid.children.length > 1) {
      for (const c of kid.children) {
        console.log(`    child ${c.j}: ${c.cls.substring(0, 50)} | y=${c.y} h=${c.h} bottom=${c.bottom} | display=${c.display} flex=${c.isFlexContainer} grid=${c.isGridContainer}`)
      }
    }
  }
  console.log(`Gaps between sections: ${JSON.stringify(pageAnalysis.gaps)}`)

  // Spot empty space > 50px
  const bigGaps: { from: any; to: any; gap: number }[] = []
  for (let i = 1; i < pageAnalysis.kids.length; i++) {
    const gap = pageAnalysis.kids[i].y - pageAnalysis.kids[i-1].bottom
    if (gap > 50) {
      bigGaps.push({ from: pageAnalysis.kids[i-1], to: pageAnalysis.kids[i], gap })
    }
  }
  console.log(`\nLarge gaps (>50px): ${bigGaps.length}`)
  for (const bg of bigGaps) {
    console.log(`  ${bg.gap}px gap between section [${bg.from.i}] and [${bg.to.i}]`)
    console.log(`    Above: "${bg.from.text.substring(0, 60)}"`)
    console.log(`    Below: "${bg.to.text.substring(0, 60)}"`)
  }

  // ================================
  // PHASE 2: DEEP DIVE INTO TWO-COL LAYOUT
  // ================================
  const twoColAnalysis = await page.evaluate(() => {
    const twoCols = document.querySelectorAll('.flex.flex-col.lg\\:flex-row.gap-6.items-start')
    console.log('TWO-COL LAYOUTS:', twoCols.length)
    const results: any[] = []
    twoCols.forEach((tc, ti) => {
      const children = Array.from(tc.children)
      const colInfo = children.map((col, ci) => {
        const r = col.getBoundingClientRect()
        const cs = window.getComputedStyle(col)
        const colChildren = Array.from(col.children).map((item, ii) => {
          const ir = item.getBoundingClientRect()
          const ics = window.getComputedStyle(item)
          return {
            ii, tag: item.tagName,
            cls: item.className.substring(0, 80),
            y: Math.round(ir.y), h: Math.round(ir.height), bottom: Math.round(ir.bottom),
            text: (item.textContent || '').trim().substring(0, 60),
            display: ics.display,
            marginTop: ics.marginTop,
            marginBottom: ics.marginBottom,
            paddingTop: ics.paddingTop,
            paddingBottom: ics.paddingBottom,
          }
        })
        const gaps: number[] = []
        for (let i = 1; i < colChildren.length; i++) {
          const actualGap = colChildren[i].y - colChildren[i-1].bottom
          gaps.push(actualGap)
        }
        return {
          ci,
          y: Math.round(r.y), h: Math.round(r.height), bottom: Math.round(r.bottom),
          w: Math.round(r.width),
          display: cs.display,
          flexDirection: cs.flexDirection,
          gap: cs.gap,
          alignItems: cs.alignItems,
          scrollHeight: col.scrollHeight,
          clientHeight: col.clientHeight,
          colChildren, gaps,
        }
      })
      results.push({ ti, children: colInfo })
    })
    return results
  })

  console.log('\n=== TWO-COLUMN ANALYSIS ===')
  for (const tc of twoColAnalysis) {
    for (const col of tc.children) {
      console.log(`\nColumn ${col.ci}: y=${col.y} h=${col.h} w=${col.w} display=${col.display} direction=${col.flexDirection} gap=${col.gap}`)
      console.log(`  scrollHeight=${col.scrollHeight} clientHeight=${col.clientHeight}`)
      console.log(`  Children (${col.colChildren.length}):`)
      for (const c of col.colChildren) {
        console.log(`    [${c.ii}] ${c.text.substring(0, 50)} | y=${c.y} h=${c.h} bottom=${c.bottom} | mt=${c.marginTop} mb=${c.marginBottom} pt=${c.paddingTop} pb=${c.paddingBottom}`)
      }
      console.log(`  Internal gaps: ${JSON.stringify(col.gaps)}`)
      if (col.colChildren.length > 0) {
        const firstTop = col.colChildren[0].y
        const lastBottom = col.colChildren[col.colChildren.length - 1].bottom
        const internalHeight = lastBottom - firstTop
        console.log(`  Internal content height: ${internalHeight}px`)
        console.log(`  Container height: ${col.h}px`)
        console.log(`  Extra space in container: ${col.h - internalHeight}px`)
      }
    }
  }

  // ================================
  // PHASE 3: FIND THE ACTUAL EMPTY REGION
  // ================================
  const emptyRegions = await page.evaluate(() => {
    const results: { y: number; h: number; from: string; to: string }[] = []
    // Scan entire page for elements
    const allElements = document.querySelectorAll('main *')
    const positions: { y: number; bottom: number; label: string; el: Element }[] = []
    allElements.forEach(el => {
      const r = el.getBoundingClientRect()
      const w = Math.round(r.width)
      const h = Math.round(r.height)
      // Only visible elements with some width/height
      if (h > 0 && w > 50 && r.left < 1400) {
        const text = (el.textContent || '').trim().substring(0, 40)
        const hasVisibleContent = text.length > 0 || 
          el.querySelector('img') || 
          el.querySelector('svg') ||
          el.querySelector('canvas')
        if (hasVisibleContent || h > 30) {
          positions.push({ y: r.top + window.scrollY, bottom: r.bottom + window.scrollY, label: text, el })
        }
      }
    })
    
    // Sort by y
    positions.sort((a, b) => a.y - b.y)
    
    // Look for gaps
    for (let i = 1; i < positions.length; i++) {
      const gap = positions[i].y - positions[i-1].bottom
      if (gap > 50) {
        results.push({ 
          y: positions[i-1].bottom, 
          h: gap,
          from: positions[i-1].label,
          to: positions[i].label,
        })
      }
    }
    results.sort((a, b) => b.h - a.h)
    return results.slice(0, 20)
  })

  console.log('\n=== TOP 20 EMPTY REGIONS (>50px) ===')
  for (const er of emptyRegions) {
    console.log(`  Gap at y=${er.y}: ${er.h}px between "${er.from.substring(0, 40)}" and "${er.to.substring(0, 40)}"`)
  }

  // ================================
  // PHASE 4: SCROLL CAPTURE
  // ================================
  console.log('\n=== SCROLL CAPTURE SEQUENCE ===')
  await page.screenshot({ path: '../test-results/dashboard-fullpage-before.png', fullPage: true })
  console.log('Captured: fullpage-before')

  // Capture at multiple scroll positions
  const scrollPositions = [0, 400, 800, 1200, 1600, 2000, 2500]
  for (const pos of scrollPositions) {
    if (pos < pageAnalysis.docH - 768) {
      await page.evaluate((p) => window.scrollTo(0, p), pos)
      await page.waitForTimeout(300)
      await page.screenshot({ path: `../test-results/dashboard-scroll-${String(pos).padStart(3,'0')}.png`, fullPage: false })
      console.log(`  scrollY=${pos}: captured`)
    }
  }

  // Scroll to bottom
  await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight))
  await page.waitForTimeout(300)
  await page.screenshot({ path: '../test-results/dashboard-scroll-bottom.png', fullPage: false })
  console.log('  scrollY=bottom: captured')

  // Scroll back to top
  await page.evaluate(() => window.scrollTo(0, 0))
  await page.waitForTimeout(500)

  // Keep browser open for manual inspection
  console.log('\n=== BROWSER OPEN FOR MANUAL INSPECTION ===')
  console.log('Holding browser open for 15 seconds...')
  await page.waitForTimeout(15000)

  // ================================
  // SUMMARY
  // ================================
  console.log('\n=== GAP ANALYSIS SUMMARY ===')
  console.log(`Page height: ${pageAnalysis.docH}px`)
  console.log(`Viewport height: ${pageAnalysis.vpH}px`)
  if (bigGaps.length > 0) {
    console.log(`BIG GAPS FOUND: ${bigGaps.length}`)
    for (const bg of bigGaps) {
      console.log(`  ${bg.gap}px: "${bg.from.text.substring(0, 30)}" → "${bg.to.text.substring(0, 30)}"`)
    }
  } else {
    console.log('NO BIG GAPS BETWEEN MAIN SECTIONS')
  }

  // Two-column analysis
  for (const tc of twoColAnalysis) {
    for (const col of tc.children) {
      if (col.colChildren.length > 0) {
        const first = col.colChildren[0]
        const last = col.colChildren[col.colChildren.length - 1]
        const contentSpan = last.bottom - first.y
        const containerH = col.h
        const extra = containerH - contentSpan
        if (extra > 50) {
          console.log(`Column ${col.ci} has ${extra}px extra vertical space (content=${contentSpan}px in container=${containerH}px)`)
        }
      }
    }
  }

  if (emptyRegions.length > 0) {
    console.log(`Largest empty region: ${emptyRegions[0].h}px`)
  }

  console.log(`\nPage errors: ${errors.length}`)
})
