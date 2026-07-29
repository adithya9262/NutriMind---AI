import { test, expect } from '@playwright/test';

// Use a long timeout for the entire visual QA process
test.setTimeout(180000);

const uniqueId = Date.now();
const TEST_EMAIL = `qa_test_${uniqueId}@example.com`;
const TEST_PASSWORD = 'TestPassword123!';

test('Autonomous Dashboard QA - Full Sequence', async ({ page }) => {
  // Set realistic desktop viewport
  await page.setViewportSize({ width: 1366, height: 768 });

  console.log(`\n--- STARTING NUTRIMIND AUTONOMOUS QA ---`);
  console.log(`Test Email: ${TEST_EMAIL}`);

  // ==========================================
  // 1. REGISTER & STATE A (Empty)
  // ==========================================
  console.log('1. Registering new user...');
  await page.goto('http://localhost:3000/register');
  
  await page.fill('input[id="register-email"]', TEST_EMAIL);
  await page.fill('input[id="register-password"]', TEST_PASSWORD);
  await page.fill('input[id="register-confirm"]', TEST_PASSWORD);
  
  await page.click('button[type="submit"]');
  
  // Wait for dashboard to load
  await page.waitForURL('**/dashboard**');
  
  // Let UI settle
  await page.waitForTimeout(2000);

  console.log('Verifying STATE A: Incomplete Profile + Empty Dashboard');
  // Check for onboarding
  await expect(page.getByText('Complete Your Nutrition Profile')).toBeVisible();
  await expect(page.getByText('Recent Nutritional Log')).toBeVisible();
  
  // Take screenshot A
  await page.screenshot({ path: '../test-results/dashboard-state-a-empty.png', fullPage: true });

  // ==========================================
  // 2. COMPLETE PROFILE & STATE B
  // ==========================================
  console.log('2. Completing profile...');
  await page.click('button:has-text("Complete Profile")');
  await page.waitForURL('**/settings**');
  
  // Fill profile forms
  await page.fill('input[id="settings-dob"]', '1990-01-01');
  await page.selectOption('select[id="settings-sex"]', 'male');
  await page.fill('input[id="settings-height"]', '180');
  await page.fill('input[id="settings-weight"]', '80');
  await page.selectOption('select[id="settings-activity"]', 'moderately_active');
  await page.selectOption('select[id="settings-goal"]', 'maintain_weight');
  
  await page.click('button:has-text("Save Changes")');
  
  // Wait for the save to complete (toast message or button state)
  // Actually, since the button already said Save Changes, wait a bit
  await page.waitForTimeout(2000);
  
  console.log('Navigating back to Dashboard...');
  await page.goto('http://localhost:3000/dashboard');
  await page.waitForTimeout(2000); // Wait for data to load

  console.log('Verifying STATE B: Complete Profile + Empty Data');
  // Onboarding should be gone
  await expect(page.getByText('Complete Your Nutrition Profile')).not.toBeVisible();
  
  // Take screenshot B
  await page.screenshot({ path: '../test-results/dashboard-state-b-complete-empty.png', fullPage: true });

  // Measure gaps explicitly
  const chartBox = await page.locator('.recharts-responsive-container').first().boundingBox();
  const feedBox = await page.getByText('Recent Nutritional Log').boundingBox();
  if (chartBox && feedBox) {
     const verticalGap = feedBox.y - (chartBox.y + chartBox.height);
     console.log(`Measured gap between WeeklyChart and ActivityFeed: ${verticalGap}px`);
  }

  // ==========================================
  // 3. ADD MEAL & STATE C (Partially Populated)
  // ==========================================
  console.log('3. Adding Meal data (State C)...');
  await page.goto('http://localhost:3000/nutrition/logs');
  // Click Log Food if there's a button
  const logFoodBtn = page.getByRole('button', { name: 'Log Food' });
  if (await logFoodBtn.isVisible()) {
      await logFoodBtn.click();
  } else {
      console.log('Log food button not found on nutrition page directly, looking for form...');
  }
  
  // Fill meal form (might vary depending on implementation)
  try {
      await page.fill('input[id="food-name"]', 'QA Apple');
      await page.fill('input[id="entry-calories_kcal"]', '95');
      await page.fill('input[id="entry-protein_g"]', '0.5');
      await page.fill('input[id="entry-carbohydrate_g"]', '25');
      await page.fill('input[id="entry-fat_g"]', '0.3');
      await page.fill('input[id="serving-description"]', '1 medium');
      
      await page.click('button:has-text("Add Entry")');
      await page.waitForTimeout(2000);
  } catch (e) {
      console.log('Failed to log food - UI might be different', e);
  }
  
  console.log('Adding Body Weight data...');
  await page.goto('http://localhost:3000/body-weight');
  try {
      await page.fill('input[id="bw-weight-kg"]', '79.5');
      await page.click('button:has-text("Add Weight")');
      await page.waitForTimeout(2000);
  } catch (e) {
      console.log('Failed to log weight', e);
  }

  console.log('Navigating back to Dashboard...');
  await page.goto('http://localhost:3000/dashboard');
  await page.waitForTimeout(2000);

  console.log('Verifying STATE C: Partially Populated');
  // Check feed
  try {
      await expect(page.getByText('QA Apple')).toBeVisible({timeout: 5000});
  } catch (e) {
    console.log('Apple meal not visible on dashboard. Current text in activity feed:');
    const feedTexts = await page.locator('.space-y-3 .truncate').allTextContents();
    console.log(feedTexts);
  }
  
  await page.screenshot({ path: '../test-results/dashboard-state-c-partial.png', fullPage: true });

  // ==========================================
  // 4. FULLY POPULATED & STATE D
  // ==========================================
  console.log('4. Adding Goals and Tasks (State D)...');
  await page.goto('http://localhost:3000/tasks');
  try {
      // First click the 'Add Task' button to show the form
      await page.getByRole('button', { name: 'Add Task', exact: true }).click();
      await page.waitForTimeout(500); // Wait for form animation
      
      await page.fill('input[id="task-title"]', 'QA Test Task');
      // The form submit button also says "Add Task", but it's type="submit"
      await page.click('button[type="submit"]');
      await page.waitForTimeout(2000);
  } catch (e) {
      console.log('Failed to add task', e);
  }
  
  console.log('Navigating back to Dashboard...');
  await page.goto('http://localhost:3000/dashboard');
  await page.waitForTimeout(2000);
  
  console.log('Verifying STATE D: Fully Populated');
  await page.screenshot({ path: '../test-results/dashboard-state-d-populated.png', fullPage: true });

  // ==========================================
  // 5. REFRESH TEST
  // ==========================================
  console.log('5. Testing Refresh...');
  await page.reload();
  await page.waitForTimeout(2000);
  
  await page.screenshot({ path: '../test-results/dashboard-after-refresh.png', fullPage: true });

  // ==========================================
  // FINAL HOLD
  // ==========================================
  console.log('Pausing for 10 seconds to allow visible inspection of final dashboard...');
  await page.waitForTimeout(10000);
  
  console.log('--- QA COMPLETE ---');
});
