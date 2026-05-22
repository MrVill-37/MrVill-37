export function createWallet() {
  const pk = process.env.PRIVATE_KEY;
  if (!pk) {
    return null;
  }

  return {
    address: process.env.WALLET_ADDRESS ?? '0xSIMULATEDWALLET',
    privateKeyLoaded: true,
  };
}

export const wallet = createWallet();
