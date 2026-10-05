const {chromium}=require('C:/Users/dasta/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 const page=await browser.newPage();await page.goto('http://127.0.0.1:8082/');await page.waitForSelector('#history .card');
 await page.selectOption('#genre','romance');await page.selectOption('#duration','any');
 assert.equal(await page.locator('#discoveries .card').count(),1);
 assert.equal(await page.locator('#history .card').count(),6);
 assert.equal(await page.locator('.card[data-video="IGuYKCiLxc4"]').count(),1);
 await page.selectOption('#duration','long');assert(await page.locator('.card').count()>0);
 await browser.close();console.log('Romance discovery, history separation and duration filtering passed.');
})().catch(e=>{console.error(e);process.exit(1)});
