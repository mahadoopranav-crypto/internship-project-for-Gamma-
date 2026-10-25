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
| source_file | PDF the row was extracted from |
| supplier, customer | Issuer and recipient of the invoice |
| invoice_number | Invoice number as printed |
| invoice_date, due_date, event_date | Dates (YYYY-MM-DD), blank where the invoice has none |
| customer_reference, payment_terms | As printed, blank where absent |
| currency | MUR or USD |
| subtotal, discount, delivery, tax_rate, tax_amount, total | Amounts in the invoice currency |
| deposit, balance_due | Deposit already paid and amount still owed |
| line_count | Number of line items |
| lines_match_subtotal | True if the line items add up to the printed subtotal |
| total_reconciles | True if subtotal - discount + delivery + tax equals the printed total |

## Sheet: Line items (one row per invoice line)

source_file, invoice_number, line, item_code, description, quantity, unit_price, discount_percent, discount_amount, line_total. Fields an invoice does not have are left blank.

## Method

- Text is extracted from each PDF with pdfplumber.
- The five invoices use five different layouts (English and French, MUR and USD, different number formats), so each layout has its own parser.
- Amounts written as `2 250,00` or `1,200.00` are converted to plain numbers, and dates to YYYY-MM-DD.
- All five invoices pass both checks above, and every line item was also compared against the text of its PDF.
- Names of individual people printed on the invoices are not included.
