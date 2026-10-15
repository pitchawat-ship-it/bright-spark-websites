import { describe,it,expect } from 'vitest';
import { assessment,simulate,reconcile,type Profile,type Debt } from './engine';
const p:Profile={name:'Test',income:2000,expenses:1000,commitments:0,reserve:100,savings:100,currency:'USD',incomeType:'fixed',start:'2026-10'};
const debts:[Debt,Debt,Debt]=[{id:'card',name:'Card',balance:3200,apr:22,minimum:100,dueDay:20,type:'standard',years:0,days:30,notes:''},{id:'loan',name:'Loan',balance:5800,apr:9,minimum:180,dueDay:25,type:'standard',years:0,days:30,notes:''},{id:'installment',name:'Installment',balance:1500,apr:5,minimum:70,dueDay:28,type:'standard',years:0,days:30,notes:''}];
describe('Financial safety and supplied simulation logic',()=>{
 it('matches the original Python full-term avalanche fixture',()=>expect(simulate(p,debts,'avalanche')).toMatchObject({months:14,interest:680.49,total:11180.49}));
 it('matches the original Python full-term snowball fixture',()=>expect(simulate(p,debts,'snowball')).toMatchObject({months:15,interest:806.96,total:11306.96}));
 it('protects reserve and savings in available budget',()=>{expect(assessment(p,debts)).toMatchObject({budget:800,minimum:350,extra:450,total:10500});});
 it('refuses hardship when required minimums cannot be covered',()=>{const low={...p,income:1500};expect(assessment(low,debts).shortfall).toBe(50);expect(()=>simulate(low,debts,'avalanche')).toThrow('minimum payments');});
 it('does not silently turn unknown APR into zero',()=>expect(()=>simulate(p,[{...debts[0],apr:null}],'avalanche')).toThrow('unknown'));
 it('allocates avalanche extras to highest APR',()=>{const plan=simulate(p,debts,'avalanche');expect(plan.rows.find(r=>r.month===1&&r.debtId==='card')).toMatchObject({interest:58.67,payment:550,extra:450,closing:2708.67});});
 it('allocates snowball extras to smallest balance',()=>expect(simulate(p,debts,'snowball').rows.find(r=>r.month===1&&r.debtId==='installment')).toMatchObject({interest:6.25,payment:520,extra:450,closing:986.25}));
 it('never exceeds budget and respects minima when affordable',()=>{for(const strategy of ['avalanche','snowball'] as const){const plan=simulate(p,debts,strategy);for(let m=1;m<=plan.months;m++){const rows=plan.rows.filter(r=>r.month===m);expect(rows.reduce((s,r)=>s+r.payment,0)).toBeLessThanOrEqual(800.001);rows.forEach(r=>expect(r.payment).toBeGreaterThanOrEqual(r.minimum));}expect(plan.paidOff).toBe(true);}});
 it('handles all-zero debt without failing',()=>expect(simulate(p,[],'avalanche')).toMatchObject({months:0,interest:0,paidOff:true,rows:[]}));
 it('matches supplied daily interest formula',()=>expect(simulate(p,[{...debts[0],type:'daily_card',days:30}],'avalanche').rows[0]?.interest).toBe(57.86));
 it('applies interest only once when recording multiple partial payments',()=>{const plan=simulate(p,debts,'avalanche');const first=reconcile(debts,[],plan,'card',100,'2026-10-10','');expect(first.debts[0]?.balance).toBe(3158.67);const second=reconcile(first.debts,[first.payment],plan,'card',200,'2026-10-11','');expect(second.debts[0]?.balance).toBe(2958.67);expect(second.payment.interest).toBe(0);});
 it('prevents duplicate payment records',()=>{const plan=simulate(p,debts,'avalanche');const first=reconcile(debts,[],plan,'card',100,'2026-10-10','');expect(()=>reconcile(first.debts,[first.payment],plan,'card',100,'2026-10-10','')).toThrow('already');});
 it('rejects payments exceeding amount owed',()=>expect(()=>reconcile(debts,[],simulate(p,debts,'avalanche'),'card',4000,'2026-10-10','')).toThrow('exceeds'));
});