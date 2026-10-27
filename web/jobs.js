'use strict';
names.jobs = 'AI 任务';
headings.jobs = ['从一个想法，到一篇完整内容。', '创建任务，跟随研究、创作与评批的真实进度，随时回看结果。'];
const jobNav = document.createElement('a');
jobNav.href = '#jobs';
jobNav.dataset.view = 'jobs';
jobNav.innerHTML = '<span aria-hidden="true">✳</span>AI 任务';
$('nav').insertBefore(jobNav, $('nav [data-view="briefs"]'));
const launchButton = document.createElement('button');
launchButton.className = 'primary';
launchButton.dataset.newJob = '';
launchButton.textContent = '创建 AI 任务 ＋';
const oldAction = $('.page-heading [data-new-brief]');
oldAction.className = 'secondary';
const actions = document.createElement('div');
actions.className = 'heading-actions';
oldAction.replaceWith(actions);
actions.append(launchButton, oldAction);
const statusNames = { queued:'等待执行', running:'生成中', completed:'已完成', failed:'生成失败', cancelled:'已取消', interrupted:'已中断' };
const stageNames = { research:'研究方向', writing:'撰写文章', review:'评批建议' };
let generationStatus = { available:false }, csrfToken = '', jobs = [], activeJobId = null;
let submissionKey = null, submitting = false, pollTimer, previousJobs = '', previousDetail = '';

async function api(path, options={}) {
  const response = await fetch(path, options);
  let value;
  try { value = await response.json(); } catch { throw new Error('无法读取服务响应，请确认登录状态并刷新页面。'); }
  if (!response.ok) throw new Error(value.error || '请求失败，请稍后重试。');
  return value;
}

async function checkGeneration() {
  try {
    const status = await api('/api/status');
    generationStatus = status.generation;
    csrfToken = status.csrf_token;
    $('#model-status').textContent = generationStatus.available
      ? `${generationStatus.local_model?'本地模型 · 无外部 API 调用费用':'远程模型 · 使用已配置的服务额度'} · ${generationStatus.model}。任务按顺序执行。`
      : generationStatus.message;
  } catch (error) {
    generationStatus = { available:false };
    $('#model-status').textContent = error.message;
  }
}

function openJobForm(brief={}) {
  if (submitting) return;
  submissionKey = crypto.randomUUID();
  $('#job-keyword').value = brief.keyword || '';
  $('#job-topic').value = ['技术','创业','商业','工具','金融','其他'].includes(brief.topic) ? brief.topic : '其他';
  $('#job-notes').value = brief.notes || '';
  $('#job-form-error').textContent = '';
  $('#job-model-hint').textContent = generationStatus.available
    ? `使用 ${generationStatus.model}，完成研究、写作与评批三个阶段。`
    : '生成服务尚不可用，可以先保存创作草稿。';
  $('#job-submit').disabled = !generationStatus.available;
  $('#job-form-dialog').showModal();
}

async function submitJob(event) {
  event.preventDefault();
  if (submitting) return;
  const brief = {keyword:$('#job-keyword').value.trim(),topic:$('#job-topic').value,notes:$('#job-notes').value.trim()};
  if (!brief.keyword) { $('#job-form-error').textContent='请输入有效关键词。';$('#job-keyword').focus();return; }
  submitting=true;
  $('#job-submit').disabled=true;
  $('#job-submit').textContent='正在创建任务…';
  try {
    const data = await api('/api/jobs', {method:'POST',headers:{'Content-Type':'application/json','X-Workbench-Token':csrfToken,'Idempotency-Key':submissionKey},body:JSON.stringify(brief)});
    $('#job-form-dialog').close();
    location.hash='jobs';
    await refreshJobs();
    openJobDetail(data.job.id);
    notify('任务已创建，进度与结果会自动保存。');
  } catch (error) { $('#job-form-error').textContent=error.message; }
  finally { submitting=false;$('#job-submit').disabled=!generationStatus.available;$('#job-submit').textContent='提交并开始生成 ↗'; }
}

function renderJobs() {
  const serialized=JSON.stringify(jobs);
  if(serialized===previousJobs)return;
  previousJobs=serialized;
  $('#jobs-list').innerHTML=jobs.length?jobs.map(job=>`<article class="job-card"><div><span class="job-status ${escapeHTML(job.status)}">${escapeHTML(statusNames[job.status]||job.status)}</span><h3><button class="article-open" data-job="${job.id}">${escapeHTML(job.brief.keyword)}</button></h3><p>${escapeHTML(job.brief.topic)} · ${date(job.created_at)} · 已完成 ${job.completed_stages}/3 个阶段</p></div><button class="secondary" data-job="${job.id}">${job.status==='completed'?'查看结果':'查看进度'} ↗</button></article>`).join(''):'<div class="empty"><span aria-hidden="true">✳</span><h3>还没有生成任务</h3><p>创建第一项任务，或者从创作草稿开始。</p><button class="primary" data-new-job>创建 AI 任务</button></div>';
}

