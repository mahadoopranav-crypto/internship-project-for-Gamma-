# Task 4: PDF Data Extraction

Data extracted from the five invoice PDFs supplied for the assessment (52 line items in total).

## Files

| File | Description |
|---|---|
| `Task4.xlsx` | Extracted data, with two sheets: `Invoices` and `Line items` |
| `Task4_extraction.ipynb` | Python notebook (pdfplumber and pandas) that reads the PDFs and writes `Task4.xlsx` |

To rerun, put the five PDFs in a folder called `pdfs` next to the notebook and run all cells. The source PDFs are not included in this repository.

## Sheet: Invoices (one row per invoice)

| Column | Description |
|---|---|
| source file | PDF the row was extracted from |
| supplier, customer | Issuer and recipient of the invoice |
| invoice number | Invoice number as printed |
| invoice date, due date, event date | Dates (YYYY-MM-DD), blank where the invoice has none |
| customer reference, payment terms | As printed, blank where absent |
| currency | MUR or USD |
| subtotal | Sum of the line items |
| tax amount, tax rate | VAT or sales tax charged, and its rate in % (15 for the MUR invoices, 0 for the USD invoices) |
| delivery | Delivery or other charges |
| discount | Discount applied to the whole invoice |
| total | Total as printed on the invoice |
| deposit, deposit date | Deposit already paid and the date it was received |
| balance due | Amount still owed |

## Sheet: Line items (one row per invoice line)

source file, invoice number, line, item code, description, quantity, unit price, discount percent, discount amount, line total. Fields an invoice does not have are left blank.

## Method

- Text is extracted from each PDF with pdfplumber.
- The five invoices use five different layouts (English and French, MUR and USD, different number formats), so each layout has its own parser.
- Amounts written as `2 250,00` or `1,200.00` are converted to plain numbers, and dates to YYYY-MM-DD.
- The notebook checks every invoice: the line items must add up to the subtotal, and subtotal - discount + delivery + tax must equal the printed total. All five invoices pass.
