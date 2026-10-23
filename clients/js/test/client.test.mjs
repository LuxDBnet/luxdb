import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {Client, ApiError, TransportError} from '../index.js';
import {OPERATIONS} from '../generated.js';
const reply = (data, status=200, headers={}) => new Response(JSON.stringify(data), {status, headers});
const fixture = JSON.parse(readFileSync(new URL('../../../tests/fixtures/synthetic-response.json', import.meta.url))).response;
function fake(response=reply(fixture)) {
  const calls=[];
  return {calls, fetch: async (...args) => {calls.push(args); return response;}};
}
test('constructing a client does not call fetch; demo response charge is preserved', async () => {
  const f=fake(); const c=new Client({fetch:f.fetch}); assert.equal(f.calls.length,0);
  const result=await c.search({q:'synthetic',page:'1'});
  assert.equal(result.credits_charged,0);assert.equal(f.calls.length,1);
  const [url,options]=f.calls[0];assert.equal(options.headers['X-API-Key'],'demo');
  assert.equal(options.redirect,'error');assert.equal(options.credentials,'omit');assert.equal(options.cache,'no-store');
  assert.equal(new URL(url).searchParams.get('q'),'synthetic');
});
test('paid keys require literal explicit opt-in and are absent from object serialisation', () => {
  for (const allowPaid of [undefined,false,1,'true']) assert.throws(()=>new Client({apiKey:'SYNTHETIC-KEY',allowPaid}),TypeError);
  const c=new Client({apiKey:'SYNTHETIC-KEY',allowPaid:true,fetch:fake().fetch});
  assert.ok(!JSON.stringify(c).includes('SYNTHETIC-KEY'));
  for (const apiKey of ['',null,'bad\nheader']) assert.throws(()=>new Client({apiKey}),TypeError);
});
test('every operation uses one request, and public openapi carries no key', async () => {
  const params={article:{codes:'SYNTHETIC-ITEM'},search:{},changes:{since:'synthetic-week'},family:{id:'nvprod0v'},resolve:{url:'synthetic-link'},index:{},snapshot:{},openapi:{}};
  assert.equal(Object.keys(OPERATIONS).length,8);
  for(const [method,p] of Object.entries(params)) {
    const f=fake();await new Client({fetch:f.fetch})[method](p);assert.equal(f.calls.length,1);
    assert.equal('X-API-Key' in f.calls[0][1].headers,method!=='openapi');
  }
});
test('batch and parameter checks happen before fetch; encoding cannot change origin', async () => {
  const f=fake();const c=new Client({fetch:f.fetch});
  for(const params of [{codes:''},{codes:'a,,b'},{codes:Array(21).fill('synthetic').join(',')},{codes:4},{codes:'a',extra:'b'}]) await assert.rejects(c.article(params),TypeError);
  await assert.rejects(c.family({id:'bad-family'}),TypeError);assert.equal(f.calls.length,0);
  await c.resolve({url:'synthetic & ? # /',brand:'synthetic'});
  assert.equal(new URL(f.calls[0][0]).searchParams.get('url'),'synthetic & ? # /');
  assert.equal(new URL(f.calls[0][0]).origin,'https://luxdb.net');
});
test('errors expose only approved code, mode and retry delay, with no retry',async()=>{
  const f=fake(reply({code:'member_limit_reached',secret:'SYNTHETIC-SECRET'},402,{'Retry-After':'17'}));
  await assert.rejects(new Client({fetch:f.fetch}).article({codes:'SYNTHETIC-ITEM'}),e=>e instanceof ApiError && e.status===402 && e.code==='member_limit_reached' && e.retryAfterSeconds===17 && !String(e).includes('SYNTHETIC-SECRET'));
  assert.equal(f.calls.length,1);
  for(const [status,body,code,mode] of [[503,{code:'maintenance',mode:'maintenance'},'maintenance','maintenance'],[429,{code:'rate_limited',retry_after_seconds:2},'rate_limited',null],[500,{code:'SYNTHETIC-SECRET',mode:'SYNTHETIC-SECRET'},'http_error',null]]) {
    await assert.rejects(new Client({fetch:fake(reply(body,status)).fetch}).snapshot(),e=>e.code===code && e.mode===mode);
  }
});
test('redirects and 304 are refused without following or retrying',async()=>{
  for(const status of [301,302,307,308,304]) {
    const f=fake(new Response(null,{status,headers:{Location:'https://luxdb.net/'}}));
    await assert.rejects(new Client({fetch:f.fetch}).snapshot(),TransportError);assert.equal(f.calls.length,1);
  }
});
test('transport and body errors cannot leak message, cause, key or query',async()=>{
  const c=new Client({fetch:async()=>{throw new Error('SYNTHETIC-KEY SYNTHETIC-QUERY');}});
  await assert.rejects(c.search({q:'SYNTHETIC-QUERY'}),e=> e instanceof TransportError && e.cause===undefined && !e.stack.includes('SYNTHETIC-'));
  for(const value of ['not JSON','[]','null']) await assert.rejects(new Client({fetch:fake(new Response(value)).fetch}).snapshot(),TransportError);
});
test('timeout aborts one request without retries',async()=>{
  let calls=0;
  const transport=(_url,{signal})=>new Promise((_resolve,reject)=>{calls++;signal.addEventListener('abort',()=>reject(new Error('synthetic timeout')),{once:true});});
  await assert.rejects(new Client({timeoutMs:5,fetch:transport}).snapshot(),TransportError);assert.equal(calls,1);
  for(const timeoutMs of [0,-1,Infinity,NaN,true,2147483648]) assert.throws(()=>new Client({timeoutMs}),TypeError);
});
test('oversize streamed response is cancelled',async()=>{
  let cancelled=false;
  const stream=new ReadableStream({start(c){c.enqueue(new Uint8Array(8*1024*1024+1));},cancel(){cancelled=true;}});
  await assert.rejects(new Client({fetch:fake(new Response(stream)).fetch}).snapshot(),TransportError);assert.equal(cancelled,true);
});
test('response credits are never inferred from method or number of codes',async()=>{
  const f=fake(reply({credits_charged:0,results:{}}));
  const result=await new Client({fetch:f.fetch}).article({codes:'SYNTHETIC-A,SYNTHETIC-B'});assert.equal(result.credits_charged,0);
});
test('live null values pass unchanged; extra error keys survive only in explicit details',async()=>{
  const response=await new Client({fetch:fake(reply({results:[{price_usd_band:null,dimensions:{height_cm:null,height_in:null}}]})).fetch}).search();
  assert.equal(response.results[0].price_usd_band,null);assert.equal(response.results[0].dimensions.height_cm,null);
  for(const [status,code] of [[404,'not_found'],[405,'method_not_allowed']]){
    const body={code,error:'synthetic',hint:'SYNTHETIC-PRIVATE',batch_max:20,brands:[],plan:'synthetic',sandbox:true,remaining_today:0};
    await assert.rejects(new Client({fetch:fake(reply(body,status)).fetch}).snapshot(),error=>error instanceof ApiError && error.code===code && error.details.hint==='SYNTHETIC-PRIVATE' && error.details.remaining_today===0 && !JSON.stringify(error).includes('SYNTHETIC-PRIVATE') && !String(error).includes('SYNTHETIC-PRIVATE'));
  }
});
test('generated declarations include exactly the documented nullable compatibility',()=>{
  const types=readFileSync(new URL('../index.d.ts',import.meta.url),'utf8');
  assert.match(types,/"price_usd_band"\??: \(string \| null\)/);
  assert.match(types,/"height_cm"\??: \(number \| null\)/);
  assert.match(types,/"height_in"\??: \(number \| null\)/);
});
