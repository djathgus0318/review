import assert from 'node:assert/strict';
import {io} from 'socket.io-client';
const url=process.env.TEST_SERVER_URL||'http://127.0.0.1:3001';
const a=io(url,{autoConnect:false}),b=io(url,{autoConnect:false});
const ack=(s,event,data)=>new Promise((resolve,reject)=>s.timeout(4000).emit(event,data,(error,result)=>error?reject(error):resolve(result)));
const wait=(s,predicate)=>new Promise((resolve,reject)=>{const timer=setTimeout(()=>{s.off('players',onPlayers);reject(Error('Player state timeout'))},5000);function onPlayers(p){if(predicate(p)){clearTimeout(timer);s.off('players',onPlayers);resolve(p)}}s.on('players',onPlayers)});
try{
 for(const [s,name] of [[a,'카페 하나'],[b,'카페 둘']]){await new Promise((resolve,reject)=>{s.once('connect',resolve);s.once('connect_error',reject);s.connect()});const ready=wait(s,p=>p.some(x=>x.nickname===name));s.emit('join',{nickname:name,scene:'temple'});await ready;}
 assert.equal((await ack(a,'sit-coffee',0)).ok,false);
 assert.equal((await ack(a,'get-coffee',null)).ok,true);assert.equal((await ack(b,'get-coffee',null)).ok,true);
 const results=await Promise.all([ack(a,'sit-coffee',0),ack(b,'sit-coffee',0)]);assert.equal(results.filter(r=>r.ok).length,1);
 const winner=results[0].ok?a:b,loser=winner===a?b:a;
 const both=wait(winner,p=>p.filter(x=>x.action==='sitCoffee'&&x.hasCoffee).length===2);assert.equal((await ack(loser,'sit-coffee',1)).ok,true);await both;
 const stood=wait(loser,p=>p.some(x=>x.id===winner.id&&x.seatId===null));winner.emit('stand');await stood;
 assert.equal((await ack(loser,'sit-coffee',0)).ok,true);
 const freed=wait(winner,p=>p.length===1);loser.disconnect();await freed;
 assert.equal((await ack(winner,'sit-coffee',0)).ok,true);
 console.log('PASS coffee prerequisite, simultaneous-seat conflict, two seated drinkers, standing and disconnect release');
}finally{a.disconnect();b.disconnect()}
