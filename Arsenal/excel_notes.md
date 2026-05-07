# CrowdStrike — Find Mac Users from a List of Usernames

## Scenario
You have a list of usernames and want to find out which ones are using macOS, along with their hostnames — using CrowdStrike Falcon export and Excel.

---

## Step 1: Export Mac Hosts from CrowdStrike

1. Go to **Falcon Console → Host Management → Hosts**
2. Filter by **Platform = macOS**
3. Click **Export** (top right) → save as CSV
4. This becomes your **Sheet2** in Excel

---

## Step 2: Set Up Excel

| Sheet1 Column | Contains |
|---|---|
| Column A | Usernames (e.g. `john.doe`) |
| Column B | OS ← pulled from Sheet2 |
| Column C | Hostname ← pulled from Sheet2 |

| Sheet2 Column | Contains |
|---|---|
| Column A | Hostname |
| Column F | OS / Platform |
| Column N | Username (Last User) |

> ⚠️ Both sheets must be in the **same Excel workbook** (as separate tabs). If your CrowdStrike export is a separate file, copy the sheet into the same workbook first.

---

## Step 3: Excel Formulas

**Column B — Get OS:**
```
=XLOOKUP(A2, Sheet2!N:N, Sheet2!F:F, "Not Found")
```

**Column C — Get Hostname:**
```
=XLOOKUP(A2, Sheet2!N:N, Sheet2!A:A, "Not Found")
```

**Count total Mac users:**
```
=COUNTIF(B2:B101, "<>Not Found")
```

---

## Common Errors & Fixes

| Error | Cause | Fix |
|---|---|---|
| `#VALUE!` | Formula has `LEFT/FIND("@")` but column A has usernames, not emails | Remove `LEFT(A2,FIND("@",A2)-1)` — just use `A2` directly |
| File browser popup | Sheet2 is in a different file, not the same workbook | Copy CrowdStrike sheet into the same workbook |
| `Not Found` for all rows | Username column in Sheet2 is not column N | Check the actual column and update `Sheet2!N:N` accordingly |

---

## Key CrowdStrike Fields for Mac Detection

| Field | Mac Indicator |
|---|---|
| `SystemManufacturer` | `Apple Inc.` |
| `Platform` | `Mac` |
| `Last User` | Username to match against your list |

---

*Scenario: Cross-referencing usernames against CrowdStrike Falcon host export to identify macOS users.*
