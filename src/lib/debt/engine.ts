import Decimal from 'decimal.js';
import { z } from 'zod';

const value = z.number().finite().min(0).max(1e10);
export const debtSchema = z.object({ id:z.string(), name:z.string().trim().min(1).max(100), balance:value, apr:z.number().min(0).max(100).nullable(), minimum:value.nullable(), dueDay:z.number().int().min(1).max(31), type:z.enum(['standard','daily_card','flat_rate']), years:z.number().min(0).max(50), days:z.number().int().min(1).max(366), notes:z.string().max(1000) });
export type Debt = z.infer<typeof debtSchema>;
export const profileSchema = z.object({name:z.string().min(1).max(100),income:value,expenses:value,commitments:value,reserve:value,savings:value,currency:z.enum(['USD','THB','EUR','GBP']),incomeType:z.enum(['fixed','variable','irregular']),start:z.string().regex(/^\d{4}-(0[1-9]|1[0-2])$/)});
export type Profile = z.infer<typeof profileSchema>;
export type Strategy = 'avalanche'|'snowball';
export type Row = {month:number;period:string;debtId:string;name:string;opening:number;interest:number;minimum:number;extra:number;payment:number;principal:number;closing:number;due:string};
export type Plan = {id:string;created:string;strategy:Strategy;budget:number;rows:Row[];months:number;interest:number;total:number;paidOff:boolean;end:string;signature:string};
const d=(n:number)=>new Decimal(n);
export const round=(n:number)=>d(n).toDecimalPlaces(2,Decimal.ROUND_HALF_UP).toNumber();
const q=(n:Decimal)=>n.toDecimalPlaces(2,Decimal.ROUND_HALF_UP);
export function assessment(p:Profile, debts:Debt[]) {
 const budget=round(p.income-p.expenses-p.commitments-p.reserve-p.savings);
 const minimum=round(debts.filter(x=>x.balance>0).reduce((s,x)=>s+(x.minimum??0),0));
 return {budget,minimum,extra:Math.max(0,round(budget-minimum)),shortfall:Math.max(0,round(minimum-budget)),total:round(debts.reduce((s,x)=>s+x.balance,0)),unknown:debts.some(x=>x.balance>0&&(x.apr===null||x.minimum===null||x.type==='flat_rate'&&x.years<=0))};
}
export const signature=(p:Profile,debts:Debt[])=>JSON.stringify({p,debts});
export function monthDate(period:string,day:number) {const [y=2026,m=1]=period.split('-').map(Number); return `${period}-${String(Math.min(day,new Date(y,m,0).getDate())).padStart(2,'0')}`;}
export function simulate(p:Profile,debts:Debt[],strategy:Strategy):Plan {
 profileSchema.parse(p); debts.forEach(x=>debtSchema.parse(x));
 const a=assessment(p,debts); if(a.unknown)throw new Error('Add the unknown interest rates, minimum payments and flat-rate terms before estimating a plan.');
 if(a.shortfall>0)throw new Error('Your budget cannot cover minimum payments. Review hardship options first.');
 const state=debts.map(x=>({...x,bal:d(x.balance),rate:x.type==='flat_rate'&&x.years>0?round(2*x.years*12/(x.years*12+1)*(x.apr??0)):x.apr??0}));
 const rows:Row[]=[];const pool=d(a.budget);
 for(let month=1;month<=600;month++) {
  const active=state.filter(x=>x.bal.gt(0));if(!active.length)break;
  const [year=2026,mo=1]=p.start.split('-').map(Number);const dt=new Date(Date.UTC(year,mo+month-2,1));const period=dt.toISOString().slice(0,7);
  const allocations=active.map(x=>{const interest=q(x.bal.mul(x.rate).div(100).div(x.type==='daily_card'?365:12).mul(x.type==='daily_card'?x.days:1));const owed=x.bal.add(interest);const minimum=Decimal.min(d(x.minimum??0),owed);return{x,interest,owed,minimum,extra:d(0)}});
  let extra=Decimal.max(0,pool.sub(allocations.reduce((s,x)=>s.add(x.minimum),d(0))));
  allocations.sort((a,b)=>strategy==='avalanche'?b.x.rate-a.x.rate||a.x.bal.cmp(b.x.bal)||a.x.name.localeCompare(b.x.name):a.x.bal.cmp(b.x.bal)||b.x.rate-a.x.rate||a.x.name.localeCompare(b.x.name));
  for(const r of allocations){r.extra=Decimal.min(extra,r.owed.sub(r.minimum));extra=extra.sub(r.extra);}
  for(const r of allocations){const payment=r.minimum.add(r.extra);const closing=q(r.owed.sub(payment));rows.push({month,period,debtId:r.x.id,name:r.x.name,opening:r.x.bal.toNumber(),interest:r.interest.toNumber(),minimum:r.minimum.toNumber(),extra:r.extra.toNumber(),payment:payment.toNumber(),principal:payment.sub(r.interest).toNumber(),closing:closing.toNumber(),due:monthDate(period,r.x.dueDay)});r.x.bal=closing;}
 }
 return {id:'preview',created:'',strategy,budget:a.budget,rows,months:Math.max(0,...rows.map(x=>x.month)),interest:round(rows.reduce((s,x)=>s+x.interest,0)),total:round(rows.reduce((s,x)=>s+x.payment,0)),paidOff:state.every(x=>x.bal.lte(0)),end:rows.at(-1)?.period??p.start,signature:signature(p,debts)};
}
export type Payment = {id:string;debtId:string;date:string;amount:number;period:string;interest:number;note:string;source:'manual'};
export function reconcile(debts:Debt[],payments:Payment[],plan:Plan,debtId:string,amount:number,date:string,note:string):{debts:Debt[];payment:Payment} {
 if(!Number.isFinite(amount)||amount<=0)throw new Error('Enter a positive payment amount.');
 if(!/^\d{4}-\d{2}-\d{2}$/.test(date)||new Date(date+'T00:00:00Z').toISOString().slice(0,10)!==date||date>new Date().toISOString().slice(0,10))throw new Error('Choose a valid payment date, not in the future.');
 const debt=debts.find(x=>x.id===debtId);if(!debt)throw new Error('Debt not found.');
 const period=date.slice(0,7);const row=plan.rows.find(x=>x.debtId===debtId&&x.period===period);if(!row)throw new Error('No confirmed schedule exists for this payment month. Review your plan.');
 if(payments.some(x=>x.debtId===debtId&&x.date===date&&x.amount===amount))throw new Error('This payment has already been recorded.');
 const interest=payments.some(x=>x.debtId===debtId&&x.period===period)?0:row.interest;
 if(amount>round(debt.balance+interest))throw new Error('Payment exceeds the estimated amount owed.');
 return {debts:debts.map(x=>x.id===debtId?{...x,balance:round(x.balance+interest-amount)}:x),payment:{id:crypto.randomUUID(),debtId,date,amount:round(amount),period,interest,note,source:'manual'}};
}