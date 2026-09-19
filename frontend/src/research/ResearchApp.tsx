import React, {useEffect, useMemo, useState} from 'react';
import {Bot, Camera, Monitor, Mic2, CircleDot, FlaskConical, Undo2, Hand} from 'lucide-react';
import './research.css';

const API='http://localhost:8000';
const researcher=new URLSearchParams(location.search).get('view')!=='participant';
type Condition='manual'|'assistive'|'autonomous';
type State=any;

async function post(path:string, body?:any){
  const r=await fetch(API+path,{method:'POST',headers:{'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body)});
  if(!r.ok) throw new Error(await r.text());
  return r.json();
}

function Pill({children,kind='neutral'}:{children:React.ReactNode,kind?:string}){return <span className={'pill '+kind}>{children}</span>}

function Feedback(){
  const [saved,setSaved]=useState(false);
  if(saved) return <p>Thank you. Your feedback has been recorded.</p>;
  return <form onSubmit={async e=>{e.preventDefault();const f=new FormData(e.currentTarget);await post('/api/study/feedback',{
    perceived_control:Number(f.get('perceived_control')),trust:Number(f.get('trust')),workload:Number(f.get('workload')),
    delegation_preferences:Object.fromEntries(['camera','display','audio','recording'].map(k=>[k,f.get(k)])),notes:f.get('notes')});setSaved(true)}}>
    <h3>Post-condition feedback</h3>
    <p>Rate your experience from 1 (very low) to 7 (very high).</p>
    {['perceived_control','trust','workload'].map(k=><label key={k}>{k.replaceAll('_',' ')} <select name={k} required defaultValue=""><option value="" disabled>Select</option>{[1,2,3,4,5,6,7].map(n=><option key={n}>{n}</option>)}</select></label>)}
    <p>How would you prefer to delegate each AV capability?</p>
    {['camera','display','audio','recording'].map(k=><label key={k}>{k==='display'?'Display/source':k} <select required name={k} defaultValue=""><option value="" disabled>Select</option><option value="manual">Manual</option><option value="assistive">Assistive</option><option value="autonomous">Autonomous</option></select></label>)}
    <label>Comments <textarea name="notes" maxLength={2000}/></label><button type="submit">Save feedback</button>
  </form>;
}

export default function ResearchApp(){
  const [state,setState]=useState<State|null>(null);
  const [recommendation,setRecommendation]=useState<any>(null);
  const [config,setConfig]=useState<any>({scenarios:[]});
  const [research,setResearch]=useState(true);
  const [busy,setBusy]=useState(false);
  const [order,setOrder]=useState(0);
  const [position,setPosition]=useState(0);
  const [error,setError]=useState('');
  useEffect(()=>{const handler=(event:PromiseRejectionEvent)=>{event.preventDefault();setError(String(event.reason))};window.addEventListener('unhandledrejection',handler);return()=>window.removeEventListener('unhandledrejection',handler)},[]);

  const refresh=async()=>{const d=await fetch(API+'/api/state').then(r=>r.json());setState(d.state);setRecommendation(d.recommendation)};
  useEffect(()=>{refresh();fetch(API+'/api/config?researcher='+researcher).then(r=>r.json()).then(setConfig);const id=setInterval(refresh,750);return()=>clearInterval(id)},[]);
  if(!state) return <div className="loading">Connecting to classroom brain…</div>;

  const participant=(config.participant_view!==false || Boolean(state.study)) && !researcher;
  const showResearch=research && !participant;
  const condition:Condition=state.condition;
  const inject=async(name:string)=>{setBusy(true);try{await post('/api/scenario/'+name+(config.profile==='study'?'?realtime=true':''));await refresh()}finally{setBusy(false)}};
  const conditionSet=async(c:Condition)=>{await post('/api/condition',{condition:c});await refresh()};
  const manual=async(tool:string,args:any)=>{await post('/api/manual/action',{action:{tool,args,reason:'Participant manual control',confidence:1}});await refresh()};

  const statusColor=state.activity.confidence>.9?'good':state.activity.confidence>.7?'warn':'bad';
  return <div className="app">
    <header><div><h1>Agentic Classroom</h1><p>Local AV control research prototype</p></div><div className="headerRight"><Pill kind={condition}>Study condition: {condition.toUpperCase()}</Pill>{!participant && <><Pill>Runtime: {config.runtime||'?'}</Pill><Pill>Agent: {config.agent_backend==='ollama'?'QWEN':(config.agent_backend||'?').toUpperCase()}</Pill><button className="ghost" onClick={()=>setResearch(!research)}><FlaskConical size={16}/> Research Console</button></>}</div></header>

    {error && <p role="alert">{error} <button onClick={()=>setError('')}>Dismiss</button></p>}
    <main className={showResearch?'grid withResearch':'grid'}>
      <section className="panel classroom">
        <div className="panelTitle">Classroom</div>
        <div className="room">
          <div className="board">PRESENTATION</div>
          <div className={'person instructor '+(['presenter','instructor'].includes(state.observations.active_speaker)?'speaking':'')}>PRESENTER</div>
          <div className="cameraIcon"><Camera size={22}/> {state.devices.camera_target}</div>
        </div>
        <div className="manualControls">
          {state.study && <div className="studyTask"><h3>Teaching task {state.study.task_index+1} of 14</h3><p>{state.study.instruction||'Wait for the facilitator to begin.'}</p>
            {!state.study.completed && state.study.task_index>=0 && <button onClick={()=>post('/api/study/complete',{outcome:'completed'}).then(refresh)}>Mark task complete</button>}
            {state.study.finished && <Feedback key={state.study.run_id}/>}
          </div>}
          <h3>Participant AV Controls</h3>
          <div className="buttonRow"><button onClick={()=>manual('audio_set_mode',{mode:'lecture'})}>Speech audio</button><button onClick={()=>manual('audio_set_mode',{mode:'media'})}>Video audio</button></div>
          <div className="buttonRow"><button onClick={()=>manual('camera_focus',{target:'presenter'})}>Camera: Presenter</button><button onClick={()=>manual('camera_focus',{target:'wide'})}>Camera: Wide</button><button onClick={()=>manual('camera_focus',{target:'demo_zone'})}>Camera: Demo area</button></div>
          <div className="buttonRow"><button onClick={()=>manual('display_set_source',{source:'presentation'})}>Slides</button><button onClick={()=>manual('display_set_source',{source:'camera'})}>Camera to Display</button><button onClick={()=>manual('display_set_source',{source:'room_pc'})}>Other application</button></div>
          <div className="buttonRow"><button onClick={()=>manual('recording_start',{})}>Record</button><button onClick={()=>manual('recording_stop',{})}>Stop</button>{['slides_plus_instructor','demo_primary','media_primary','wide'].map(layout=><button key={layout} onClick={()=>manual('recording_set_layout',{layout})}>{layout.replaceAll('_',' ')}</button>)}</div>
        </div>
      </section>

      <section className="panel statePanel">
        <div className="panelTitle">Room State</div>
        {!participant && <dl><dt>Session</dt><dd>{state.session}</dd><dt>Activity</dt><dd>{state.activity.state} <Pill kind={statusColor}>{Math.round(state.activity.confidence*100)}%</Pill></dd><dt>Active speaker</dt><dd>{state.observations.active_speaker}</dd><dt>Transcript</dt><dd className="transcript">{state.observations.transcript||'—'}</dd><dt>Evidence</dt><dd>{state.activity.evidence.join(' · ')||'—'}</dd></dl>}
        <div className="deviceGrid"><div><Camera/> <b>Camera</b><span>{state.devices.camera_target}</span></div><div><Monitor/> <b>Display</b><span>{state.devices.display_source}</span></div><div><Mic2/> <b>Audio</b><span>{state.devices.audio_mode}</span></div><div><CircleDot/> <b>Recording</b><span>{state.devices.recording?'REC':'OFF'} · {state.devices.recording_layout}</span></div></div>
      </section>

      <section className="panel agentPanel">
        <div className="panelTitle"><Bot size={18}/> Agent</div>
        {condition==='manual' && <div className="agentMessage muted"><b>Manual condition.</b><br/>The AI does not recommend or execute AV changes.</div>}
        {condition==='assistive' && !recommendation && <div className="agentMessage">Recommendations appear when the classroom activity changes.</div>}
        {condition==='autonomous' && <div className="agentMessage"><b>Autonomous authority active.</b><br/>Validated agent actions execute immediately.</div>}
        {recommendation && <div className="recommend"><h3>AI Recommendation</h3><p>{recommendation.decision.rationale}</p>{recommendation.decision.actions.map((a:any,i:number)=><div className="action" key={i}><b>{a.tool.replaceAll('_',' ')}</b><span>{Object.values(a.args).map(String).join(' · ')}</span></div>)}<div className="buttonRow"><button className="primary" onClick={async()=>{await post('/api/recommendation/apply');refresh()}}>Apply</button><button onClick={async()=>{await post('/api/recommendation/dismiss');refresh()}}>Dismiss</button></div></div>}
        {condition!=='manual' && <div className="override"><button onClick={async()=>{await post('/api/override',{mode:'undo',capability:'all'});refresh()}}><Undo2 size={16}/> Undo last AV action</button><button className="danger" onClick={async()=>{await post('/api/override',{mode:'manual',capability:'all'});refresh()}}><Hand size={16}/> Take Control</button></div>}
        {condition!=='manual' && <div className="buttonRow">{['camera','display','audio','recording'].map(capability=><button key={capability} onClick={()=>post('/api/authority/restrict',{capability,restricted:!state.restricted_capabilities.includes(capability)}).then(refresh)}>{state.restricted_capabilities.includes(capability)?'Allow AI: ':'Restrict AI: '}{capability}</button>)}</div>}
      </section>

      {showResearch && <aside className="panel research">
        <div className="panelTitle">Researcher Console</div>
        <label>Participant <input value={state.participant_id} onChange={e=>post('/api/participant',{participant_id:e.target.value}).then(refresh)}/></label>
        <label>Study condition</label>
        <div className="conditionButtons"><button disabled={Boolean(state.study&&!state.study.finished)} className={condition==='manual'?'selected':''} onClick={()=>conditionSet('manual')}>0 · Manual</button><button disabled={Boolean(state.study&&!state.study.finished)} className={condition==='assistive'?'selected':''} onClick={()=>conditionSet('assistive')}>1 · Assistive</button><button disabled={Boolean(state.study&&!state.study.finished)} className={condition==='autonomous'?'selected':''} onClick={()=>conditionSet('autonomous')}>2 · Autonomous</button></div>
        <h3>CHI V1 teaching study</h3><p>One instructor/TA participant and one facilitator. No students or actors.</p>
        <label>Counterbalance group (0–5) <input type="number" min={0} max={5} value={order} onChange={e=>setOrder(Number(e.target.value))}/></label>
        <label>Condition position (0–2) <input type="number" min={0} max={2} value={position} onChange={e=>setPosition(Number(e.target.value))}/></label>
        <button disabled={busy||Boolean(state.study&&!state.study.finished)} onClick={()=>post('/api/study/start',{counterbalance_index:order,condition_position:position}).then(refresh)}>Start assigned condition</button>
        <button disabled={busy||!state.study||state.study.finished||(!state.study.completed&&state.study.task_index>=0)} onClick={async()=>{setBusy(true);try{await post('/api/study/next');await refresh()}finally{setBusy(false)}}}>Begin next teaching task</button>
        <h3>V1 presenter scenarios</h3>
        <div className="scenarioList">{config.scenarios.map((s:string)=><button disabled={busy} className={s.startsWith('v1_wrong_')?'failure':''} key={s} onClick={()=>inject(s)}>{s.replaceAll('_',' ')}</button>)}</div>
        <button className="wide" onClick={()=>post('/api/agent/evaluate').then(refresh)}>Run agent on current state</button>
        <p className="note">V1 failures concern camera framing, display source, audio mode, or recording layout. The standardized script uses the display failure in AI conditions. Extended multi-person scenarios remain available through the development API, outside V1.</p>
      </aside>}
    </main>
  </div>
}
