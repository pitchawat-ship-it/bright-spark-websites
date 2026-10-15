import { createFileRoute } from '@tanstack/react-router';
import { Debts } from '@/components/debt-views';
export const Route=createFileRoute('/debts')({head:()=>({meta:[{title:'My debts | AI Debt Recovery'},{name:'description',content:'Manage multiple debts, interest rates, minimum payments and due dates.'},{property:'og:title',content:'My debts | AI Debt Recovery'},{property:'og:description',content:'Manage multiple debts, interest rates, minimum payments and due dates.'},{property:'og:type',content:'website'},{name:'twitter:card',content:'summary_large_image'}]}),component:Debts});
