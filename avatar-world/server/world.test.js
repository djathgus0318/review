import {test} from 'node:test';import assert from 'node:assert/strict';import {profile,movement} from './world.js';
test('profiles constrain untrusted input',()=>{assert.equal(profile({nickname:'a'.repeat(100),color:'bad'}).nickname.length,16);assert.equal(profile({color:'bad'}).color,'#e27b55');});
test('movement rejects invalid coordinates and bounds world',()=>{assert.equal(movement({x:NaN,z:0}),null);assert.deepEqual(movement({x:500,z:-500,action:'bad'}),{x:18,z:-18,rotation:0,action:'idle'});});
