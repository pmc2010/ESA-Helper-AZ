# ClassWallet 2026/2027 UI Migration Notes

## ⏭️ Resume here if this session gets interrupted

**Update 2026-07-24 ~22:25: WORKING.** Live retry succeeded end-to-end with the delete-confirmation
fix in place - a real Reimbursement (multi-item receipt collapsed to one line item, invoice +
curriculum files, category/amount/comment overwritten) submitted successfully through ESA
Helper. Both Direct Pay and Reimbursement are now confirmed working against the redesigned
ClassWallet UI. Code committed and pushed to GitHub as of this update.

**Update 2026-07-24 ~22:10: Reimbursement rewritten too, not yet live-tested.** Turns out
Reimbursement was broken by the exact same redesign - confirmed via a second live walkthrough
(see "Reimbursement" section below). It uses the *same* 4-step wizard component as Direct Pay
(`#/reimbursements/wizard/...` instead of `#/direct_pay/wizard/...`), same Manage Expenses field
names, minus the "User Name" field. Given how much was shared, the fix:
- Renamed the genuinely-shared wizard-step methods to drop the "direct_pay"-specific naming:
  `upload_direct_pay_invoice`→`upload_wizard_invoice`, `select_direct_pay_purse`→`select_wizard_purse`,
  `fill_direct_pay_review`→`fill_wizard_review`, `submit_direct_pay`→`submit_wizard` (the
  classwallet.py instance methods only - `SubmissionOrchestrator.submit_direct_pay` in
  automation.py, the public per-flow API, was NOT renamed and still exists separately from
  `submit_reimbursement`), `_select_direct_pay_line_item_category`→`_select_line_item_category`.
- Deleted all the old pre-redesign Reimbursement code: `upload_files`, `select_expense_category`
  (274 lines of Arizona-ESA-checkbox/category fallback-selector logic for the old single-page
  purse+category step), `fill_po_and_comment`, the old `start_reimbursement(store_name, amount)`,
  and the old `submit_reimbursement()` instance method - all fully superseded.
- Added `fill_reimbursement_expenses()` + `_collapse_to_single_line_item()`: unlike Direct Pay's
  single pre-existing line item, IDP can split a Reimbursement receipt into multiple rows (one per
  purchased item) - since ESA Helper's form only models one lump-sum amount/category per
  submission, extra rows are deleted (via each row's "Remove expense" button, aria-label-matched,
  removing from the end to dodge index-shifting) and the remaining row is fully overwritten:
  price = ESA Helper's amount, description = ESA Helper's comment, category = ESA Helper's
  category. Shipping/discount/tax are always zeroed (force-set, same masked-input fix as
  everything else) so the total matches the amount exactly regardless of what the scan picked up
  off the receipt.
- `SubmissionOrchestrator.submit_reimbursement()` rewritten to the same 7-step sequence as Direct
  Pay's orchestrator, with one addition: `files` are split by primary key `invoice`, falling back
  to `receipt` if no `invoice` key is present (Direct Pay only ever had `invoice`), since
  Reimbursement's required file types vary by category (receipt, invoice, attestation,
  curriculum per `CLAUDE.md`) - **this fallback is an assumption, not yet confirmed against a
  receipt-only (no invoice) submission.**
