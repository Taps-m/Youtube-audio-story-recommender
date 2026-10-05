const {chromium}=require('C:/Users/dasta/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});const page=await browser.newPage();
 await page.goto('http://127.0.0.1:8082/');await page.waitForSelector('#favorites .card');
 const catalog=await (await page.request.get('http://127.0.0.1:8082/__private/catalog')).json();
 assert(!(await page.locator('#duration').isDisabled()));
 for(const [value,valid] of [['medium',n=>n>=30&&n<=60],['long',n=>n>60]]){
  await page.selectOption('#duration',value);
  const ids=await page.locator('.card').evaluateAll(cards=>cards.map(c=>c.dataset.video));
  assert(ids.length>0,'Duration filter must return real results');
  for(const id of ids)assert(valid(catalog.find(s=>s.video_id===id).duration_minutes));
  console.log(value+': '+ids.length+' displayed stories, all within the selected interval.');
 }
 assert(!(await page.content()).includes('Unverified durations are excluded'));
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
