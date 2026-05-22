import { fetchDexPrice } from './priceFeeds.js';

export async function scanPrices(pair, exchanges) {
  const entries = await Promise.all(
    exchanges.map(async (exchange) => [exchange.name, await fetchDexPrice(exchange.name, pair)])
  );

  return Object.fromEntries(entries);
}
