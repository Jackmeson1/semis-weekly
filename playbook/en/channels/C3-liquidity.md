# C3 Liquidity plumbing

Layer: L2 · Main horizon: mid · Weight: lower than C1 and C2

## Explainer · Added

- **A simplified identity for the Fed's balance sheet**: assets ≈ bank reserves + the Treasury's cash account (TGA) + the reverse repo balance + currency in circulation, and so on. With assets unchanged, every extra dollar in the TGA or reverse repo means a dollar less in reserves.
- **TGA**: the Treasury's money held at the Fed. Bond issuance and tax receipts raise it and drain reserves from the banking system; government spending lowers it.
- **Reverse repo (ON RRP)**: money market funds park cash at the Fed. When the balance is high it is a buffer: balance-sheet runoff or a TGA rebuild can draw on it first without hitting reserves directly. Only once it is used up does the pressure fall on reserves.
- **Net liquidity = assets − TGA − reverse repo**: a rough measure the author often used in 2024 to see whether the amount of money in the system is growing or shrinking.

## What the author thinks

- In 2024 this was one of the author's main frameworks (40% of records in the first half of 2024 mention this layer).
- In 2025-11 the author lowered its weight, saying there was no longer any need to watch the TGA in liquidity analysis.
- In 2025-10 the author argued that bank regulation matters more than balance-sheet runoff, and that the key to dollar liquidity is changing the SLR rule.

## Signals

| ID | What | Threshold | Basis |
|---|---|---|---|
| S-L2-02 | 4-week change in net liquidity | watch −$150 billion, binding −$300 billion | Added |

## Common pitfalls

- An identity is not causation. A fall in reverse repo does not mean the same amount of money flowed into stocks.
- Fed assets and the TGA are both Wednesday levels; the reverse repo is daily and is taken on the same Wednesday.
  FRED's WTREGEN and WRESBAL are week averages, not Wednesday levels, so they are not mixed with WALCL.
- A binding reading on its own is not enough for level 2 to call "mid-horizon tightening"; it needs C1 or C2 to agree.

## What to write in this week's log

Same as C1: state, one line, evidence, change vs last week, explainer (3–5 sentences, using this week's numbers), deviations and uncertainty.
