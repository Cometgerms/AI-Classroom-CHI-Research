import React, {useEffect, useMemo, useState} from 'react';
import {createRoot} from 'react-dom/client';
import {Bot, Camera, Monitor, Mic2, CircleDot, FlaskConical, Undo2, Hand} from 'lucide-react';
import './styles.css';

const API='http://localhost:8000';
const researcher=new URLSearchParams(location.search).get('researcher')==='1';
type Condition='manual'|'assistive'|'autonomous';
type State=any;

async function post(path:string, body?:any){
  const r=await fetch(API+path,{method:'POST',headers:{'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body)});
  if(!r.ok) throw new Error(await r.text());
  return r.json();
}

function Pill({children,kind='neutral'}:{children:React.ReactNode,kind?:string}){return <span className={'pill '+kind}>{children}</span>}

function App(){
  const [state,setState]=useState<State|null>(null);
  const [recommendation,setRecommendation]=useState<any>(null);
  const [config,setConfig]=useState<any>({scenarios:[]});
  const [research,setResearch]=useState(true);
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState('');
  useEffect(()=>{const handler=(event:PromiseRejectionEvent)=>{event.preventDefault();setError(String(event.reason))};window.addEventListener('unhandledrejection',handler);return()=>window.removeEventListener('unhandledrejection',handler)},[]);

  const refresh=async()=>{const d=await fetch(API+'/api/state').then(r=>r.json());setState(d.state);setRecommendation(d.recommendation)};
  useEffect(()=>{refresh();fetch(API+'/api/config?researcher='+researcher).then(r=>r.json()).then(setConfig);const id=setInterval(refresh,750);return()=>clearInterval(id)},[]);
  if(!state) return <div className="loading">Connecting to classroom brain…</div>;

  const participant=config.participant_view!==false && !researcher;
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
          <div className={'person instructor '+(state.observations.active_speaker==='instructor'?'speaking':'')}>INSTRUCTOR</div>
          <div className="students">{[1,2,3,4,5,6].map(n=><div key={n} className={'student '+(state.observations.active_speaker===`student_${n}`?'speaking':'')}>S{n}</div>)}</div>
          <div className="cameraIcon"><Camera size={22}/> {state.devices.camera_target}</div>
        </div>
        <div className="manualControls">
          <h3>Participant AV Controls</h3>
          <div className="buttonRow"><button onClick={()=>manual('camera_focus',{target:'instructor'})}>Camera: Instructor</button><button onClick={()=>manual('camera_focus',{target:'wide'})}>Camera: Wide</button><button onClick={()=>manual('camera_focus',{target:'student_3'})}>Camera: Student</button></div>
          <div className="buttonRow"><button onClick={()=>manual('display_set_source',{source:'presentation'})}>Slides</button><button onClick={()=>manual('display_set_source',{source:'camera'})}>Camera to Display</button><button onClick={()=>manual('student_voice_lift',{enabled:!state.devices.student_voice_lift})}>Student Voice {state.devices.student_voice_lift?'Off':'On'}</button></div>
          <div className="buttonRow"><button onClick={()=>manual('recording_start',{})}>Record</button><button onClick={()=>manual('recording_stop',{})}>Stop</button><button onClick={()=>manual('recording_set_layout',{layout:'q_and_a'})}>Q&A Layout</button></div>
        </div>
      </section>

      <section className="panel statePanel">
        <div className="panelTitle">Room State</div>
        {!participant && <dl><dt>Session</dt><dd>{state.session}</dd><dt>Activity</dt><dd>{state.activity.state} <Pill kind={statusColor}>{Math.round(state.activity.confidence*100)}%</Pill></dd><dt>Active speaker</dt><dd>{state.observations.active_speaker}</dd><dt>Transcript</dt><dd className="transcript">{state.observations.transcript||'—'}</dd><dt>Evidence</dt><dd>{state.activity.evidence.join(' · ')||'—'}</dd></dl>}
        <div className="deviceGrid"><div><Camera/> <b>Camera</b><span>{state.devices.camera_target}</span></div><div><Monitor/> <b>Display</b><span>{state.devices.display_source}</span></div><div><Mic2/> <b>Audio</b><span>{state.devices.audio_mode}{state.devices.student_voice_lift?' + student lift':''}</span></div><div><CircleDot/> <b>Recording</b><span>{state.devices.recording?'REC':'OFF'} · {state.devices.recording_layout}</span></div></div>
      </section>

      <section className="panel agentPanel">
        <div className="panelTitle"><Bot size={18}/> Agent</div>
        {condition==='manual' && <div className="agentMessage muted"><b>Manual condition.</b><br/>The AI does not recommend or execute AV changes.</div>}
        {condition==='assistive' && !recommendation && <div className="agentMessage">Recommendations appear when the classroom activity changes.</div>}
        {condition==='autonomous' && <div className="agentMessage"><b>Autonomous authority active.</b><br/>Validated agent actions execute immediately.</div>}
        {recommendation && <div className="recommend"><h3>AI Recommendation</h3><p>{recommendation.decision.rationale}</p>{recommendation.decision.actions.map((a:any,i:number)=><div className="action" key={i}><b>{a.tool.replaceAll('_',' ')}</b><span>{Object.values(a.args).map(String).join(' · ')}</span></div>)}<div className="buttonRow"><button className="primary" onClick={async()=>{await post('/api/recommendation/apply');refresh()}}>Apply</button><button onClick={async()=>{await post('/api/recommendation/dismiss');refresh()}}>Dismiss</button></div></div>}
        {condition==='autonomous' && <div className="override"><button onClick={async()=>{await post('/api/override',{mode:'undo',capability:'all'});refresh()}}><Undo2 size={16}/> Undo last AI action</button><button className="danger" onClick={async()=>{await post('/api/override',{mode:'manual',capability:'all'});refresh()}}><Hand size={16}/> Take Control</button></div>}
      </section>

      {showResearch && <aside className="panel research">
        <div className="panelTitle">Researcher Console</div>
        <label>Participant <input value={state.participant_id} onChange={e=>post('/api/participant',{participant_id:e.target.value}).then(refresh)}/></label>
        <label>Study condition</label>
        <div className="conditionButtons"><button className={condition==='manual'?'selected':''} onClick={()=>conditionSet('manual')}>0 · Manual</button><button className={condition==='assistive'?'selected':''} onClick={()=>conditionSet('assistive')}>1 · Assistive</button><button className={condition==='autonomous'?'selected':''} onClick={()=>conditionSet('autonomous')}>2 · Autonomous</button></div>
        <h3>Play scenario</h3>
        <div className="scenarioList">{config.scenarios.map((s:string)=><button disabled={busy} className={s==='controlled_wrong_qna'?'failure':''} key={s} onClick={()=>inject(s)}>{s.replaceAll('_',' ')}</button>)}</div>
        <button className="wide" onClick={()=>post('/api/agent/evaluate').then(refresh)}>Run agent on current state</button>
        <p className="note">The controlled wrong-Q&A scenario intentionally creates the study failure. Do not rely on a naturally occurring model error.</p>
      </aside>}
    </main>
  </div>
}

createRoot(document.getElementById('root')!).render(<App/>);
