import {test} from 'node:test';import assert from 'node:assert/strict';import {profile,movement} from './world.js';
test('profiles constrain untrusted input',()=>{assert.equal(profile({nickname:'a'.repeat(100),color:'bad'}).nickname.length,16);assert.equal(profile({color:'bad'}).color,'#e27b55');});
test('movement rejects invalid coordinates and bounds world',()=>{assert.equal(movement({x:NaN,z:0}),null);assert.deepEqual(movement({x:500,z:-500,action:'bad'}),{x:18,z:-18,rotation:0,action:'idle'});});

import {beds,heightAt} from '../shared/world.js';
test('long hair and expressions survive profile validation',()=>{assert.equal(profile({hair:'long',expression:'surprised'}).hair,'long');assert.equal(profile({expression:'surprised'}).expression,'surprised');assert.equal(profile({expression:'bad'}).expression,'happy');});
test('new activities are synchronized and terrain heights are derived',()=>{for(const action of ['lie','drink','climb'])assert.equal(movement({x:0,z:0,action}).action,action);assert.equal(beds.length,5);assert.equal(new Set(beds.map(b=>b.x)).size,5);assert.equal(heightAt('temple',0,-3,6.8),6.8);assert.equal(heightAt('temple',4,7),0);assert.ok(heightAt('temple',4,2)>0);assert.equal(heightAt('beach',0,-3),0);});

test('ground walkers do not teleport onto the viewing deck',()=>{assert.equal(heightAt('temple',0,-3,0),0);assert.equal(heightAt('temple',4,-3,6.4),6.8);assert.equal(heightAt('temple',1,-3,6.8),6.8);});

import {serverUrl,clientOrigins,normalizeOrigin} from '../shared/connection.js';
test('production has working endpoint defaults and normalizes copied URLs',()=>{assert.equal(serverUrl('',true),'https://sai-realtime.onrender.com');assert.equal(serverUrl(' https://sai-realtime.onrender.com/ ',true),'https://sai-realtime.onrender.com');assert.equal(serverUrl('',false),undefined);assert.equal(normalizeOrigin('javascript:alert(1)'),null);assert.equal(normalizeOrigin('https://user:password@example.com'),null);assert.ok(clientOrigins(' https://sai-avatar-web.vercel.app/ ').includes('https://sai-avatar-web.vercel.app'));assert.ok(clientOrigins('wrong').includes('https://sai-avatar-web.vercel.app'));assert.ok(!clientOrigins('*').includes('*'));});

import {reserveCafeSeat} from './world.js';
import {cafeChairs} from '../shared/world.js';
test('cafe has two seats and requires coffee before sitting',()=>{const p={id:'a',scene:'temple',hasCoffee:false,seatId:null};const players=new Map([['a',p]]);assert.equal(cafeChairs.length,2);assert.equal(reserveCafeSeat(players,'a',0).ok,false);p.hasCoffee=true;assert.equal(reserveCafeSeat(players,'a',2).ok,false);assert.equal(reserveCafeSeat(players,'a',0).ok,true);assert.equal(p.action,'sitCoffee');assert.equal(p.x,cafeChairs[0].x);assert.equal(p.seatId,0);});
test('one chair cannot be claimed by two players, and disconnect frees it',()=>{const a={id:'a',scene:'temple',hasCoffee:true},b={id:'b',scene:'temple',hasCoffee:true};const players=new Map([['a',a],['b',b]]);assert.equal(reserveCafeSeat(players,'a',0).ok,true);assert.equal(reserveCafeSeat(players,'b',0).ok,false);assert.equal(reserveCafeSeat(players,'b',1).ok,true);players.delete('a');assert.equal(reserveCafeSeat(players,'b',0).ok,true);assert.equal(b.seatId,0);});
