import React,{lazy,Suspense} from 'react';
import {createRoot} from 'react-dom/client';
const ResearchApp=lazy(()=>import('./research/ResearchApp'));
const InstructorApp=lazy(()=>import('./InstructorApp'));
const researchRoute=location.pathname.startsWith('/research');
createRoot(document.getElementById('root')!).render(<Suspense fallback={<p style={{padding:32}}>Opening Agentic Classroom…</p>}>{researchRoute?<ResearchApp/>:<InstructorApp/>}</Suspense>);
