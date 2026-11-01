import {actions} from '../shared/world.js';
export const scenes = ['temple','beach'];
export function profile(data={}) {return {nickname:String(data.nickname||'여행자').trim().slice(0,16)||'여행자',expression:['happy','neutral','surprised'].includes(data.expression)?data.expression:'happy',gender:data.gender==='female'?'female':'male',hair:['short','bob','bun','long'].includes(data.hair)?data.hair:'short',color:/^#[0-9a-f]{6}$/i.test(data.color)?data.color:'#e27b55'};}
export function movement(data={}) {if(!Number.isFinite(data.x)||!Number.isFinite(data.z))return null;return {x:Math.max(-18,Math.min(18,data.x)),z:Math.max(-18,Math.min(18,data.z)),rotation:Number.isFinite(data.rotation)?data.rotation:0,action:actions.includes(data.action)?data.action:'idle'};}
