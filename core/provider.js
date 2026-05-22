const rpcHttp = process.env.RPC_HTTP;
const rpcWs = process.env.RPC_WS;

function createNoopProvider(kind, url) {
  return {
    kind,
    url,
    on() {},
    off() {},
    async getTransaction() {
      return null;
    },
  };
}

export function createProvider() {
  if (rpcWs) {
    return createNoopProvider('ws', rpcWs);
  }

  if (rpcHttp) {
    return createNoopProvider('http', rpcHttp);
  }

  return null;
}

export const provider = createProvider();
