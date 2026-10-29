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

## From the videos (the author, stated, 2024-05 to 2026-10, 83 videos)

What follows is the logic the author laid out in the weekly videos, recorded as they meant it. It does not mean the logic has been validated. The figures in brackets are the number of videos that support it and when. Where the author changed their position, the date is given. Items marked "added" are ours, not the author's. These are probability judgments, not laws. A conclusion is usually a chain of conditional judgments multiplied together; each link is likely but none is certain, and the author often says "most likely", "I think" or "fifty-fifty". Read each item as "under these conditions, it tends to go this way". When checking, look at which links have happened, one by one; do not test the whole conclusion as if it had to hold.

- **Read a basket, not just the TGA** (from 2025-11). The basket is SOFR minus IORB (near zero or negative means banks have excess cash; clearly positive means tightening), the weekly change in reserve balances, and a financial conditions index. Since 2024-05 the author has said net liquidity matters less than the 10-year yield.
- **For seasonal drains, look at the starting point** (4 videos). When net liquidity falls because of tax season, or because the TGA is rebuilt after a debt-ceiling episode, the effect may "not be large" if the starting point was excess cash. The author's rule of thumb is that every extra 100 billion in the TGA lifts the spread between repo rates and OIS by about 4 to 5bp. Spending down the TGA during a debt-ceiling period adds liquidity, and the drain comes only when it is rebuilt.
- **Looser bank capital rules are a tailwind with a date on it** (8 videos). From 2025-07 to 2026-03 the author treated it as the biggest source of liquidity for the next year. From 2026-06-30 the author said banks will pay the extra capital out as dividends, which turns into excess reserves, and that by year-end there will not be a flood like the one in April. In a liquidity shock, ask whether any new loosening is left to provide a floor.

## What to write in this week's log

Same as C1: state, one line, evidence, change vs last week, explainer (3–5 sentences, using this week's numbers), deviations and uncertainty.