- New `tests/test_reimbursement.py` (7 tests, mirrors `test_direct_pay.py`'s structure). Full
  suite: 126/126 passing. **Not yet tried live** - this is written from a real DOM walkthrough
  (confirmed field names, confirmed same wizard) but the actual code hasn't been run against
  ClassWallet yet, only unit-tested against mocks.

Assumptions carried over unverified from the old code because we didn't specifically re-check
them this time (low risk, but flagging): the `button[data-test='start-reimbursement']` selector
for the "Start a new Reimbursement" button on the ClassWallet home page (unrelated to the wizard
redesign, so likely unchanged) and the `button[aria-label='Remove expense']` selector (this one
*was* confirmed live via JS inspection, see below - not actually unverified, kept here as the
first thing to check if row-deletion fails).

**Update 2026-07-24 ~22:20**: First live retry hit a new snag - clicking "Remove expense" opens
an "Are you sure you want to delete this item?" confirmation dialog that has to be confirmed via
its "Yes, Delete Item" button, or the row never actually gets removed. Fixed:
`_collapse_to_single_line_item()` now confirms each deletion (text-match on "yes, delete", same
pattern as Continue/Submit). Retried live immediately after this fix and it worked end-to-end -
see the "WORKING" update at the top of this file.

## Reimbursement wizard - confirmed via live walkthrough 2026-07-24 22:00

Same wizard, same field names as Direct Pay's Manage Expenses page (`vendor`, `poNumber`,
`rows[N].description/quantity/price`, `shipping`, `discount`, `tax`), confirmed via
`document.querySelectorAll('input, textarea')` on `https://app.classwallet.com/#/reimbursements/wizard/2-manage-expenses`.
Differences from Direct Pay:
- No `studentName` field at all (Details section only has Vendor*, Transaction Date, Invoice Number).
- Section header text is "Reimbursement Details" instead of "Direct Pay Details" (cosmetic only,
  doesn't affect selectors since nothing there is targeted by text).
- IDP scanned 3 line-item rows from a single multi-item receipt in the observed test (vs. Direct
  Pay's invoice which always produced exactly 1 row) - this is what motivated the
  collapse-to-single-row approach in `fill_reimbursement_expenses`.
- Each row's delete control is `button[aria-label='Remove expense']` (one per row) - confirmed via
  live JS inspection, not previously seen on the Direct Pay page (Direct Pay's test never had a
  second row to delete, so this control may exist there too but was never exercised/confirmed).

## Direct Pay - WORKING (previous session)

**Update 2026-07-24 ~14:30: WORKING.** Third live attempt succeeded end-to-end - the real invoice
was submitted successfully through ESA Helper's Direct Pay flow. All four issues found across the
first three attempts (wizard reorder, clear()-append bug, calendar-picker popup blocking the
date field, click-timing race after closing that popup) are fixed and confirmed live. Code
committed and pushed to GitHub as of this update.

This one successful run exercised the entire flow including purse selection, review, and final
submit, so those selectors are now confirmed working too - not just the Manage Expenses step.
Remaining known gaps (not blockers, just not yet exercised): multi-line-item submissions, and
PDF invoices (only a JPG has been tested so far). See "Not done yet" section below.

**As of 2026-07-24 ~14:00**: First live attempt (first version of the rewrite) got most of the
way through but hit a real bug: overwriting the pre-filled Unit Price field turned $2,047.50 into
$2,047,502,089.29, and the same thing happened to the invoice number field. Root cause: Selenium's
`element.clear()` doesn't reset ClassWallet's masked/React-controlled inputs' internal state, so
`clear()` + `send_keys()` silently *appends* instead of overwriting. Fixed with a new
`_force_set_field_value()` helper (real select-all + delete keystrokes instead of `.clear()`),
and implemented the exact per-field rules the user specified:
- **Vendor, User Name**: always overwritten with ESA Helper's known values.
- **Line item amount**: always overwritten with ESA Helper's amount.
- **Invoice/quote number**: keep ClassWallet's scanned value if present; only fill with ESA
  Helper's `po_number` if blank.
- **Transaction date**: keep ClassWallet's scanned date if it's today or earlier; otherwise
  (blank/unparseable/future) overwrite with today's date.

Code updated in `app/classwallet.py` (`_force_set_field_value`, `_fill_transaction_date_if_needed`,
`fill_direct_pay_expenses` now takes `vendor_name` too) and `app/automation.py`. Server
auto-reloaded (confirmed via `/tmp/esa-helper-error.log`, no restart needed). 119/119 tests pass.
**Nothing committed to git yet.** Still needs a fresh live retry to confirm this actually fixes
the overwrite bug (only the first attempt, which had the bug, has been tried live so far).

Next action: user is about to retry the real invoice submission (due 2026-07-27, ~$2,047.50 —
see git-ignored `data/vendors.json`/`students.json` for real details, not repeated here per the
privacy rules below) through ESA Helper's UI at http://127.0.0.1:5000/. Watch
`logs/automation_*.log` (today's file) for the run — if it fails, the browser window is left open
per existing behavior, so the failing page's DOM can be inspected directly.

If it works end-to-end: ask whether to commit the changes, then update `CLAUDE.md`'s "Direct Pay
Submission Workflow" section (open item #5 below).

**Status**: Implemented and confirmed working end-to-end against a real ClassWallet Direct Pay
submission on 2026-07-24. `app/classwallet.py` and `app/automation.py` were rewritten to match
the new 4-step wizard; `tests/test_direct_pay.py` updated accordingly (119/119 tests pass).

## Background

Starting ~July 2026, ClassWallet rolled out a "Platform Enhancement" for the 2026/2027 school
year (announced via an in-app modal on first login, and referenced in an email dated 2026-07-22).
Two changes broke our Direct Pay automation:

1. **Intelligent Document Processing (IDP)** — uploaded invoices/receipts are now scanned by an
   AI/OCR step that extracts vendor, transaction date, invoice number, and line items automatically.
2. **Line-item categorization** — Direct Pay (and Reimbursement) submissions are no longer a single
   lump-sum amount + single expense category. Each submission now has one or more line-item rows,
   each with its own description, expense category, quantity, and unit price (same model the
   Marketplace flow already used).

As a result, ClassWallet **reordered the entire Direct Pay wizard**. Symptom seen in
`logs/automation_*.log`: `start_direct_pay()` in `app/classwallet.py` times out waiting for
`id="amount"` (app/classwallet.py:1407-1409) because that field no longer exists on the page that
appears right after vendor selection.

## Old wizard order (what the current code assumes)

1. Search vendor → click Pay
2. Enter amount (`input#amount`) → click Next (`#next`)
3. Upload files (`input[type=file]`) → handle image editor "Save" modal → click Next
4. Select purse + expense category
5. Additional info (PO number / comment)
6. Review & submit

## New wizard order (confirmed by walking the live UI 2026-07-24)

URL pattern: `https://app.classwallet.com/#/direct_pay/wizard/<n>-<slug>`

1. **`1-upload-invoice`** — vendor is already selected at this point (title shows vendor name +
   purse balance). Single dropzone, "Browse files" button. This is the exact page our automation
   gets stuck on today.
   - File input: `input[type='file']` (still the only one on the page — existing selector at
     `app/classwallet.py:565` still matches).
   - After a file is chosen, an image editor modal appears ("Resize and rotate your image...").
     The action button's **visible label changed from "Save" to "Scan Receipt"**, but the
     underlying attributes are unchanged: `data-test="Save"`, new `id="save-file"`. **Our existing
     selector `button[data-test='Save']` in `handle_image_editor_modal()`
     (app/classwallet.py:469) still works — no change needed there.**
   - Clicking "Scan Receipt" triggers the IDP scan (takes a few seconds) and auto-advances to step 2.

2. **`2-manage-expenses`** — new page, does not exist in the old flow. Contains:
   - **Details card**: thumbnail of the uploaded file, plus fields pre-filled by IDP where it could
     extract them:
     - `input[name="vendor"]` (aria-label "Vendor", required) — populated from scan.
     - `input[name="studentName"]` (aria-label **"Student Name"**, but the on-screen *label* says
       **"User Name"**, required) — **NOT populated by IDP in our test**; user must fill manually.
       This is the field the user wants ESA Helper to pre-fill/override (see Feature Request below).
     - Transaction date input (aria-label "Transaction date", no `name` attribute) — populated from scan.
     - `input[name="poNumber"]` (aria-label "Invoice") — populated from scan (invoice number).
   - **Direct Pay Details table** (this is the new line-item area):
     - One row per line item: `input[name="rows[0].description"]` (placeholder "Enter Item
       Description"), a **"Select Expense Category"** button (opens a modal, see below),
       `input[name="rows[0].quantity"]` (type number), `input[name="rows[0].price"]` (type text,
       currency), computed "Amount" (read-only), delete icon.
     - `+ Add Expense` button adds another `rows[N].*` row — so `upload_files`/category selection
       logic needs to become a loop over N rows instead of a single category pick.
     - Category picker modal: opened by clicking the row's "Select Expense Category" button.
       Contains a search box (`input[type=search]`, aria-label "Search Categories..."), a "Purse"
       filter (defaults "All Purses"), and a scrollable list of ~20 categories rendered as
       `input[type=radio][name="RadioGroup"]` with **no `data-test` and an opaque/base64-looking
       `value`** — so, like the old code, categories must be matched/clicked **by visible label
       text**, not by attribute. Modal has a `button[data-test='Save']` to confirm the pick (note:
       this is a *different* button instance than the image-editor one, same `data-test` value —
       scope queries to the open dialog).
   - **Totals**: `input[name="shipping"]`, `input[name="discount"]`, `input[name="tax"]`
     (all currency text inputs), computed Subtotal / Total Amount (read-only).
   - **Additional Documentation**: a second, separate dropzone (`Browse Files` link, "PDF, PNG or
     JPG - Max 10MB") for supporting docs — this is likely where receipt/attestation files should
     go now, separate from the primary invoice uploaded in step 1.
   - **Continue** button at the bottom advances to step 3.

3. **`3-select-wallet`** (heading on page reads "Select Purse") — replaces the purse-selection part
   of the old `select_expense_category()` (app/classwallet.py:604+), now decoupled from category
   selection (which moved into step 2's per-row modal).
   - Shows "Total Expenses" and "Total Direct Pay" summary, and one row per available purse (in our
     test, just "Arizona - ESA") with its balance and a `input[type=checkbox]` (no `name`/`id`/
     `data-test` — will need to locate via the row's label text, e.g. XPath
     `//div[contains(., 'Arizona - ESA')]//input[@type='checkbox']`).
   - **Continue** button is disabled (`Mui-disabled` class, no `data-test`) until a purse checkbox
     is checked.

4. **`4-review`** (heading "Review & Submit") — final confirmation page.
   - Read-only summary: vendor, transaction date, User Name, Invoice Number, uploaded file
     thumbnail, "Total Direct Pay" amount, "Purse Allocation" (with an `EDIT` button, no
     `data-test`, to jump back to step 3), and a **Direct Pay Details** section repeating each line
     item (description, expense category, unit price, qty) plus Subtotal/Shipping/Discount/Tax/Total.
   - `textarea[name="comments"]` (placeholder "Add a comment for the approver") — equivalent of the
     old comment field.
   - Attestation notice ("By submitting an expense, you are attesting that it is for your
     individual student's education, pursuant to A.R.S.§15-2402.") directly above the submit control.
   - Submit button: visible text "SUBMIT", but **no `data-test` or `id`** — will need to match by
     button text (`//button[normalize-space()='Submit']`), same pattern the old code already uses
     as a fallback elsewhere in `classwallet.py`.

## Feature Request (from user, 2026-07-24): known-value pre-fill / override — RESOLVED

Original ask: when ClassWallet's IDP scan can't extract a field (e.g. "Student Name" /
`studentName`), let the automation fill/overwrite it with a value ESA Helper already knows,
instead of the user having to type it in manually every time.

Resolved without a new `known_fields` UI/API concept — no new form field was needed. Per-field
rules (informed by the first live test, which surfaced a real overwrite bug) are hardcoded into
`fill_direct_pay_expenses()`:
- **Vendor, User Name (`studentName`)**: always overwritten with ESA Helper's `vendor_name`/
  `student` (already known - no new input required).
- **Line item amount**: always overwritten with ESA Helper's `amount`.
- **Invoice/quote number (`poNumber`)**: keep ClassWallet's scanned value if present; only fill
  with ESA Helper's `po_number` if IDP left it blank.
- **Transaction date**: keep ClassWallet's scanned date if it's today or earlier; otherwise
  (blank/unparseable/future) overwrite with today's date.

If a genuinely new *unknown-to-ESA-Helper* field needs a user-facing override later (not just
using data we already have), a `known_fields` dict on the submission payload is still the natural
extension point, but nothing currently needs it.

## What was implemented (2026-07-24)

`app/classwallet.py`:
- `start_direct_pay(vendor_name, search_term=None)` — dropped the `amount` param and the old
  amount-fill/Next-click block; now just clicks Pay, searches, selects the vendor, and waits to
  land on the "Upload Invoice" step. (Vendor search/selection logic itself is unchanged.)
- `upload_direct_pay_invoice(file_paths)` — new. Uploads the invoice file(s), handles the
  resize/rotate → "Scan Receipt" modal (reuses `handle_image_editor_modal()` unchanged, since its
  `data-test='Save'` selector still matches), then waits up to 30s for IDP scanning to finish and
  the URL to reach `manage-expenses`.
- `fill_direct_pay_expenses(vendor_name, amount, category, student_name=None, po_number=None,
  additional_files=None)` — new. Applies the per-field overwrite rules from the "Feature Request"
  section above (Vendor/User Name/amount always overwritten via `_force_set_field_value`; invoice
  number kept-if-present; transaction date kept-if-today-or-earlier via
  `_fill_transaction_date_if_needed`), selects the expense category via the new picker modal,
  uploads any additional docs (curriculum, etc.) into the step-2 dropzone, and clicks Continue.
  Only supports a single line item (`rows[0]`) — see "Not done yet" below.
- `_force_set_field_value(element, value)` — new private helper. Replaces the
  `.clear()` + `.send_keys()` pattern for any field we need to overwrite: `.clear()` sets the DOM
  value directly and doesn't reset ClassWallet's masked/React-controlled inputs' internal state,
  so a plain `.clear()` + `.send_keys()` **silently appends instead of overwriting** (this is
  exactly how a pre-filled $2,047.50 became $2,047,502,089.29 on the first live attempt). Instead,
  this clicks the field and does real select-all (Cmd/Ctrl+A) + Delete keystrokes, looped up to 5
  times until the field reads empty, before typing the new value.
- `_fill_transaction_date_if_needed()` — new private helper implementing the transaction-date rule
  above, via `input[aria-label='Transaction date']`, parsed as `%m/%d/%Y`.
- `_select_direct_pay_line_item_category(category)` — new private helper. Opens the category
  modal, types into the search box, and matches/clicks the radio option by walking up to 6 DOM
  ancestors from each `input[type=radio]` looking for text containing the normalized category
  name (exact match tried first, then substring) — done via `execute_script` since the radios have
  no `data-test` or usable `value`.
- `select_direct_pay_purse(purse_name="Arizona - ESA")` — new. Same ancestor-walk-by-text approach
  to find and check the purse's checkbox, then clicks Continue.
- `fill_direct_pay_review(comment=None)` — new. Fills the optional approver comment
  (`textarea[name='comments']`) on the Review & Submit page.
- `submit_direct_pay()` — updated to click the Submit button by visible text (no `data-test`/`id`
  exists on it) instead of the old `#next` id.
- `_normalize_category_name()` — extracted from `select_expense_category()` into a shared static
  method so both the (untouched) Reimbursement flow and the new Direct Pay category picker use the
  same ESA-Helper-name → ClassWallet-text mapping.
- `fill_direct_pay_additional_info()` and `proceed_direct_pay_to_review()` were deleted (fully
  superseded by `fill_direct_pay_expenses`'s po_number handling and the new
  `select_direct_pay_purse`/`fill_direct_pay_review` steps).
- **Reimbursement is untouched**: `upload_files()`, `select_expense_category()`,
  `start_reimbursement()`, `fill_po_and_comment()`, `submit_reimbursement()` were not modified
  (beyond the `_normalize_category_name` extraction, which preserves identical behavior).

`app/automation.py`: `SubmissionOrchestrator.submit_direct_pay()` rewritten to call the new
7-step sequence (select_student → start_direct_pay → upload_direct_pay_invoice →
fill_direct_pay_expenses → select_direct_pay_purse → fill_direct_pay_review → submit_direct_pay).
It also now splits `submission_data['files']` into the `invoice` entry (step 1) vs. everything
else (step 2 "Additional Documentation"), and passes `student` through as `student_name` to
`fill_direct_pay_expenses` — this resolves the "User Name" feature request using data ESA Helper
already had, without needing a new form field or a general `known_fields` mechanism.

`tests/test_direct_pay.py`: rewritten to mock/assert the new method names and call sequence.
Full suite: 119/119 passing.

## Not done yet / open questions

1. **Fully verified against the real site as of the 3rd attempt (2026-07-24).** Every step of the
   wizard - vendor selection, invoice upload/IDP scan, all Manage Expenses field rules (vendor,
   user name, invoice number, transaction date incl. the calendar popup, line item amount,
   category selection), purse selection, review, and final submit - has now run successfully
   against a real submission.
2. **Multi-line-item submissions are not supported.** If IDP splits an invoice into more than one
   row, or a vendor requires it, `fill_direct_pay_expenses` only ever touches `rows[0]`.
3. **PDF invoices**: we only observed the resize/rotate/"Scan Receipt" modal for a JPG upload. If a
   PDF doesn't trigger that modal, `handle_image_editor_modal()` should still return `True` after
   a ~3s no-modal timeout (existing behavior), and the subsequent 30s wait for `manage-expenses`
   should still apply — but this path wasn't observed live.
4. Whether an invoice upload is now *mandatory* to start any Direct Pay submission (old flow made
   files optional) — `upload_direct_pay_invoice` now fails fast with a clear error if no `invoice`
   file is provided, since step 1 of the new wizard has no visible skip option.
5. `CLAUDE.md`'s "Direct Pay Submission Workflow" section still describes the old
   vendor→amount→upload→category order and hasn't been updated to match the new wizard - worth
   doing next, but not urgent now that the code itself is confirmed working.

## Privacy note

All selectors/field names above were captured by walking the live UI with a real (but redacted)
test submission. No real names, vendor names, amounts, or account numbers are included in this
file, per the privacy rules in `CLAUDE.md`. The in-progress test submission in ClassWallet was
**not submitted/finalized** during this investigation.
