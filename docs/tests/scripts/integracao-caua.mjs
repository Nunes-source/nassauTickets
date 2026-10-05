import assert from 'node:assert/strict';
import { build, stop } from 'esbuild';
import { JSDOM } from 'jsdom';
import { fileURLToPath } from 'node:url';
import { criarSenha, escolherProxima } from '../../../frontend/src/utils/senhas.js';

process.env.TZ = 'America/Sao_Paulo';
const frontend = fileURLToPath(new URL('../../../frontend/', import.meta.url));
const compilado = await build({
  stdin: { contents: 'export {default as App} from "./src/App.jsx"; export {act,createElement} from "react"; export {createRoot} from "react-dom/client";', resolveDir: frontend, loader: 'jsx' },
  bundle: true, write: false, format: 'esm', platform: 'browser', jsx: 'automatic',
});
const dom = new JSDOM('<!doctype html><div id="root"></div>', {url:'http://localhost/#totem',pretendToBeVisual:true});
globalThis.window=dom.window;
globalThis.document=dom.window.document;
const intervalos = new Set();
const setIntervalReal = globalThis.setInterval;
const clearIntervalReal = globalThis.clearInterval;
globalThis.setInterval = (...args) => {const id=setIntervalReal(...args);intervalos.add(id);return id;};
globalThis.clearInterval = (id) => {intervalos.delete(id);clearIntervalReal(id);};
Object.defineProperty(globalThis,'navigator',{configurable:true,value:dom.window.navigator});
globalThis.IS_REACT_ACT_ENVIRONMENT=true;
// Registra os canais criados por React para encerrá-los ao terminar a suíte.
const MessageChannelReal=globalThis.MessageChannel;
const canais=[];
globalThis.MessageChannel=class extends MessageChannelReal {constructor(){super();canais.push(this);}};
const {App,act,createElement,createRoot}=await import('data:text/javascript;base64,'+Buffer.from(compilado.outputFiles[0].text).toString('base64'));
const resultados=[];
const pendencias=[];
let root;
const texto=()=>document.body.textContent;
const button=(seletor)=>document.querySelector(seletor);
async function iniciar(hash='totem') {
  if(root) await act(async()=>root.unmount());
  window.history.replaceState(null,'','#'+hash);
  document.body.innerHTML='<div id="root"></div>';
  root=createRoot(document.getElementById('root'));
  await act(async()=>root.render(createElement(App)));
}
async function click(el) {
  assert.ok(el,'Elemento da interação existe');
  assert.ok(!el.disabled,'Elemento da interação está habilitado');
  await act(async()=>el.dispatchEvent(new window.MouseEvent('click',{bubbles:true})));
}
async function emitir(tipo) {await click(button('.opcao-'+tipo)); return button('.senha-numero').textContent;}
async function navegar(tela) {
  await act(async()=>{
    window.history.replaceState(null,'','#'+tela);
    window.dispatchEvent(new window.HashChangeEvent('hashchange'));
  });
}
async function guiche(n) {
  const el=button('select');
  await act(async()=>{el.value=String(n);el.dispatchEvent(new window.Event('change',{bubbles:true}));});
}
async function chamar(){await click(button('.botao-primario'));}
async function caso(id,descricao,executar){
 try{await iniciar();await executar();resultados.push({id,descricao,status:'APROVADO'});}
 catch(e){resultados.push({id,descricao,status:'REPROVADO',erro:e.message});}
}
await caso('I01','Totem inicia vazio com SP, SG e SE',async()=>{assert.equal(document.querySelectorAll('.totem-opcoes button').length,3);assert.match(texto(),/Aguardando atendimento agora: 0/);});
await caso('I02','Emissão sequencial e contadores independentes por tipo',async()=>{assert.match(await emitir('SP'),/-SP001$/);assert.match(await emitir('SP'),/-SP002$/);assert.match(await emitir('SG'),/-SG001$/);assert.match(await emitir('SE'),/-SE001$/);assert.match(texto(),/Aguardando atendimento agora: 4/);});
await caso('I03','Senha emitida aparece na fila ao navegar',async()=>{const n=await emitir('SG');await navegar('atendente');assert.equal(document.querySelectorAll('.fila-item').length,1);assert.match(texto(),/Fila de espera \(1\)/);assert.ok(texto().includes(n));});
await caso('I04','Chamada remove a senha da fila e registra guichê 2 no painel',async()=>{const n=await emitir('SP');await navegar('atendente');await guiche(2);await chamar();assert.match(texto(),/Nenhuma senha aguardando/);await navegar('painel');assert.equal(button('.painel-senha').textContent,n);assert.match(button('.painel-guiche').textContent,/Guichê 2/);});
await caso('I05','Regra simplificada escolhe SP na fila mista',async()=>{await emitir('SG');await emitir('SE');const sp=await emitir('SP');await navegar('atendente');await chamar();await navegar('painel');assert.equal(button('.painel-senha').textContent,sp);});
await caso('I06','Sem SP, SE é escolhida antes de SG',async()=>{await emitir('SG');const se=await emitir('SE');await navegar('atendente');await chamar();await navegar('painel');assert.equal(button('.painel-senha').textContent,se);});
await caso('I07','Somente SG: ordem de chegada é mantida',async()=>{const primeira=await emitir('SG');await emitir('SG');await navegar('atendente');await chamar();await navegar('painel');assert.equal(button('.painel-senha').textContent,primeira);});
await caso('I08','Botão de chamada desabilitado em fila vazia',async()=>{await navegar('atendente');assert.equal(button('.botao-primario').disabled,true);assert.match(texto(),/Nenhuma senha aguardando/);});
await caso('I09','Painel não antecipa senha emitida ainda não chamada',async()=>{const n=await emitir('SP');await navegar('painel');assert.match(texto(),/Nenhuma senha chamada ainda/);assert.ok(!texto().includes(n));});
await caso('I10','Painel limita sete chamadas às cinco mais recentes',async()=>{const senhas=[];for(let i=0;i<7;i++)senhas.push(await emitir('SG'));await navegar('atendente');for(let i=0;i<7;i++)await chamar();await navegar('painel');const exibidas=[button('.painel-senha').textContent,...[...document.querySelectorAll('.historico-senha')].map(x=>x.textContent)];assert.deepEqual(exibidas,senhas.slice(2).reverse());});
await caso('I11','Navegação entre telas conserva a fila em memória',async()=>{const n=await emitir('SE');await navegar('painel');await navegar('totem');assert.equal(button('.senha-numero').textContent,n);await navegar('atendente');assert.match(texto(),/Fila de espera \(1\)/);});
await caso('I12','Cada guichê disponível chama cada tipo de senha',async()=>{for(const g of [1,2,3])for(const tipo of ['SP','SE','SG']){await iniciar();const n=await emitir(tipo);await navegar('atendente');await guiche(g);await chamar();await navegar('painel');assert.equal(button('.painel-senha').textContent,n);assert.match(button('.painel-guiche').textContent,new RegExp('Guichê '+g));}});
await caso('I13','Atendente mostra a última chamada do guichê selecionado',async()=>{const n=await emitir('SG');await navegar('atendente');await guiche(3);await chamar();assert.ok(button('.ultima-do-guiche').textContent.includes(n));await guiche(1);assert.match(button('.ultima-do-guiche').textContent,/ainda não fez nenhuma chamada/);});
await caso('I14','Hash inválido abre Totem',async()=>{await iniciar('inexistente');assert.equal(button('h1').textContent,'Retire sua senha');});
await caso('I15','Menu marca a tela atual e rótulo do guichê está presente',async()=>{await navegar('atendente');assert.equal(button('a[aria-current="page"]').getAttribute('href'),'#atendente');assert.ok(button('select').closest('label').textContent.includes('Guichê'));});

