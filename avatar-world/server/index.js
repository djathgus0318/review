import {clientOrigins} from '../shared/connection.js';
import {heightAt} from '../shared/world.js';
import {createServer} from 'node:http';
import {Server} from 'socket.io';
import {profile,movement,scenes} from './world.js';
const http=createServer((req,res)=>{res.writeHead(200,{'Content-Type':'application/json'});res.end(JSON.stringify({status:'ok',players:players.size}));});
const io=new Server(http,{cors:{origin:clientOrigins(process.env.CLIENT_ORIGIN)}});
const players=new Map();
function broadcast(){for(const scene of scenes)io.to(scene).emit('players',[...players.values()].filter(p=>p.scene===scene));}
io.on('connection',socket=>{
 socket.on('join',(data={})=>{const old=players.get(socket.id);if(old)socket.leave(old.scene);const scene=scenes.includes(data.scene)?data.scene:'temple';players.set(socket.id,{id:socket.id,...profile(data),scene,x:0,y:0,z:7,rotation:0,action:'idle'});socket.join(scene);broadcast();});
 let last=0;socket.on('move',data=>{const now=Date.now();if(now-last<35)return;last=now;const p=players.get(socket.id),m=movement(data);if(p&&m){Object.assign(p,m,{y:heightAt(p.scene,m.x,m.z,m.action==='climb'?6.8:p.y)});broadcast();}});
 socket.on('disconnect',()=>{players.delete(socket.id);broadcast();});
});
http.listen(Number(process.env.PORT)||3001,'0.0.0.0',()=>console.log('Realtime server ready'));
