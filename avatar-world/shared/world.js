export const beds = Array.from({length:5},(_,i)=>({id:i,x:-10+i*5,z:4}));
export function heightAt(scene,x,z,previousHeight=0){
 if(scene!=='temple')return 0;
 if(x>=3&&x<=5&&z>=-3&&z<=7)return Math.min(6.8,Math.max(0,Math.floor((7-z)/.5)*.34));
 if(z>=-4&&z<=-2&&x>=-1&&x<=5&&previousHeight>=6.4)return 6.8;
 return 0;
}
export const actions=['idle','walk','swim','castle','dig','climb','drink','lie','sitCoffee'];
export const cafeChairs=[{id:0,x:-9.35,z:8,rotation:Math.PI/2},{id:1,x:-6.65,z:8,rotation:-Math.PI/2}];
