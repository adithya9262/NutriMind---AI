import { test } from '@playwright/test'
import path from 'path'

test('Debug goals form', async ({ page }) => {
  test.setTimeout(120000)

  const uid = Date.now()
  await page.goto('/register', { waitUntil: 'networkidle' })
  await page.waitForTimeout(1000)
  await page.fill('#register-email', `debug_${uid}@example.com`)
  await page.fill('#register-password', 'TestPass123!')
  await page.fill('#register-confirm', 'TestPass123!')
  await page.click('button[type="submit"]')
  await page.waitForURL('**/dashboard**', { timeout: 30000 })

  await page.goto('/goals', { waitUntil: 'networkidle', timeout: 30000 })
  await page.waitForTimeout(3000)
  await page.screenshot({ path: path.join(process.cwd(), 'debug-a.png'), fullPage: true })
  
  const btn = page.getByRole('button', { name: /add goal/i })
  console.log('Add Goal btn visible:', await btn.isVisible())
  console.log('Add Goal btn text:', await btn.textContent())
  await btn.click()
  await page.waitForTimeout(2000)
  await page.screenshot({ path: path.join(process.cwd(), 'debug-b.png'), fullPage: true })

  const titleInput = page.locator('#title')
  console.log('#title visible:', await titleInput.isVisible())
  if (await titleInput.isVisible()) {
    await titleInput.fill('Test Goal')
    await page.waitForTimeout(500)
  }
  await page.screenshot({ path: path.join(process.cwd(), 'debug-c.png'), fullPage: true })

  // List all buttons on the page
  const allBtns = page.locator('button')
  const count = await allBtns.count()
  console.log(`Total buttons: ${count}`)
  for (let i = 0; i < count; i++) {
    const txt = (await allBtns.nth(i).textContent())?.trim()
    const disabled = await allBtns.nth(i).isDisabled()
    const visible = await allBtns.nth(i).isVisible()
    console.log(`  btn[${i}] text="${txt}" disabled=${disabled} visible=${visible}`)
  }

  // Try clicking create goal
  const createBtn = page.locator('button:has-text("Create Goal")')
  console.log('Create Goal btn visible:', await createBtn.isVisible())
  console.log('Create Goal btn disabled:', await createBtn.isDisabled())
  console.log('Create Goal btn count:', await createBtn.count())
  if (await createBtn.isVisible() && !(await createBtn.isDisabled())) {
    await createBtn.click()
    await page.waitForTimeout(3000)
    await page.screenshot({ path: path.join(process.cwd(), 'debug-d.png'), fullPage: true })
  }
})
