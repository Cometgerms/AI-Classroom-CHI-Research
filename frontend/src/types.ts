export type Mode='off'|'assist'|'auto';
export type Health='ready'|'degraded'|'disconnected'|'connecting';
export type RecentAction={id:string;time:string;label:string;actor:string;canUndo:boolean};
export type InstructorAppState={
  roomStatus:Health;aiMode:Mode;ai:{status:Health;busy:boolean;message:string|null;label:string};currentActivity:string;
  currentDisplay:{source:string;label:string;available:boolean};
  cameraState:{target:string;label:string;follow:boolean;available:boolean;zone:string};
  audioState:{mode:string;label:string;available:boolean;microphoneActive:boolean;programActive:boolean};
  recordingState:{status:Health;simulated:boolean;recording:boolean|null;startedAt:string|null;layout:string|null};
  programState:{layout:string|null;label:string;preview:{kind:string;label:string;description:string}};
  recentActions:RecentAction[];pendingRecommendation:{id:string;title:string;actions:string[];why:string}|null;
  devices:{id:string;label:string;status:Health;detail:string}[];restrictions:string[];
};
export type Preferences={default_mode:Mode;local_model:string;default_framing:string;follow_presenter:boolean;default_layout:string};
