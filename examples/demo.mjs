/** Synthetic offline example. No live request or paid record. */
import {Client} from '../clients/js/index.js';
import {readFileSync} from 'node:fs';
const synthetic = JSON.parse(readFileSync(new URL('../tests/fixtures/synthetic-response.json', import.meta.url))).response;
const client = new Client({fetch: async () => new Response(JSON.stringify(synthetic))});
const response = await client.search({q: 'synthetic', page: '1'});
console.log('Synthetic offline response; credits charged:', response.credits_charged);
