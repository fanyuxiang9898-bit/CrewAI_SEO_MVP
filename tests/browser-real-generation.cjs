const assert=require('node:assert/strict');
const {chromium}=require(process.argv[2]);
(async()=>{
  const browser=await chromium.launch({headless:true,executablePath:process.argv[3]});
  try{
    const page=await browser.newPage({viewport:{width:1440,height:1050},acceptDownloads:true});
    const errors=[];page.on('pageerror',e=>errors.push(e.message));
    await page.goto((process.argv[4]||'http://127.0.0.1:8766')+'/#jobs');
    await page.locator('[data-new-job]').first().click();
    await page.locator('#job-keyword').fill('如何给个人笔记建立清晰的分类');
    await page.locator('#job-notes').fill('面向初学者，给出实际可执行的方法，不编造数据。');
    const responsePromise=page.waitForResponse(r=>r.url().endsWith('/api/jobs')&&r.request().method()==='POST');
    await page.locator('#job-submit').click();
    const response=await responsePromise;assert.equal(response.status(),202);
    const {job}=await response.json();console.log('Created real task:',job.id);
    await page.locator('#cancel-job').waitFor();
    await page.reload();await page.locator(`[data-job="${job.id}"]`).first().click();
    await page.waitForFunction(()=>document.querySelector('#download-job')&&document.querySelector('.job-progress').textContent.includes('3/3'),null,{timeout:900000});
    assert.equal(await page.locator('.job-output').count(),3);
    const download=page.waitForEvent('download');await page.locator('#download-job').click();
    assert.equal((await download).suggestedFilename(),`generated-${job.id}.md`);
    if(process.argv[5])await page.screenshot({path:process.argv[5],fullPage:true});
    assert.deepEqual(errors,[]);console.log('PASS: real browser submission, reload during execution, three CrewAI outputs and article download.');
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
