import assert from 'node:assert/strict';
import { criarSenha, escolherProxima, formatarHora } from '../../../frontend/src/utils/senhas.js';
import { TIPOS, ORDEM_TOTEM } from '../../../frontend/src/data/tipos.js';

process.env.TZ = 'America/Sao_Paulo';
const data = new Date('2026-10-04T09:30:00-03:00');
const resultados = [];
function caso(id, descricao, executar) {
  try { executar(); resultados.push({id, descricao, status: 'APROVADO'}); }
  catch (erro) { resultados.push({id, descricao, status: 'REPROVADO', erro: erro.message}); }
}
const senha = (tipo, n) => criarSenha(tipo, n, data);
caso('U01', 'Numeração SP com data e três dígitos', () => assert.equal(senha('SP',1).numero,'261004-SP001'));
caso('U02', 'Numeração SG com sequência própria recebida pela função', () => assert.equal(senha('SG',1).numero,'261004-SG001'));
caso('U03', 'Numeração SE com sequência própria recebida pela função', () => assert.equal(senha('SE',1).numero,'261004-SE001'));
caso('U04', 'Sequência 9 com preenchimento de zeros', () => assert.equal(senha('SP',9).numero,'261004-SP009'));
caso('U05', 'Sequência 99 com preenchimento de zeros', () => assert.equal(senha('SP',99).numero,'261004-SP099'));
caso('U06', 'Sequência 999 preserva três dígitos', () => assert.equal(senha('SP',999).numero,'261004-SP999'));
caso('U07', 'Tipo e instante da emissão registrados', () => assert.deepEqual(senha('SE',2),{numero:'261004-SE002',tipo:'SE',emitidaEm:'2026-10-04T12:30:00.000Z'}));
caso('U08', 'Fila vazia retorna null', () => assert.equal(escolherProxima([]),null));
caso('U09', 'SP é escolhida antes de SE e SG na regra simplificada', () => { const sp=senha('SP',1); assert.equal(escolherProxima([senha('SG',1),senha('SE',1),sp]),sp); });
caso('U10', 'SE é escolhida antes de SG quando não há SP', () => { const se=senha('SE',1); assert.equal(escolherProxima([senha('SG',1),se]),se); });
caso('U11', 'SG é escolhida quando as outras filas estão vazias', () => {const sg=senha('SG',1);assert.equal(escolherProxima([sg]),sg);});
caso('U12', 'Dentro do mesmo tipo vale a chegada na lista', () => {const primeira=senha('SP',2);assert.equal(escolherProxima([primeira,senha('SP',1)]),primeira);});
caso('U13', 'Escolha não altera a fila original', () => {const fila=[senha('SG',1),senha('SP',1)];const antes=structuredClone(fila);escolherProxima(fila);assert.deepEqual(fila,antes);});
caso('U14', 'Hora exibida em horas e minutos no fuso definido', () => assert.equal(formatarHora('2026-10-04T12:30:00.000Z'),'09:30'));
caso('U15', 'Data recebida altera o prefixo da senha', () => assert.equal(criarSenha('SG',1,new Date('2026-10-05T09:00:00-03:00')).numero,'261005-SG001'));
caso('U16', 'Totem oferece apenas os três tipos previstos', () => {assert.deepEqual(Object.keys(TIPOS).sort(),['SE','SG','SP']);assert.deepEqual([...ORDEM_TOTEM].sort(),['SE','SG','SP']);});
const aprovados=resultados.filter(r=>r.status==='APROVADO').length;
console.log(JSON.stringify({suite:'Gabriel Luann — testes unitários',executadoEm:new Date().toISOString(),ambiente:{node:process.version,fuso:process.env.TZ},total:resultados.length,aprovados,reprovados:resultados.length-aprovados,resultados},null,2));
if(aprovados!==resultados.length) process.exitCode=1;
