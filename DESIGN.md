# ProcureGuard — design notes

The visual language is **the official record**: a government file that moves through
an office. Paper, ink, and rubber stamps — not a SaaS dashboard. Procurement officers
work in exactly this world of dockets, annexures, and signed orders, so the design
speaks their vernacular instead of a generic admin-panel look.

## Why each choice

- **Paper base `#EDEAE2`, ink `#232A35`.** A manila-grey paper, deliberately greyer
  than the warm cream AI pages cluster around. Iron-gall blue-black ink rather than
  near-black.
- **File-tab red `#A3352C`.** The sealing-wax / case-file tab red of Indian government
  records. One accent, spent on the brand tab, destructive action, and failures.
- **IBM Plex family.** Condensed for headings and stamps (bureaucratic signage),
  Sans for body, Mono only for true identifiers — GSTINs, reference numbers, rule
  versions. Mono is never used as a label style.
- **Stamps for the four-state model.** The PRD's central rule — *unverifiable is not
  verified* — is encoded structurally: verified is stamped in green ink, review in
  amber, non-compliant in red, and unverifiable in washed grey that can never be
  mistaken for a good outcome.
- **Gazette double rules** open each record section; a ledger-ruled score figure
  replaces the score card. Structure encodes meaning; nothing is decorated.
- **One orchestrated moment.** The risk and recommendation stamps land on the
  dashboard on load (with `prefers-reduced-motion` respected). Everything else is
  still.

## Copy voice

Officer-to-officer: "Open a new file", "Add a bidder", "A reason is required to
record a final decision". Errors state what happened and what to do; empty states
invite the next action. The interface never apologizes and never editorializes —
the human decides, the record keeps the receipts.
