import { test, expect } from '@playwright/test';
import path from 'path';
import fs from 'fs';

test('Full QA Verification', async ({ browser }) => {
  test.setTimeout(300000); // 5 minutes max
  const context = await browser.newContext();
  const page = await context.newPage();

  const uid = Date.now();
  const email = `qa_user_${uid}@example.com`;
  const pwd = 'QaPassword123!';
  const results = {};

  const reportError = (phase, msg) => {
    console.error(`[ERROR][${phase}] ${msg}`);
    if (!results[phase]) results[phase] = { errors: [] };
    results[phase].errors.push(msg);
  };
  const log = (phase, msg) => {
    console.log(`[INFO][${phase}] ${msg}`);
  };

  // 1. Landing Page
  log('LANDING', 'Checking landing page...');
  await page.goto('http://localhost:3000/');
  await page.waitForTimeout(1000);
  await page.screenshot({ path: '../test-results/qa_landing.png' });

  // 2. Auth / Register
  log('AUTH', 'Registering new QA user...');
  await page.goto('http://localhost:3000/register');
  await page.fill('#register-email', email);
  await page.fill('#register-password', pwd);
  await page.fill('#register-confirm', pwd);
  await page.click('button[type="submit"]');
  await page.waitForURL('**/dashboard**', { timeout: 30000 });
  await page.waitForTimeout(2000);
  log('AUTH', 'Registration successful. State A - New User.');

  // 3. STATE A - Empty User Dashboard
  await page.screenshot({ path: '../test-results/qa_dashboard_empty.png' });
  const dashboardText = await page.textContent('body');
  if (dashboardText.includes('Failed to fetch') || dashboardText.includes('Retry')) {
    reportError('DASHBOARD_EMPTY', 'Found Failed to fetch or Retry on new user dashboard');
  }

  // 4. Goals CRUD
  log('GOALS', 'Testing Goals CRUD...');
  await page.goto('http://localhost:3000/goals');
  await page.waitForTimeout(1500);
  
  // Validation check
  const addGoalBtn = page.getByRole('button', { name: /add goal/i }).first();
  if (await addGoalBtn.isVisible()) {
    await addGoalBtn.click();
    await page.waitForTimeout(1000);
    await page.getByRole('button', { name: /create goal/i }).click();
    await page.waitForTimeout(500);
    if (await page.locator('.text-error, .text-red, .text-destructive, [role="alert"]').count() === 0) {
      reportError('GOALS', 'Required validation failed (no error shown for blank submission)');
    }
    
    // Valid creation
    await page.fill('input[id="title"]', `QA_GOAL_${uid}`);
    await page.getByRole('button', { name: /create goal/i }).click();
    await page.waitForTimeout(1500);
    const goalsText = await page.textContent('body');
    if (!goalsText.includes(`QA_GOAL_${uid}`)) {
       reportError('GOALS', 'Goal creation failed, title not found on page');
    }
  } else {
    reportError('GOALS', 'Add goal button not found');
  }
  await page.screenshot({ path: '../test-results/qa_goals.png' });

  // 5. Tasks CRUD
  log('TASKS', 'Testing Tasks CRUD...');
  await page.goto('http://localhost:3000/tasks');
  await page.waitForTimeout(1500);
  const addTaskBtn = page.getByRole('button', { name: /add task/i }).first();
  if (await addTaskBtn.isVisible()) {
    await addTaskBtn.click();
    await page.waitForTimeout(500);
    await page.fill('input[id="title"]', `QA_TASK_${uid}`);
    await page.getByRole('button', { name: /create task/i }).click();
    await page.waitForTimeout(1500);
    const tasksText = await page.textContent('body');
    if (!tasksText.includes(`QA_TASK_${uid}`)) {
       reportError('TASKS', 'Task creation failed, title not found on page');
    }
  } else {
    reportError('TASKS', 'Add task button not found');
  }
  await page.screenshot({ path: '../test-results/qa_tasks.png' });

  // 6. Food Diary
  log('FOOD_DIARY', 'Testing Food Diary...');
  await page.goto('http://localhost:3000/nutrition');
  await page.waitForTimeout(1500);
  await page.screenshot({ path: '../test-results/qa_food_diary.png' });

  // 7. Weight Tracker
  log('WEIGHT', 'Testing Weight Tracker...');
  await page.goto('http://localhost:3000/body-weight');
  await page.waitForTimeout(1500);
  await page.screenshot({ path: '../test-results/qa_weight.png' });

  // 8. Import JSON (State E)
  log('IMPORT', 'Testing JSON Import...');
  await page.goto('http://localhost:3000/settings');
  await page.waitForTimeout(1500);
  const dataCenterTab = page.getByRole('tab', { name: /data center/i });
  if (await dataCenterTab.isVisible()) {
    await dataCenterTab.click();
    await page.waitForTimeout(1000);
  }
  
  const jsonPath = path.resolve(__dirname, '../test-import.json');
  try {
    const fileInput = await page.waitForSelector('input[accept=".json,.csv,.txt"]', { state: 'attached', timeout: 5000 });
    if (fileInput) {
      await fileInput.setInputFiles(jsonPath);
      const importBtn = page.getByRole('button', { name: /import data/i });
      if (await importBtn.isVisible()) {
         await importBtn.click();
         await page.waitForTimeout(4000);
      }
    }
  } catch (e) {
    reportError('IMPORT', 'File input not found or import failed');
  }

  // 9. Verify Post-Import Stability
  log('POST_IMPORT', 'Verifying pages after import...');
  
  await page.goto('http://localhost:3000/tasks');
  await page.waitForTimeout(2000);
  let pageText = await page.textContent('body');
  if (pageText.includes('Failed to fetch') || pageText.includes('Could not load tasks')) {
    reportError('POST_IMPORT_TASKS', 'Failed to fetch tasks after import');
  }

  await page.goto('http://localhost:3000/goals');
  await page.waitForTimeout(2000);
  pageText = await page.textContent('body');
  if (pageText.includes('Failed to fetch')) {
    reportError('POST_IMPORT_GOALS', 'Failed to fetch goals after import');
  }

  await page.goto('http://localhost:3000/dashboard');
  await page.waitForTimeout(3000);
  await page.screenshot({ path: '../test-results/qa_dashboard_populated.png' });
  pageText = await page.textContent('body');
  if (pageText.includes('Failed to fetch')) {
    reportError('POST_IMPORT_DASHBOARD', 'Failed to fetch on populated dashboard');
  }

  // 10. AI Coach & Food Recognition smoke load
  log('AI_COACH', 'Testing AI Coach...');
  await page.goto('http://localhost:3000/ai-coach');
  await page.waitForTimeout(2000);
  await page.screenshot({ path: '../test-results/qa_ai_coach.png' });
  
  // 11. Responsive checks
  log('RESPONSIVE', 'Testing mobile viewport...');
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto('http://localhost:3000/dashboard');
  await page.waitForTimeout(2000);
  await page.screenshot({ path: '../test-results/qa_mobile_dashboard.png' });

  // 12. Final Report Output
  console.log('=== QA_RESULTS_JSON_START ===');
  console.log(JSON.stringify(results, null, 2));
  console.log('=== QA_RESULTS_JSON_END ===');

  await context.close();
});
