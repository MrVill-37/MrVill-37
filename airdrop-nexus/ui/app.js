const ADDRESS_RE = /^0x[a-fA-F0-9]{40}$/;
const NETWORKS = new Set(["ethereum", "base", "arbitrum", "zksync", "bnb"]);

function parseWallets(text) {
  const rows = text.split(/\n/).map((line) => line.trim()).filter(Boolean);
  const invalid = rows.filter((row) => !ADDRESS_RE.test(row));
  return { wallets: [...new Set(rows)], invalid };
}

function safeJsonParse(raw) {
  try {
    return [JSON.parse(raw), null];
  } catch (err) {
    return [null, err.message || "Invalid JSON"];
  }
}

function evaluateEligibility(wallets, rules) {
  const allowlists = rules?.rules?.allowlists || {};
  const result = {};
  wallets.forEach((wallet) => {
    result[wallet] = {};
    for (const [campaign, list] of Object.entries(allowlists)) {
      const normalized = new Set((list || []).filter((x) => ADDRESS_RE.test(x)));
      result[wallet][campaign] = normalized.has(wallet);
    }
  });
  return result;
}

function buildPlan(inventory, vault, gasReserve) {
  if (!ADDRESS_RE.test(vault)) throw new Error("Invalid vault address.");
  if (gasReserve < 0) throw new Error("Gas reserve must be non-negative.");

  const plan = {};
  for (const [wallet, assets] of Object.entries(inventory)) {
    if (!ADDRESS_RE.test(wallet)) throw new Error(`Invalid wallet in inventory: ${wallet}`);
    plan[wallet] = [];

    for (const asset of assets) {
      const network = (asset.network || "").toLowerCase();
      const kind = (asset.kind || "").toLowerCase();
      const token = String(asset.token || "");
      const amount = Number(asset.amount);

      if (!NETWORKS.has(network)) throw new Error(`Unsupported network: ${network}`);
      if (!["eth", "erc20", "nft"].includes(kind)) throw new Error(`Unsupported asset kind: ${kind}`);
      if (!Number.isFinite(amount) || amount < 0) throw new Error("Invalid asset amount.");

      if (kind === "eth") {
        const sweep = Math.max(0, amount - gasReserve);
        if (sweep > 0) {
          plan[wallet].push({ network, kind, token: "ETH", amount: sweep.toString(), note: "gas reserve deducted" });
        }
      } else {
        if (!["erc20", "nft"].includes(kind) || !ADDRESS_RE.test(token)) {
          throw new Error(`Invalid token address for ${kind}.`);
        }
        if (amount > 0) {
          plan[wallet].push({
            network,
            kind,
            token,
            amount: amount.toString(),
            note: "plan only - explicit owner consent + signer approval required"
          });
        }
      }
    }
  }
  return plan;
}

const walletInput = document.getElementById("walletInput");
const walletSummary = document.getElementById("walletSummary");
const rulesInput = document.getElementById("rulesInput");
const eligibilityResult = document.getElementById("eligibilityResult");
const inventoryInput = document.getElementById("inventoryInput");
const vaultAddress = document.getElementById("vaultAddress");
const gasReserve = document.getElementById("gasReserve");
const planResult = document.getElementById("planResult");

document.getElementById("validateWallets").addEventListener("click", () => {
  const { wallets, invalid } = parseWallets(walletInput.value);
  if (invalid.length) {
    walletSummary.className = "err";
    walletSummary.textContent = `Invalid (${invalid.length}): ${invalid.slice(0, 2).join(", ")}`;
    return;
  }
  walletSummary.className = "ok";
  walletSummary.textContent = `Validated ${wallets.length} wallet(s).`;
});

document.getElementById("checkEligibility").addEventListener("click", () => {
  const { wallets, invalid } = parseWallets(walletInput.value);
  if (invalid.length) {
    eligibilityResult.className = "output err";
    eligibilityResult.textContent = "Please fix invalid wallet addresses first.";
    return;
  }
  const [rules, err] = safeJsonParse(rulesInput.value || "{}");
  if (err) {
    eligibilityResult.className = "output err";
    eligibilityResult.textContent = `Rules JSON error: ${err}`;
    return;
  }
  const result = evaluateEligibility(wallets, rules);
  eligibilityResult.className = "output ok";
  eligibilityResult.textContent = JSON.stringify(result, null, 2);
});

document.getElementById("buildPlan").addEventListener("click", () => {
  const [inventory, err] = safeJsonParse(inventoryInput.value || "{}");
  if (err) {
    planResult.className = "output err";
    planResult.textContent = `Inventory JSON error: ${err}`;
    return;
  }

  try {
    const plan = buildPlan(inventory, vaultAddress.value.trim(), Number(gasReserve.value));
    planResult.className = "output ok";
    planResult.textContent = JSON.stringify(plan, null, 2);
  } catch (e) {
    planResult.className = "output err";
    planResult.textContent = e.message;
  }
});
