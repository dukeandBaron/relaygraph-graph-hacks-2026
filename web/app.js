'use strict';
const $ = id => document.getElementById(id);
let state = null, proposal = null, selected = [], workspace = 'demo', busy = false;
let graphView = [0,0,1155,665];
const positions = new Map();
const typeNames = {SourceRevision:'SOURCE',Requirement:'REQUIREMENT',Task:'TASK',Person:'OWNER',Artifact:'RECORD',ReviewAction:'REVIEW',Operation:'OPERATION'};
const defaultPositions = {
  notice_v1:[95,95],notice_v2:[95,295],deadline:[315,95],registration_form:[315,245],venue:[315,475],declaration:[315,365],
  register:[540,140],travel:[775,140],catering:[1010,140],accessibility:[540,475],
  mina:[540,40],noor:[775,40],jules:[1010,40],kai:[775,475],
  ack_register:[540,275],receipt_register:[540,370],ack_travel:[775,275],ack_catering:[1010,275],ack_accessibility:[775,575]
};
function el(tag, text, cls) { const node=document.createElement(tag); if(text!==undefined)node.textContent=text; if(cls)node.className=cls; return node; }
function clearError(){ $('error').hidden=true; $('error').textContent=''; }
function showError(error){ $('error').textContent=error.message || String(error); $('error').hidden=false; }
function ready(){ return !!state?.initialized && !busy; }
function controls(){ $('preview').disabled=!ready() || state.revision!==1; $('adopt').disabled=!ready() || !proposal || !$('confirm').checked; $('seed').disabled=busy || !!state?.initialized; $('reload').disabled=busy; $('open-workspace').disabled=busy; }
async function api(path, data) {
  const response=await fetch('/api/'+path,{method:data===undefined?'GET':'POST',headers:{'Content-Type':'application/json','X-Workspace':workspace},...(data===undefined?{}:{body:JSON.stringify(data)})});
  const result=await response.json();
  if(!response.ok){ if(response.status===503){state=null;proposal=null;$('connection').className='connection offline';$('connection').textContent='Graph unavailable';renderGraph();controls();} throw new Error(result.error || 'Request could not be completed.'); }
  return result;
}
async function work(fn){ if(busy)return;busy=true;clearError();controls();try{await fn();}catch(error){showError(error);}finally{busy=false;controls();} }
async function refresh(){
  const next=await api('state');state=next;
  $('connection').className='connection online';$('connection').textContent='Graph connected';
  $('graph-title').textContent=state.initialized?state.title:'Your relationship map';
  $('revision').textContent=state.initialized?'Revision '+state.revision+' · '+state.workspace:'Empty workspace · '+state.workspace;
  if(state.initialized&&state.revision>1){const deadline=state.nodes.find(n=>n.id==='deadline'),material=state.nodes.find(n=>n.id==='declaration');if(deadline)$('deadline').value=deadline.value.slice(0,16);if(material)$('material').value=material.value;if(!$('preview-result').textContent)$('preview-result').append(el('p','This correction is already stored. Open a new workspace to replay the example.','preview-summary'));}
  renderGraph();
  if(state.initialized)renderActions((await api('actions')).actions);else renderActions([]);
  controls();
}
function svgElement(tag, attrs={}){const n=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const [k,v]of Object.entries(attrs))n.setAttribute(k,v);return n;}
function findNode(id){return state?.nodes.find(n=>n.id===id);}
function label(id){return findNode(id)?.title || id.replaceAll('_',' ');}
function selectedEdge(source,target){for(let i=0;i<selected.length-1;i++)if(selected[i]===source&&selected[i+1]===target)return true;return false;}
function renderGraph(){
  const host=$('graph');host.replaceChildren();
  if(!state?.initialized){const empty=el('div',undefined,'empty');empty.append(el('span','↳','empty-glyph'),el('h3',state?'Start with a connected example.':'Waiting for the graph.'),el('p',state?'Load a fictional activity to follow a deadline change across three dependent tasks.':'No graph data or substitute demo state is displayed while the database is unavailable.'));host.append(empty);return;}
  const svg=svgElement('svg',{viewBox:graphView.join(' '),role:'group','aria-label':'Sources, requirements, task dependencies and recorded confirmations'});
  let pan=null;
  svg.addEventListener('pointerdown',event=>{if(event.target.closest('.node'))return;const inverse=svg.getScreenCTM().inverse();const p=new DOMPoint(event.clientX,event.clientY).matrixTransform(inverse);pan={point:p,inverse,origin:[...graphView]};svg.setPointerCapture(event.pointerId);});
  svg.addEventListener('pointermove',event=>{if(!pan)return;const p=new DOMPoint(event.clientX,event.clientY).matrixTransform(pan.inverse);graphView=[pan.origin[0]-(p.x-pan.point.x),pan.origin[1]-(p.y-pan.point.y),pan.origin[2],pan.origin[3]];svg.setAttribute('viewBox',graphView.join(' '));});
  svg.addEventListener('pointerup',()=>{pan=null;});
  const defs=svgElement('defs');
  for(const hot of [false,true]){const marker=svgElement('marker',{id:hot?'arrow-hot':'arrow',viewBox:'0 0 10 10',refX:'9',refY:'5',markerWidth:'5',markerHeight:'5',orient:'auto-start-reverse'});marker.append(svgElement('path',{d:'M 0 0 L 10 5 L 0 10 z',class:hot?'edge-arrow hot':'edge-arrow'}));defs.append(marker);}svg.append(defs);
  const visible=state.nodes.filter(n=>['Person','SourceRevision','Requirement','Task','Artifact'].includes(n.kind));
  const ids=new Set(visible.map(n=>n.id));
  visible.forEach((n,i)=>{if(!positions.has(n.id))positions.set(n.id,defaultPositions[n.id] || [100+(i%5)*220,600]);});
  const edgeLayer=svgElement('g');svg.append(edgeLayer);
  function drawEdges(){edgeLayer.replaceChildren();for(const edge of state.edges){if(!ids.has(edge.source)||!ids.has(edge.target))continue;const a=positions.get(edge.source),b=positions.get(edge.target);const dx=b[0]-a[0],dy=b[1]-a[1];const distance=Math.hypot(dx,dy)||1;const isHot=selectedEdge(edge.source,edge.target);const shorten= Math.abs(dx)>Math.abs(dy)?85:31;const x1=a[0]+dx/distance*shorten,y1=a[1]+dy/distance*shorten,x2=b[0]-dx/distance*shorten,y2=b[1]-dy/distance*shorten;const path=svgElement('path',{d:`M ${x1} ${y1} L ${x2} ${y2}`,class:'edge'+(edge.type==='FOR_TASK'?' artifact-edge':'')+(isHot?' highlight':''),'marker-end':isHot?'url(#arrow-hot)':'url(#arrow)'});const title=svgElement('title');title.textContent=`${label(edge.source)} → ${edge.type} → ${label(edge.target)}`;path.append(title);edgeLayer.append(path);if(edge.type==='DEPENDS_ON'){const text=svgElement('text',{x:(x1+x2)/2,y:(y1+y2)/2-6,'text-anchor':'middle',class:'edge-label'+(isHot?' highlight':'')});text.textContent='depends on';edgeLayer.append(text);}}}
  drawEdges();
  for(const node of visible){const point=positions.get(node.id);const kind=node.kind==='SourceRevision'?'source':node.kind.toLowerCase();const group=svgElement('g',{transform:`translate(${point[0]},${point[1]})`,class:'node '+kind+(String(node.state).startsWith('needs_')?' stale':'')+(selected.includes(node.id)?' active':''),tabindex:'0',role:'button','aria-label':node.title+(node.state?', '+node.state.replaceAll('_',' '):''),'data-node':node.id});group.append(svgElement('rect',{x:'-87',y:'-30',width:'174',height:'60',rx:node.kind==='Person'?'24':'7'}));const kindText=svgElement('text',{x:'-75',y:'-12',class:'node-kind'});kindText.textContent=typeNames[node.kind];const name=svgElement('text',{x:'-75',y:'6'});name.textContent=node.title.length>26?node.title.slice(0,24)+'…':node.title;const small=svgElement('text',{x:'-75',y:'21',class:'node-kind'});small.textContent=node.kind==='Requirement'?(node.id==='deadline'?node.value.slice(5,16).replace('T',' '):node.value).slice(0,28):node.state?node.state.replaceAll('_',' '):node.synthetic?'SYNTHETIC':'';group.append(kindText,name,small);svg.append(group);
    let start=null,moved=false;
    group.addEventListener('pointerdown',event=>{const matrix=svg.getScreenCTM();const loc=new DOMPoint(event.clientX,event.clientY).matrixTransform(matrix.inverse());start={x:loc.x,y:loc.y,origin:[...positions.get(node.id)]};moved=false;group.setPointerCapture(event.pointerId);});
    group.addEventListener('pointermove',event=>{if(!start)return;const loc=new DOMPoint(event.clientX,event.clientY).matrixTransform(svg.getScreenCTM().inverse());const dx=loc.x-start.x,dy=loc.y-start.y;if(Math.abs(dx)+Math.abs(dy)>4)moved=true;const next=[Math.max(90,Math.min(1060,start.origin[0]+dx)),Math.max(32,Math.min(630,start.origin[1]+dy))];positions.set(node.id,next);group.setAttribute('transform',`translate(${next[0]},${next[1]})`);drawEdges();});
    group.addEventListener('pointerup',()=>{start=null;if(!moved)inspectNode(node);});
    group.addEventListener('keydown',event=>{if(event.key==='Enter')inspectNode(node);});
  }
  host.append(svg);$('graph-caption').textContent=`${visible.length} visible records · drag to arrange · select a task to inspect its source paths`;
}
function highlight(path){selected=path;renderGraph();}
function change(){return {deadline:$('deadline').value+':00+08:00',material:$('material').value};}
function invalidate(){proposal=null;$('preview-result').replaceChildren();$('adoption').hidden=true;$('confirm').checked=false;controls();}
function renderPreview(data){const host=$('preview-result');host.replaceChildren();host.append(el('p',`${data.tasks.length} tasks and ${data.affectedArtifacts.length} records need review.`,'preview-summary'));const seen=new Set();for(const impact of data.impacts){if(seen.has(impact.task))continue;seen.add(impact.task);const row=el('div',undefined,'impact-row'),button=el('button',undefined);button.type='button';button.append(el('span',impact.title),el('small',impact.owner+' · '+(impact.path.length-1)+' dependency hop'+(impact.path.length===2?'':'s')));button.addEventListener('click',()=>highlight(impact.path));row.append(button);host.append(row);}host.append(el('p',`${data.unaffectedTasks.length} unrelated task stays current.`,'fine'));$('adoption').hidden=false;$('confirm').checked=false;$('query-text').textContent=Object.entries(data.queries).map(([name,query])=>name.toUpperCase()+'\n'+query).join('\n\n');}
function renderActions(actions){const host=$('actions');host.replaceChildren();if(!actions.length){host.append(el('div','Adopt a reviewed correction to create persistent review actions. Unrelated work stays current.','empty-note'));return;}$('actions-heading').textContent='The work that follows this change.';for(const action of actions){const card=el('article',undefined,'action-card');card.dataset.task=action.task;card.append(el('span',action.state,'status-pill stale'),el('h3',action.taskTitle),el('div','Owner · '+action.owner,'owner'));const path=action.paths[0]||[];card.append(el('div',path.map(label).join(' → '),'path'));const button=el('button','Show the evidence path');button.type='button';button.addEventListener('click',()=>work(async()=>{document.querySelectorAll('.action-card').forEach(c=>c.classList.toggle('selected',c===card));highlight([...path,'notice_v2']);await showTask(action.task);}));card.append(button);host.append(card);}}
function evidenceShell(title){const host=$('evidence');host.hidden=false;host.replaceChildren(el('h3',title));return host;}
function showSource(node){const host=evidenceShell(node.title);host.append(el('p','An immutable synthetic source revision. Compare its original text with the current requirement version.'),el('div',node.body,'source-quote'));}
function inspectNode(node){if(node.kind==='Task'){work(()=>showTask(node.id));return;}if(node.kind==='SourceRevision'){showSource(node);return;}const host=evidenceShell(node.title);highlight([node.id]);if(node.kind==='Requirement'){host.append(el('p','Current requirement · version '+node.version),el('div',node.value,'source-quote'));for(const edge of state.edges.filter(e=>e.source===node.id&&e.type==='CITED_IN')){const source=findNode(edge.target);host.append(el('div',source.title+'\n'+source.body,'source-quote'));}}else if(node.kind==='Artifact'){host.append(el('p',node.artifactKind+' · '+node.state.replaceAll('_',' ')+' · recorded against revision '+node.basisRevision));for(const edge of state.edges.filter(e=>e.source===node.id&&e.type==='FOR_TASK')){const button=el('button','Inspect '+label(edge.target),'quiet');button.addEventListener('click',()=>work(()=>showTask(edge.target)));host.append(button);}}else if(node.kind==='Person'){host.append(el('p','Synthetic owner. Assigned work is read from the graph.'));for(const edge of state.edges.filter(e=>e.source===node.id&&e.type==='OWNS'))host.append(el('div',label(edge.target),'source-quote'));}}
async function showTask(task){const data=await api('explain/'+encodeURIComponent(task));const host=evidenceShell(label(task));host.append(el('p','These are stored graph paths and source revisions. Current requirement values are separate from the historical source text.'));const sources=new Set();for(const record of data.evidence){const line=el('div',undefined,'evidence-path');line.append(el('strong',record.title+' · current v'+record.currentVersion),el('div',record.path.map(label).join(' → '),'path'),el('p','Current value: '+record.currentValue));host.append(line);if(!sources.has(record.source)){sources.add(record.source);host.append(el('div',record.sourceTitle+'\n'+record.sourceBody,'source-quote'));}}if(!data.evidence.length)host.append(el('p','No source path exists for this task in the current workspace.'));$('query-text').textContent=data.query;}
$('reload').addEventListener('click',()=>work(refresh));
$('open-workspace').addEventListener('click',()=>work(async()=>{const name=$('workspace').value.trim();if(!/^[a-z][a-z0-9_-]{0,31}$/.test(name))throw new Error('Use a lowercase workspace name, up to 32 letters, digits, underscores or hyphens.');workspace=name;state=null;selected=[];positions.clear();invalidate();$('evidence').hidden=true;await refresh();}));
$('seed').addEventListener('click',()=>work(async()=>{await api('seed',{});await refresh();}));
$('preview').addEventListener('click',()=>work(async()=>{proposal=await api('preview',{change:change()});renderPreview(proposal);if(proposal.impacts.length)highlight(proposal.impacts[0].path);}));
$('deadline').addEventListener('input',invalidate);$('material').addEventListener('input',invalidate);$('confirm').addEventListener('change',controls);
$('adopt').addEventListener('click',()=>work(async()=>{if(!proposal||!$('confirm').checked)throw new Error('Review the current proposal before adopting it.');const result=await api('adopt',{change:proposal.change,proposal:proposal.proposal,expectedRevision:proposal.revision,operationId:'adopt_'+crypto.randomUUID().replaceAll('-',''),confirmed:true});state=result.state;proposal=null;$('adoption').hidden=true;$('preview-result').replaceChildren(el('p','Correction adopted. Review tasks are stored in the graph.','preview-summary'));$('revision').textContent='Revision '+state.revision+' · '+state.workspace;selected=[];renderGraph();renderActions(result.actions);}));
$('queries-toggle').addEventListener('click',()=>{$('queries').hidden=!$('queries').hidden;if(!$('query-text').textContent)$('query-text').textContent='Prepare a correction or select a task to inspect the actual query used.';});
function zoomGraph(factor){const width=Math.max(500,Math.min(1600,graphView[2]*factor)),height=width*665/1155;graphView=[graphView[0]+(graphView[2]-width)/2,graphView[1]+(graphView[3]-height)/2,width,height];renderGraph();}
$('zoom-in').addEventListener('click',()=>zoomGraph(.8));$('zoom-out').addEventListener('click',()=>zoomGraph(1.25));$('zoom-fit').addEventListener('click',()=>{graphView=[0,0,1155,665];renderGraph();});
work(refresh);
