# Additional Data Analysis Needs

## Critical Missing Data for Party Comparison

### 1. **Bill Sponsorship & Co-Sponsorship**

We need to link bills to their sponsors and co-sponsors to show:
- Which party introduces more bills
- Cross-party co-sponsorship (bipartisanship indicators)
- Success rate by party (bills that become law)

**Script Needed**: `analyze_bill_sponsors.py`

- Fetch bill sponsor data from Congress API
- Link sponsors to member party affiliations
- Calculate party success rates

### 2. **Actual Voting Records**

The House votes API isn't returning data. We need:
- Individual member votes on each bill
- Party line votes vs. defections
- Swing voter identification

**Script Needed**: `fetch_voting_records.py`

- Debug/fix the house-vote endpoint
- Try alternative endpoints (bill actions with votes)
- Parse vote data from bill details