function renderJobDetail(job) {
  const serialized=JSON.stringify(job);
  if(serialized===previousDetail)return;
  previousDetail=serialized;
  const stages=['research','writing','review'];
  const isActive=['queued','running'].includes(job.status);
  const expanded=[...document.querySelectorAll('#job-detail-body details[open]')].map(el=>el.dataset.stage);
  $('#job-detail-body').innerHTML=`<span class="job-status ${escapeHTML(job.status)}">${statusNames[job.status]||'未知状态'}</span><h2 id="job-detail-title">${escapeHTML(job.brief.keyword)}</h2><p role="status" class="job-progress">已完成 ${job.completed_stages}/3 个阶段${job.status==='queued'?' · 正在排队':job.status==='running'?` · 正在${stageNames[job.stage]||'处理'}`:''}</p><ol class="stage-list">${stages.map(stage=>`<li class="${job.outputs[stage]?'done':job.status==='running'&&job.stage===stage?'current':''}"><span>${job.outputs[stage]?'✓':job.stage===stage&&job.status==='running'?'●':'○'}</span><strong>${stageNames[stage]}</strong><small>${job.outputs[stage]?'已完成':job.stage===stage&&job.status==='running'?'进行中':'未完成'}</small></li>`).join('')}</ol>${job.error?`<p class="error-message" role="alert">${escapeHTML(job.error)}</p>`:''}<div class="reader-actions">${isActive?'<button class="secondary" id="cancel-job">取消任务</button>':''}${['failed','cancelled','interrupted'].includes(job.status)?'<button class="primary" id="retry-job">以此需求重新创建</button>':''}${job.outputs.writing?'<button class="primary" id="download-job">导出文章 Markdown ↗</button>':''}</div>${stages.filter(stage=>job.outputs[stage]).map(stage=>`<details class="job-output" data-stage="${stage}" ${expanded.includes(stage)||(stage==='writing'&&!expanded.length)?'open':''}><summary>${stageNames[stage]}</summary><div class="article-content">${escapeHTML(job.outputs[stage])}</div></details>`).join('')}`;
  if($('#cancel-job'))$('#cancel-job').onclick=async()=>{
    if(!confirm('确定取消当前任务吗？已完成的阶段结果会保留。'))return;
    try{await api(`/api/jobs/${job.id}/cancel`,{method:'POST',headers:{'Content-Type':'application/json','X-Workbench-Token':csrfToken},body:'{}'});await refreshJobs();}catch(error){notify(error.message);}
  };
  if($('#retry-job'))$('#retry-job').onclick=()=>{$('#job-detail-dialog').close();openJobForm(job.brief);};
  if($('#download-job'))$('#download-job').onclick=()=>download(job.outputs.writing,`generated-${job.id}.md`);
}

function openJobDetail(identifier) {
  activeJobId=identifier;previousDetail='';
  const job=jobs.find(job=>job.id===identifier);
  if(job)renderJobDetail(job);
  else $('#job-detail-body').innerHTML='<h2 id="job-detail-title">正在读取任务…</h2>';
  if(!$('#job-detail-dialog').open)$('#job-detail-dialog').showModal();
  refreshJobs();
}

async function refreshJobs() {
  clearTimeout(pollTimer);
  try {
    const data=await api('/api/jobs');jobs=data.jobs;
    $('#jobs-state').textContent='';renderJobs();
    if(activeJobId&&$('#job-detail-dialog').open){const job=jobs.find(job=>job.id===activeJobId);if(job)renderJobDetail(job);}
  } catch(error) {
    $('#jobs-state').textContent=`${error.message} 将自动重试；已创建的任务不会重复提交。`;
  } finally {
    if(location.hash==='#jobs'||$('#job-detail-dialog').open)pollTimer=setTimeout(refreshJobs,2000);
  }
}

function jobViewChanged(){
  $('#jobs-panel').hidden=location.hash!=='#jobs';
  if(!$('#jobs-panel').hidden){checkGeneration();refreshJobs();}
  else if(!$('#job-detail-dialog').open)clearTimeout(pollTimer);
}

document.addEventListener('click',event=>{
  const target=event.target.closest('button');if(!target)return;
  if(target.hasAttribute('data-new-job'))openJobForm();
  if(target.dataset.job)openJobDetail(target.dataset.job);
  if(target.dataset.runBrief){const brief=briefs.find(b=>b.id===target.dataset.runBrief);if(brief)openJobForm(brief);}
});
$('#job-form').addEventListener('submit',submitJob);
$('#job-form-dialog').addEventListener('cancel',event=>{if(submitting)event.preventDefault();});
$('#job-detail-dialog').addEventListener('close',()=>{activeJobId=null;previousDetail='';jobViewChanged();});
window.addEventListener('hashchange',jobViewChanged);
window.addEventListener('visibilitychange',()=>{if(!document.hidden){checkGeneration();jobViewChanged();}});
checkGeneration();navigate();jobViewChanged();
