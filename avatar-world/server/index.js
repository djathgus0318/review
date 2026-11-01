import {clientOrigins} from '../shared/connection.js';
import {heightAt} from '../shared/world.js';
import {createServer} from 'node:http';
import {Server} from 'socket.io';
import {profile,movement,scenes,reserveCafeSeat} from './world.js';
const http=createServer((req,res)=>{res.writeHead(200,{'Content-Type':'application/json'});res.end(JSON.stringify({status:'ok',players:players.size}));});
const io=new Server(http,{cors:{origin:clientOrigins(process.env.CLIENT_ORIGIN)}});
const players=new Map();
function broadcast(){for(const scene of scenes)io.to(scene).emit('players',[...players.values()].filter(p=>p.scene===scene));}
io.on('connection',socket=>{
 socket.on('join',(data={})=>{const old=players.get(socket.id);if(old)socket.leave(old.scene);const scene=scenes.includes(data.scene)?data.scene:'temple';players.set(socket.id,{id:socket.id,...profile(data),scene,x:0,y:0,z:7,rotation:0,action:'idle',hasCoffee:false,seatId:null});socket.join(scene);broadcast();});
 socket.on('get-coffee',(_,ack)=>{const p=players.get(socket.id);if(!p||p.scene!=='temple'){if(typeof ack==='function')ack({ok:false});return;}Object.assign(p,{hasCoffee:true,seatId:null,action:'drink',x:-8,y:0,z:6,rotation:Math.PI});broadcast();if(typeof ack==='function')ack({ok:true});});
 socket.on('sit-coffee',(seatId,ack)=>{const result=reserveCafeSeat(players,socket.id,seatId);if(result.ok)broadcast();if(typeof ack==='function')ack(result);});
 socket.on('stand',()=>{const p=players.get(socket.id);if(p){p.seatId=null;p.action='idle';broadcast();}});
 let last=0;socket.on('move',data=>{const now=Date.now();if(now-last<35)return;last=now;const p=players.get(socket.id),m=movement(data);if(p&&m){if(p.seatId!==null){if(['walk','swim','climb','drink','lie'].includes(m.action)){p.seatId=null;}else{p.action='sitCoffee';broadcast();return;}}if(m.action==='sitCoffee')m.action='idle';Object.assign(p,m,{y:heightAt(p.scene,m.x,m.z,m.action==='climb'?6.8:p.y)});broadcast();}});
 socket.on('disconnect',()=>{players.delete(socket.id);broadcast();});
});
http.listen(Number(process.env.PORT)||3001,'0.0.0.0',()=>console.log('Realtime server ready'));
