# Task 5: Fixed-price contracts, rising costs and how work is won

A contractor that agrees its price before it knows its costs carries every cost rise itself. In Mauritius those rises have been large lately: the labour part of the official construction cost index went up 8.5% in January 2024 and another 11.5% in July 2024, after materials rose 10% in 2021 and 17.8% in 2022. On a fixed-price contract none of that can be billed on.

But fixed prices aren't the whole problem. A business that can change its prices gets through the same cost rises fine. What decides it is pricing power, and for a contractor that comes from how the work is won. In a lowest-price tender you take the price the market gives you.

## What Granite Construction shows

Granite (NYSE: GVA) is a US contractor with a construction arm and a materials arm, so it's one company facing the same costs with two ways of pricing. I pulled 15 years of its annual filings from the SEC.

| Years | Share of order book on fixed price | Construction margin | Materials margin | Profit revised up or down on projects |
|---|---|---|---|---|
| 2009 to 2015 | 66% | 12.4% | 6.9% | +$266M |
| 2016 to 2023 | 50% | 9.5% | 14.4% | -$809M |
| 2024 to 2025 | 34% | 15.0% | 15.8% | +$7M |

Fixed prices were fine while costs behaved. In 2009 to 2015 two thirds of Granite's work was fixed price and it still made 12.4% on construction. Then costs ran past the bids, and between 2016 and 2023 Granite wrote $809M of expected profit off its projects, while its materials side, which could put prices up, kept its margin. Construction recovered once less of the work was fixed price and more clients started choosing their contractor early, on track record, instead of taking the lowest bid (CM/GC and CMAR contracts). Granite's 2020 and 2021 filings describe that shift in its clients.

## Two tools, and why both

The quick fix is to stop absorbing cost rises on the bids going out now: price them in, or write a price adjustment clause into the contract. `escalation_check.py` does those sums using the official Mauritius cost index.

The catch is that a client running a lowest-price tender won't accept a higher price or an escalation clause when the next bidder doesn't ask for one. It only works with clients who want you in particular. Having more of those clients is the slower fix, and it comes down to relationships with the people who make the decisions, kept up over years, mostly by account managers remembering things and following up. `kdm_touchpoints.py` helps with that.

## escalation_check.py

You give it a list of contracts or bids, each with its value, start month, length, how its cost splits between labour, materials, plant hire and transport, and the margin you're aiming for. It projects those costs from the Statistics Mauritius Construction Price Index and tells you how much margin each contract loses if the price stays fixed, what price would keep the margin, and the price adjustment formula to put in the contract instead.

```
python escalation_check.py contracts_example.csv
python escalation_check.py my_bids.csv --update --years 3
```

The contracts in `contracts_example.csv` are made up. On the 24-month road works bid, a 5% target margin falls to 0.2% if the price stays fixed; quoting MUR 840M instead of MUR 800M keeps it, and so, near enough, does adding the clause. The index tracks the inputs for building a house, so for road and civil works it's only an approximation.

## kdm_touchpoints.py

Account managers keep two files: the key decision makers they deal with, and notes on what each one has told them, like a pet's birthday that came up over lunch, a half marathon they're training for, a tender closing date or the anniversary of a handover. The script turns those notes into a calendar file you can import into Outlook or Google, with a reminder a few working days before each date and a draft message to send. It also flags anyone nobody has spoken to in 60 days, and prints a short brief on a person before a meeting.

```
python kdm_touchpoints.py --start 2026-10-26
python kdm_touchpoints.py --brief C001
python kdm_touchpoints.py --forget C003
```

A draft looks like this: "Hi Nadia, if I remember right Rex turns 5 on Tuesday. Hope there is an extra treat on the day. Pranav"

A few limits are built in. Public-sector contacts never get gifts, only messages, because of the Prevention of Corruption Act. Gifts to private clients are capped at MUR 2,000 unless you change `--gift-cap`. Every note has to say where it came from, and notes about health, religion, politics and similar topics are refused, to stay within the Data Protection Act 2017. `--forget` deletes everything held on a person if they ask. Everyone in the sample files is made up.

## Files

| File | What it is |
|---|---|
| `Task5_EDA.ipynb` | The analysis: scraping, charts and conclusions |
| `escalation_check.py`, `contracts_example.csv` | The pricing tool and its example input |
| `kdm_touchpoints.py`, `kdm_contacts.csv`, `kdm_notes.csv` | The relationship tool and its sample input |
| `data/granite_10k_summary.csv` | Granite figures by year, 2009 to 2025, built by the notebook |
| `data/mauritius_copi.csv` | The Statistics Mauritius cost index by month from April 2019 (July to September 2020 is missing) |

## Sources

Granite's figures come from its 10-K filings on SEC EDGAR. The notebook reads the segment figures from the XBRL data and the fixed-price share and project revisions from the text. The SEC wants a contact email in every request, and it's set at the top of the notebook. The cost index comes from the quarterly Construction Price Index releases of Statistics Mauritius.

The notebook and `escalation_check.py` need pandas, requests, beautifulsoup4, matplotlib, openpyxl and xlrd. `kdm_touchpoints.py` runs on plain Python.
