const assert = require('node:assert/strict');
const { chromium } = require(process.argv[2]);
(async () => {
  const browser = await chromium.launch({headless:true, executablePath:process.argv[3]});
  try {
    const page = await browser.newPage({viewport:{width:1440,height:1000},acceptDownloads:true});
    const errors=[]; page.on('pageerror',e=>errors.push(e.message));
    let job={id:'test-job',brief:{keyword:'测试 <img src=x onerror=alert(1)>',topic:'技术',notes:''},status:'running',stage:'writing',outputs:{research:'研究结果'},completed_stages:1,created_at:new Date().toISOString()};
    let creates=0, cancels=0;
    await page.route('**/api/status',r=>r.fulfill({json:{generation:{available:true,local_model:true,model:'Test model'},csrf_token:'test'}}));
    await page.route('**/api/jobs',r=>{
      if(r.request().method()==='POST'){creates++;assert.equal(r.request().headers()['x-workbench-token'],'test');return r.fulfill({status:202,json:{job}});}
      return r.fulfill({json:{jobs:creates?[job]:[]}});
    });
    await page.route('**/api/jobs/test-job/cancel',r=>{cancels++;job={...job,status:'cancelled'};return r.fulfill({json:{job}});});
    await page.goto((process.argv[4]||'http://127.0.0.1:8766')+'/#jobs');
    await page.locator('[data-new-job]').first().click();
    await page.locator('#job-keyword').fill('测试需求');
    await page.locator('#job-submit').click();
    await page.locator('#cancel-job').waitFor({timeout:10000}).catch(async e=>{console.error({creates,errors,formError:await page.locator('#job-form-error').textContent(),detail:await page.locator('#job-detail-body').textContent()});throw e;});
    assert.equal(creates,1);
    assert.match(await page.locator('.job-progress').textContent(),/1\/3/);
    assert.equal(await page.locator('#job-detail-body img').count(),0);
    page.on('dialog',d=>d.accept());
    await page.locator('#cancel-job').click();
    await page.locator('#retry-job').waitFor();
    assert.equal(cancels,1);
    await page.locator('#retry-job').click();
    assert.equal(await page.locator('#job-keyword').inputValue(),job.brief.keyword);
    await page.locator('#job-submit').click();
    await page.locator('#retry-job').waitFor();
    job={...job,status:'completed',stage:'review',outputs:{research:'研究结果',writing:'# 测试文章\n真实内容',review:'评批结果'},completed_stages:3};
    await page.locator('#download-job').waitFor({timeout:10000});
    const downloaded=page.waitForEvent('download');await page.locator('#download-job').click();
    assert.equal((await downloaded).suggestedFilename(),'generated-test-job.md');
    await page.reload();await page.locator('[data-job="test-job"]').first().click();
    await page.locator('#download-job').waitFor();
    assert.match(await page.locator('.job-progress').textContent(),/3\/3/);
    await page.keyboard.press('Escape');
    for(const width of [375,768,1440]){
      await page.setViewportSize({width,height:1000});
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,`overflow at ${width}`);
    }
    await page.setViewportSize({width:1440,height:1000});
    await page.evaluate(()=>document.body.style.zoom='2');
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,'overflow at 200%');
    assert.deepEqual(errors,[]);
    console.log('PASS: AI create, progress, escaping, cancel, retry, results download, reload persistence and responsive widths/200% zoom.');
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
