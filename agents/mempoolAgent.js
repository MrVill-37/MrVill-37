export function startMempoolMonitor(provider, { watchedAddress, onRelevantTx }) {
  if (!provider || typeof provider.on !== 'function') {
    return { stop: () => {} };
  }

  const handler = async (txHash) => {
    const tx = await provider.getTransaction(txHash);
    if (!tx || !tx.to || !watchedAddress) return;

    if (tx.to.toLowerCase() === watchedAddress.toLowerCase()) {
      onRelevantTx?.(tx);
    }
  };

  provider.on('pending', handler);
  return {
    stop: () => provider.off('pending', handler),
  };
}
