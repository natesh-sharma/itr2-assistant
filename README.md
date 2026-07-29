# ITR-2 Filing Assistant

A web-based tool that helps Indian salaried individuals file ITR-2 — especially those with **foreign stocks (RSU/ESPP), capital gains, and DTAA relief claims**.

Built with Python + Streamlit. Reads your tax documents, auto-fills schedules, computes taxes, and generates portal-ready exports.

## Who Is This For?

Salaried individuals who have:
- Company RSUs/ESPP held via Morgan Stanley, E*Trade, etc.
- Capital gains from Indian stocks and mutual funds
- Foreign dividend income (with US tax withheld)
- Income above Rs 50 lakhs requiring ITR-2

## Features

| Feature | Description |
|---|---|
| **Document Upload** | Upload Form 16, Form 12BA, broker P&L, Morgan Stanley statement, IRS Form 1042-S — with password-protected PDF support |
| **Auto-Fill Schedules** | Salary, Capital Gains (CG + 112A), Other Sources, Foreign Income (FSI), Foreign Assets (FA) |
| **DTAA Relief** | Automatically computes Section 90 relief for US dividends, guides you through Form 67 filing |
| **Schedule 112A CSV** | Generates portal-compatible CSV with correct BE/AE codes and non-breaking space headers |
| **SBI TT Rate Lookup** | Auto-fetches historical SBI TT Buying Rates for USD-INR conversion |
| **Regime Comparison** | Side-by-side Old vs New regime tax computation with recommendation |
| **Validation** | Pre-submission checks for common errors (FSI-OS mismatch, missing Schedule FA, Form 67 reminder) |
| **Export** | Download Schedule 112A CSV, tax summary, filing guide, Form 67 data |

## Quick Start

```bash
# Clone the repo
git clone https://github.com/yourusername/itr2-assistant.git
cd itr2-assistant

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

Open http://localhost:8501 in your browser.

## Documents You'll Need

| Document | Source | Required? |
|---|---|---|
| Form 16 (Part A & B) | Your employer's HR/payroll portal | Yes |
| Form 12BA | Your employer (perquisite statement) | Yes (if RSUs) |
| Tax P&L (Excel) | Zerodha Console / Groww / Angel One | Yes (if stocks/MF) |
| Morgan Stanley Statement | Morgan Stanley at Work portal | Optional (for Schedule FA) |
| IRS Form 1042-S | Morgan Stanley at Work portal | Optional (for DTAA relief) |

## How It Works

### Step 1: Upload Documents
Upload your tax documents. Password-protected PDFs (common for Form 16) are supported — just enter the password.

### Step 2: Review Auto-Filled Schedules
The app parses your documents and auto-fills:
- **Schedule Salary** — from Form 16 (Sec 17(1), 17(2), 17(3))
- **Schedule CG** — from broker P&L (STCG, LTCG, loss setoff)
- **Schedule OS** — interest and dividends
- **Schedule FSI/TR** — foreign dividends with DTAA relief
- **Schedule FA** — foreign asset holdings

### Step 3: Compare Tax Regimes
See a side-by-side comparison of Old vs New regime to pick the one that saves more tax.

### Step 4: Validate & Export
Run validation checks, then download:
- Schedule 112A CSV (upload directly to incometax.gov.in)
- Tax computation summary
- Form 67 data for DTAA relief

## Key Tax Concepts

### RSU Taxation in India
1. **At Vesting** — Market value is taxed as salary perquisite (Sec 17(2)). Already in Form 16.
2. **At Sale** — Gain from vesting price to sale price is capital gain.
3. **Dividends** — Taxed as "Other Sources". US withholds 25% — claim DTAA relief.

### DTAA Relief (Avoid Double Taxation)
1. File **Form 67** on incometax.gov.in BEFORE submitting ITR
2. Fill **Schedule FSI** — foreign income under "Other Sources" (NOT Salary)
3. Fill **Schedule TR** — claim relief under Section 90, Article 10
4. Relief = Lower of (US tax paid) or (Indian tax on that income)

### Schedule FA (Foreign Assets)
Mandatory for all residents holding any foreign asset. Non-disclosure attracts penalty under the Black Money Act. Report under Section A3 using SBI TT Buying Rate on 31st March for INR conversion.

### SBI TT Buying Rate
All USD-to-INR conversions must use the SBI TT Buying Rate (not Google/market rate). The app auto-fetches historical rates from a public archive.

## Project Structure

```
itr2-assistant/
├── app.py                    # Streamlit entry point
├── pages/
│   ├── 1_upload_documents.py # Document upload with PDF decryption
│   ├── 2_salary.py           # Schedule Salary
│   ├── 3_capital_gains.py    # Schedule CG + 112A
│   ├── 4_other_sources.py    # Schedule OS
│   ├── 5_foreign_income.py   # Schedule FSI + TR + DTAA
│   ├── 6_foreign_assets.py   # Schedule FA
│   ├── 7_regime_comparison.py# Old vs New regime
│   ├── 8_review.py           # Validation + tax computation
│   └── 9_export.py           # Download reports
├── utils/
│   ├── pdf_reader.py         # Password-protected PDF handling
│   ├── sbi_rates.py          # SBI TT Buying Rate lookup
│   ├── tax_calculator.py     # Tax slab computation
│   ├── form16_parser.py      # Form 16 parser
│   ├── form12ba_parser.py    # Form 12BA parser
│   ├── form1042s_parser.py   # IRS 1042-S parser
│   ├── broker_parser.py      # Zerodha/Groww P&L parser
│   ├── morgan_stanley_parser.py # Morgan Stanley parser
│   ├── schedule_112a.py      # 112A CSV generator
│   └── dtaa_calculator.py    # DTAA relief calculator
├── data/
│   └── tax_slabs.json        # Tax slab rates (updatable per FY)
└── requirements.txt
```

## Supported Brokers

- Zerodha (Tax P&L Excel from Console)
- More brokers coming soon (Groww, Angel One)

## Limitations

- This tool helps you **prepare** your ITR data — you still need to file on incometax.gov.in
- PDF parsing depends on document format — auto-extraction may need manual verification
- Tax slab data needs to be updated each financial year in `data/tax_slabs.json`
- Not a substitute for professional CA advice for complex cases

## Contributing

PRs welcome! Areas that need help:
- Support for more broker P&L formats (Groww, Angel One, ICICI Direct)
- Support for E*Trade statements (for non-IBM RSU holders)
- Improved PDF parsing accuracy
- Additional tax schedules (House Property, Business Income)

## License

MIT
