import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';

test.setTimeout(120000);

test('Final Verification Run', async ({ page }) => {
  const uid = Date.now();
  const email = `verify_${uid}@example.com`;
  const pwd = 'TestPassword123!';

  console.log('=== REGISTER ===');
  await page.goto('http://localhost:3000/register');
  await page.fill('#register-email', email);
  await page.fill('#register-password', pwd);
  await page.fill('#register-confirm', pwd);
  await page.click('button[type="submit"]');
  await page.waitForURL('**/dashboard**', { timeout: 30000 });
  await page.waitForTimeout(2000);

  console.log('=== PHASE 5: VALIDATION CHECK ===');
  await page.goto('http://localhost:3000/goals');
  await page.waitForTimeout(2000);
  
  // Open create goal
  const addGoalBtn = page.getByRole('button', { name: /add goal/i });
  if (await addGoalBtn.isVisible()) {
    await addGoalBtn.click();
    await page.waitForTimeout(1000);
    
    // Fill title
    await page.fill('input[id="title"]', 'Validation Test');
    
    // Change type of target_calories to text so we can input invalid string
    await page.evaluate(() => {
      const el = document.getElementById('target_calories');
      if (el) el.setAttribute('type', 'text');
    });
    await page.fill('input[id="target_calories"]', 'invalid_abc');
    
    // Submit
    await page.getByRole('button', { name: 'Create Goal' }).click();
    await page.waitForTimeout(2000);
    
    // Look for error
    const errors = await page.locator('.text-error, .text-red, .text-destructive, [role="alert"]').allTextContents();
    console.log('Validation Errors found:', errors);
    
    await page.screenshot({ path: '../test-results/validation_check.png' });
  }

  console.log('=== PHASE 8: IMPORT REGRESSION ===');
  await page.goto('http://localhost:3000/settings');
  await page.waitForTimeout(2000);
  
  // Click Data Center tab if not active
  const dataCenterTab = page.getByRole('tab', { name: /data center/i });
  if (await dataCenterTab.isVisible()) {
    await dataCenterTab.click();
    await page.waitForTimeout(1000);
  }
  
  const jsonPath = path.resolve(__dirname, '../test-import.json');
  console.log('JSON Path:', jsonPath);
  
  try {
    const fileInput = await page.waitForSelector('input[accept=".json,.csv,.txt"]', { state: 'attached', timeout: 10000 });
    if (fileInput) {
      await fileInput.setInputFiles(jsonPath);
      console.log('File set. Waiting for import to complete...');
      
      const importBtn = page.getByRole('button', { name: /import data/i });
      if (await importBtn.isVisible()) {
         await importBtn.click();
      }
      
      await page.waitForTimeout(4000);
    }
  } catch (e) {
    console.log('COULD NOT FIND FILE INPUT:', e);
  }

  // Verify Tasks
  console.log('Checking Tasks after import...');
  await page.goto('http://localhost:3000/tasks');
  await page.waitForTimeout(3000);
  
  const fetchError = await page.getByText(/Failed to fetch|Retry/i).isVisible();
  console.log('Tasks Failed to fetch error:', fetchError);
  
  const tasks = await page.locator('div.task-card, div.rounded-lg.border, div.bg-card').allTextContents();
  console.log('Found Tasks count:', tasks.length);

  await page.screenshot({ path: '../test-results/tasks_after_import.png' });

  // Verify Goals
  console.log('Checking Goals after import...');
  await page.goto('http://localhost:3000/goals');
  await page.waitForTimeout(2000);
  await page.screenshot({ path: '../test-results/goals_after_import.png' });

  console.log('=== PHASE 7: SMOKE TEST ===');
  const urls = ['/', '/dashboard', '/goals', '/tasks', '/settings'];
  for (const u of urls) {
     const res = await page.goto(`http://localhost:3000${u}`);
     console.log(`Smoke Load ${u}: ${res?.status()}`);
     await page.waitForTimeout(1000);
  }

  console.log('=== PHASE 12: RESPONSIVE ===');
  await page.setViewportSize({ width: 375, height: 812 });
  for (const u of ['/goals', '/tasks', '/settings']) {
     await page.goto(`http://localhost:3000${u}`);
     await page.waitForTimeout(1000);
     await page.screenshot({ path: `../test-results/mobile_${u.replace('/', '')}.png` });
     console.log(`Mobile ${u} loaded`);
  }
  
  console.log('=== DONE ===');
});
