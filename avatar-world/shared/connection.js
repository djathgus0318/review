export const publicServer='https://sai-realtime.onrender.com';
export const publicClient='https://sai-avatar-web.vercel.app';
export function normalizeOrigin(value){
 try{const url=new URL(String(value||'').trim());if(!['http:','https:'].includes(url.protocol)||url.username||url.password)return null;return url.origin;}catch{return null;}
}
export function serverUrl(value,production){return normalizeOrigin(value)||(production?publicServer:undefined);}
export function clientOrigins(value){return [...new Set([publicClient,'http://localhost:5173','http://127.0.0.1:5173',...String(value||'').split(',').map(normalizeOrigin).filter(Boolean)])];}