// Estas verificações registram limitações encontradas; não são aprovações de requisitos.
await iniciar();
const base=new Date('2026-10-04T09:00:00-03:00');
let fila=[criarSenha('SP',1,base),criarSenha('SP',2,base),criarSenha('SE',1,base),criarSenha('SG',1,base)];
const ordem=[];
while(fila.length){const s=escolherProxima(fila);ordem.push(s.tipo);fila=fila.filter(x=>x.numero!==s.numero);}
pendencias.push({id:'D01',requisitos:'RF03 / RN02 / RN03',observado:ordem.join(' → '),esperado:'SP → SE → SP → SG',status:ordem.join(',')==='SP,SE,SP,SG'?'RESOLVIDA':'PENDENCIA_CONFIRMADA'});
await emitir('SP');await iniciar();const reinicio=await emitir('SP');
pendencias.push({id:'D02',requisitos:'RF02 / RN09 / RNF05',observado:'Remontagem do App apaga a fila e recomeça em '+reinicio,esperado:'Persistir fila e sequência durante o dia. A remontagem simula reinicialização do componente, sem afirmar teste de F5.',status:'PENDENCIA_CONFIRMADA'});
await navegar('atendente');
const botoes=[...document.querySelectorAll('button')].map(x=>x.textContent.trim());
pendencias.push({id:'D03',requisitos:'RF04 a RF07 / RF10',observado:'Ações disponíveis no terminal: '+botoes.join(', '),esperado:'Rechamada, início, encerramento e registro de não comparecimento na Fase 2.',status:'NAO_IMPLEMENTADO_NESTA_FASE'});
const RealDate=globalThis.Date;
let instante='2026-10-04T23:59:00-03:00';
class DataControlada extends RealDate{constructor(...args){super(...(args.length?args:[instante]));}static now(){return new RealDate(instante).getTime();}}
let dia1,dia2;
try{
 globalThis.Date=DataControlada;
 await iniciar();dia1=await emitir('SG');
 instante='2026-10-05T00:01:00-03:00';dia2=await emitir('SG');
}finally{globalThis.Date=RealDate;}
pendencias.push({id:'D04',requisitos:'RF02 / RN09',observado:dia1+' → '+dia2,esperado:'261005-SG001 ao mudar o dia sem reinicializar a página.',status:dia2==='261005-SG001'?'RESOLVIDA':'PENDENCIA_CONFIRMADA'});
pendencias.push({id:'D05',requisitos:'RN04 / RF13',observado:'As emissões do teste D04 foram aceitas às 23h59 e 00h01.',esperado:'Controlar o expediente de 7h a 17h no sistema completo.',status:'NAO_IMPLEMENTADO_NESTA_FASE'});
if(root)await act(async()=>root.unmount());
dom.window.close();
for (const id of intervalos) clearIntervalReal(id);
globalThis.setInterval=setIntervalReal;
globalThis.clearInterval=clearIntervalReal;
stop();
for(const canal of canais){canal.port1.close();canal.port2.close();}
globalThis.MessageChannel=MessageChannelReal;
const aprovados=resultados.filter(x=>x.status==='APROVADO').length;
console.log(JSON.stringify({suite:'Cauã Andrade — integração em DOM simulado',executadoEm:new RealDate().toISOString(),ambiente:{node:process.version,fuso:process.env.TZ,dom:'jsdom 26.1.0',observacao:'Sem navegador real; sem validação visual, áudio ou concorrência de clientes.'},total:resultados.length,aprovados,reprovados:resultados.length-aprovados,resultados,pendencias},null,2));
if(aprovados!==resultados.length)process.exitCode=1;
