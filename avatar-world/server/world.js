import {actions,cafeChairs} from '../shared/world.js';
export const scenes = ['temple','beach'];
export function profile(data={}) {return {nickname:String(data.nickname||'여행자').trim().slice(0,16)||'여행자',expression:['happy','neutral','surprised'].includes(data.expression)?data.expression:'happy',gender:data.gender==='female'?'female':'male',hair:['short','bob','bun','long'].includes(data.hair)?data.hair:'short',color:/^#[0-9a-f]{6}$/i.test(data.color)?data.color:'#e27b55'};}
export function movement(data={}) {if(!Number.isFinite(data.x)||!Number.isFinite(data.z))return null;return {x:Math.max(-18,Math.min(18,data.x)),z:Math.max(-18,Math.min(18,data.z)),rotation:Number.isFinite(data.rotation)?data.rotation:0,action:actions.includes(data.action)?data.action:'idle'};}

export function reserveCafeSeat(players,id,seatId){
 const p=players.get(id),chair=cafeChairs.find(c=>c.id===seatId);
 if(!p||p.scene!=='temple'||!chair)return {ok:false,message:'미륵사지의 의자를 선택해 주세요.'};
 if(!p.hasCoffee)return {ok:false,message:'먼저 포장마차에서 음료를 받아 주세요.'};
 if([...players.values()].some(other=>other.id!==id&&other.scene==='temple'&&other.seatId===seatId))return {ok:false,message:'다른 여행자가 앉아 있어요. 옆 의자를 선택해 주세요.'};
 Object.assign(p,{x:chair.x,z:chair.z,y:0,rotation:chair.rotation,action:'sitCoffee',seatId});
 return {ok:true,chair};
}
