// ═══════════════════════════════════════════════════════════════════
// ops-knowledge-loop — Ember Grid
// Typst source — hybrid dark-cover / light-content PDF
// Build: typst compile presentation.typ ../presentation.typst.pdf
//
// EDIT THESE TWO VALUES BEFORE YOUR DEMO / INTERVIEW:
#let demo-days      = "[X days]"    // ← FILL IN
#let demo-role-name = "[Role Name]" // ← FILL IN
// ═══════════════════════════════════════════════════════════════════

#set page(
  width:  24cm,
  height: 13.5cm,
  margin: (top: 0pt, bottom: 0pt, left: 0pt, right: 0pt),
)
#set text(size: 10pt)
#set par(leading: 0.6em)

// ── DESIGN TOKENS ─────────────────────────────────────────────────
#let bg-dark   = rgb("#0A0F0A")
#let bg-dark2  = rgb("#0F1A0F")
#let bg-light  = rgb("#F4F6F2")
#let bg-light2 = rgb("#E8EDE8")
#let bg-panel  = rgb("#0D180D")
#let c-green   = rgb("#00FF41")
#let c-teal    = rgb("#19E6C5")
#let c-amber   = rgb("#FFC857")
#let c-text    = rgb("#1A2E1A")
#let c-dim     = rgb("#5A7A5A")
#let c-border  = rgb("#C8D8C8")
#let c-auto    = rgb("#00AA2B")
#let c-pend    = rgb("#CC9F40")
#let c-term    = rgb("#90EE90")

// ── HELPERS ───────────────────────────────────────────────────────
#let sp = (top: 1.3cm, bottom: 0.9cm, left: 1.4cm, right: 1.4cm)
#let mono-font = ("JetBrains Mono", "Consolas", "Courier New")
#let sans-font = ("Segoe UI", "Inter", "system-ui")

#let dark-slide(body) = rect(
  width: 100%, height: 100%, fill: bg-dark,
  stroke: none,
  inset: sp,
  body
)

#let light-slide(body) = rect(
  width: 100%, height: 100%, fill: bg-light,
  stroke: none,
  inset: sp,
  body
)

#let sh(txt) = {
  text(fill: c-green, size: 16pt, weight: "bold", font: mono-font, txt)
  v(-0.05cm)
  line(length: 100%, stroke: 0.5pt + c-border)
  v(0.2cm)
}

#let slide-label(txt) = text(
  fill: c-dim, size: 7pt, font: mono-font, upper(txt)
)

#let lcard(accent, body) = {
  block(
    fill: bg-light2,
    stroke: (left: 2pt + accent, rest: 0.4pt + c-border),
    radius: 4pt,
    inset: (x: 9pt, y: 6pt),
    width: 100%,
    body
  )
  v(0.2cm)
}

#let callout(body) = block(
  fill: rgb("#E8F5E8"),
  stroke: 0.5pt + c-green,
  radius: 4pt,
  inset: (x: 12pt, y: 7pt),
  width: 100%,
  text(fill: c-green, weight: "bold", size: 8.5pt, font: mono-font, body)
)

// Confidence bar using rect boxes
#let conf-bar(val, is-auto) = {
  let col = if is-auto { c-auto } else { c-pend }
  let w = 38pt * val
  box(width: 40pt, height: 6pt, clip: true,
    stack(dir: ltr,
      rect(width: w, height: 6pt, fill: col, radius: 2pt),
      rect(width: 40pt - w, height: 6pt, fill: bg-light2)
    )
  )
}

// ══════════════════════════════════════════════════════════════════
// SLIDE 1 — TITLE (dark)
// ══════════════════════════════════════════════════════════════════
#dark-slide[
  #v(0.5cm)
  #slide-label[ops-knowledge-loop]
  #v(0.35cm)
  #text(fill: c-green, size: 28pt, weight: "black", font: mono-font,
    tracking: -0.5pt)[ops-knowledge-loop]
  #v(0.25cm)
  #text(fill: c-teal, size: 12pt)[AI-Powered Incident Triage · Ember Grid]
  #v(0.2cm)
  #text(fill: rgb("#6B8F6B"), size: 9pt, font: mono-font
  )[#sym.triangle.r From alert to remediation in under 2 minutes]
  #v(0.6cm)
  #block(
    fill: bg-dark2,
    stroke: 0.4pt + rgb("#1E3A1E"),
    radius: 3pt,
    inset: (x: 10pt, y: 7pt),
    text(fill: rgb("#00CC33"), size: 8pt, font: mono-font
    )[INCIDENT #sym.arrow.r RAG #sym.arrow.r LLM #sym.arrow.r GATE #sym.arrow.r RUNDECK #sym.arrow.r TICKET CLOSED]
  )
  #place(bottom + right, dx: -1cm, dy: -0.6cm,
    text(fill: rgb("#1E3A1E"), size: 7pt, font: mono-font)[ember\@ops:~\$ #context counter(page).display("1") / #context counter(page).final().first()]
  )
]
#pagebreak()

// ══════════════════════════════════════════════════════════════════
// SLIDE 2 — PRIOR ART (light)
// ══════════════════════════════════════════════════════════════════
#let prior-col(frame-label, accent, chip, chip2, title, meta, items, tagline) = block(
  fill: bg-light,
  stroke: 1pt + accent,
  radius: 2pt,
  inset: 0pt,
  width: 100%,
  [
    #block(
      fill: bg-light2,
      stroke: (bottom: 0.4pt + c-border),
      inset: (x: 6pt, y: 4pt),
      width: 100%,
      text(fill: accent, size: 6pt, font: mono-font, weight: "bold")[#frame-label]
    )
    #block(inset: (x: 6pt, y: 5pt))[
      #text(fill: accent, weight: "bold", size: 6pt, font: mono-font)[#chip]
      #if chip2 != none [
        #v(0.05cm)
        #text(fill: accent, weight: "bold", size: 6pt, font: mono-font)[#chip2]
      ]
      #v(0.1cm)
      #text(fill: c-text, weight: "bold", size: 7pt, font: mono-font)[#title]
      #v(0.04cm)
      #text(fill: c-dim, size: 6pt)[#meta]
      #v(0.1cm)
      #for item in items [
        #text(fill: c-text, size: 6pt)[#sym.triangle.r #item]
        #v(0.05cm)
      ]
      #line(length: 100%, stroke: 0.3pt + c-border)
      #v(0.04cm)
      #block[
        #set par(leading: 0.35em, spacing: 0.35em)
        #text(fill: c-dim, size: 5.6pt, style: "italic")[#tagline]
      ]
    ]
  ]
)

#light-slide[
  #slide-label[Background]
  #v(0.15cm)
  #sh[Prior Art]
  #text(fill: c-dim, size: 8.5pt)[Three projects that map directly onto this one.]
  #v(0.2cm)
  #grid(
    columns: (1fr, 1fr, 1fr),
    gutter: 12pt,
    prior-col(
      [┌─ WOLF FRAMEWORK ─────────────────┐],
      c-green,
      [LangChain · ChromaDB · MCP · local LLM],
      none,
      [WOLF Framework],
      [Open-source AI-assisted game dev environment · 2025–present],
      (
        [LangChain + ChromaDB + LiteLLM RAG via MCP server],
        [Headless SimBot: evidence-gate-action loop],
        [Local (Ollama) and cloud/paid variants],
      ),
      [Same RAG stack and architectural pattern as this project.],
    ),
    prior-col(
      [┌─ QVC / QURATE RETAIL ────────────┐],
      c-teal,
      [~850 services · 5y zero audit breach],
      none,
      [Cloud Migration],
      [~850 Kubernetes microservices · 2020–2024],
      (
        [Migrated off Jenkins, Spinnaker, Rancher, Bitbucket, Ansible fully to Azure DevOps],
        [Live multi-DC AEM deployments; up to 40 stakeholders],
        [Zero audit breach over 5 years; ServiceNow tracked],
      ),
      [Same retail-scale infrastructure, ServiceNow, and gating discipline.],
    ),
    prior-col(
      [┌─ MULTI-GEO MOBILE PIPELINE ──────┐],
      c-amber,
      [Release: 3h → 30min],
      [PR acceptance: 2h → 20min],
      [Build-Test-Deploy],
      [Bitbucket · Jenkins · Artifactory · Jira · Consul],
      (
        [Multi-geo mobile build-test-deploy pipeline],
        [Release effort: 3 hours → 30 minutes],
        [Automated PR acceptance: 2 hours → 20 minutes],
        [Stage tracking, drift detection, rollback paths],
      ),
      [Same compression pattern applied to incident response.],
    ),
  )
  #v(0.15cm)
  #text(fill: c-dim, size: 7pt, font: mono-font)[
    #sym.triangle.r 8+ years automotive & UK retail · Ansible · ServiceNow · multi-geo release engineering · RAG / MCP / local-LLM
  ]
]
#pagebreak()

// ══════════════════════════════════════════════════════════════════
// SLIDE 3 — THE PROBLEM (light)
// ══════════════════════════════════════════════════════════════════
#light-slide[
  #slide-label[Context]
  #v(0.2cm)
  #sh[The On-Call Problem]

  #lcard(c-green)[
    #text(fill: c-green, weight: "bold", size: 8pt, font: mono-font)[MEAN TIME TO REMEDIATION]
    #linebreak()
    #text(fill: c-text, size: 9pt)[Mean time to remediation is dominated by ]
    #text(fill: c-text, style: "italic", size: 9pt)[lookup time]
    #text(fill: c-text, size: 9pt)[, not fix time]
  ]

  #lcard(c-teal)[
    #text(fill: c-teal, weight: "bold", size: 8pt, font: mono-font)[KNOWLEDGE SILO]
    #linebreak()
    #text(fill: c-text, size: 9pt)[Institutional knowledge lives in engineers' heads, not in systems]
  ]

  #lcard(c-amber)[
    #text(fill: c-amber, weight: "bold", size: 8pt, font: mono-font)[REPEAT WORK]
    #linebreak()
    #text(fill: c-text, size: 9pt)[Repeated incidents get manually triaged every single time]
  ]

  #v(0.15cm)
  #text(fill: c-dim, size: 8pt, font: mono-font)[
    #sym.triangle.r Ember Grid runs 17 microservices across UK retail infrastructure
  ]
]
#pagebreak()

// ══════════════════════════════════════════════════════════════════
// SLIDE 3 — SYSTEM ARCHITECTURE (light)
// ══════════════════════════════════════════════════════════════════
#light-slide[
  #slide-label[Architecture]
  #v(0.2cm)
  #sh[How It Works]

  #let stage(num, lbl, desc) = block(
    fill: bg-dark2,
    stroke: 0.5pt + c-green,
    radius: 4pt,
    inset: 7pt,
    width: 100%,
    [
      #text(fill: c-green, weight: "bold", size: 7pt, font: mono-font)[#num]\
      #text(fill: c-green, weight: "bold", size: 7.5pt, font: mono-font)[#lbl]\
      #text(fill: rgb("#6B8F6B"), size: 6.5pt)[#desc]
    ]
  )

  #grid(
    columns: (1fr, auto, 1fr, auto, 1fr, auto, 1fr, auto, 1fr),
    gutter: 4pt,
    align: center + horizon,
    stage([01], [INCIDENT], [ServiceNow ticket free-text description]),
    text(fill: c-green, size: 12pt)[#sym.arrow.r],
    stage([02], [RAG SEARCH], [sentence-transformers + ChromaDB top-3 matches]),
    text(fill: c-green, size: 12pt)[#sym.arrow.r],
    stage([03], [LLM REASONING], [Ollama qwen3:14b returns structured JSON]),
    text(fill: c-green, size: 12pt)[#sym.arrow.r],
    stage([04], [DECISION GATE], [>= 0.70 auto-fire · below 0.70 human review]),
    text(fill: c-green, size: 12pt)[#sym.arrow.r],
    stage([05], [OUTCOME], [Rundeck fires or engineer briefed]),
  )

  #v(0.3cm)
  #callout[#sym.triangle.r Fully local · No data leaves the machine · No API costs · ~30s end-to-end]
]
#pagebreak()

// ══════════════════════════════════════════════════════════════════
// SLIDE 4 — KNOWLEDGE BASE (light, two columns)
// ══════════════════════════════════════════════════════════════════
#light-slide[
  #slide-label[Data]
  #v(0.2cm)
  #sh[What the RAG Searches]

  #grid(columns: (1fr, 1fr), gutter: 1cm, [
    #text(fill: c-teal, weight: "bold", size: 8pt, font: mono-font)[#sym.triangle.r INCIDENT HISTORY]
    #v(0.2cm)
    #lcard(c-green)[#text(fill: c-text, size: 8.5pt)[500+ synthetic incidents across 17 services]]
    #lcard(c-green)[#text(fill: c-text, size: 8.5pt)[Each indexed as a vector embedding in ChromaDB]]
    #lcard(c-green)[
      #text(fill: c-dim, size: 7.5pt, font: mono-font
      )[OOM kills · latency spikes · ETL failures · EDI mismatches · POS outages · loyalty bugs · notification duplicates]
    ]
  ], [
    #text(fill: c-teal, weight: "bold", size: 8pt, font: mono-font)[#sym.triangle.r RUNBOOKS]
    #v(0.2cm)
    #lcard(c-teal)[
      #text(fill: c-text, size: 8.5pt)[Per-service markdown runbooks]\
      #text(fill: c-dim, size: 7pt, font: mono-font)[checkout · product-search · payment-processor · …]
    ]
    #lcard(c-teal)[#text(fill: c-text, size: 8.5pt)[Auto-generated runbooks from resolved ServiceNow tickets]]
    #lcard(c-teal)[#text(fill: c-text, size: 8.5pt)[Chunked and embedded alongside incident history]]
  ])
  #v(0.05cm)
  #line(length: 100%, stroke: 0.4pt + c-border)
  #v(0.1cm)
  #text(fill: c-dim, size: 7.5pt, font: mono-font)[All embeddings: ]
  #text(fill: c-teal, size: 7.5pt, weight: "bold", font: mono-font)[all-MiniLM-L6-v2]
  #text(fill: c-dim, size: 7.5pt, font: mono-font)[ · Similarity threshold: ]
  #text(fill: c-green, size: 7.5pt, weight: "bold", font: mono-font)[0.60 strong match]
]
#pagebreak()

// ══════════════════════════════════════════════════════════════════
// SLIDE 5 — DASHBOARD (light)
// ══════════════════════════════════════════════════════════════════
#light-slide[
  #slide-label[Tooling]
  #v(0.2cm)
  #sh[Ops Dashboard]

  #grid(columns: (1fr, 1fr), gutter: 1cm, [
    #for (icon, feat) in (
      ("📋", "Recent incidents and their triage status"),
      ("🎯", "RAG match scores per incident"),
      ("🤖", "AI recommendation with confidence score"),
      ("⚡", "Decision gate outcome (auto-executed vs pending review)"),
      ("🔧", "Rundeck job catalogue"),
    ) {
      grid(
        columns: (14pt, 1fr), gutter: 4pt, align: top,
        text(size: 9pt)[#icon],
        text(fill: c-text, size: 8.5pt)[#feat]
      )
      line(length: 100%, stroke: 0.3pt + c-border)
      v(0.1cm)
    }
    #v(0.1cm)
    #block(
      fill: bg-dark2, stroke: 0.5pt + c-teal, radius: 3pt,
      inset: (x: 8pt, y: 4pt),
      text(fill: c-teal, size: 7.5pt, weight: "bold", font: mono-font)[Flask · localhost:5000]
    )
  ], [
    #block(
      fill: bg-panel, stroke: 0.5pt + c-teal, radius: 4pt,
      inset: (x: 10pt, y: 8pt), width: 100%,
      text(fill: c-term, size: 7pt, font: mono-font)[
#text(fill: c-teal)[ops-knowledge-loop dashboard]

+------+--------------+--------+
| INC  | STATUS       | CONF   |
+------+--------------+--------+
| 0043 | AUTO-EXECUTE | 0.95 v |
| 0044 | PENDING      | 0.35 ~ |
| 0045 | AUTO-EXECUTE | 0.75 v |
| 0046 | AUTO-EXECUTE | 0.75 v |
| 0047 | PENDING      | 0.66 ~ |
+------+--------------+--------+
      ]
    )
  ])
]
#pagebreak()

// ══════════════════════════════════════════════════════════════════
// SLIDE 6 — LIVE DEMO RESULTS (light, hero)
// ══════════════════════════════════════════════════════════════════
#light-slide[
  #slide-label[Results]
  #v(0.2cm)
  #sh[10 Queries · Live Run]

  #grid(columns: (auto, auto, 1fr), gutter: 8pt, align: center + horizon,
    block(fill: rgb("#E8F5E8"), stroke: 0.5pt + c-green, radius: 3pt, inset: (x:10pt,y:5pt),
      stack(
        text(fill: c-auto, size: 14pt, weight: "black")[5],
        v(2pt),
        text(fill: c-auto, size: 7pt, weight: "bold", font: mono-font)[AUTO-EXECUTED]
      )
    ),
    block(fill: rgb("#FFF8E6"), stroke: 0.5pt + c-amber, radius: 3pt, inset: (x:10pt,y:5pt),
      stack(
        text(fill: c-pend, size: 14pt, weight: "black")[5],
        v(2pt),
        text(fill: c-pend, size: 7pt, weight: "bold", font: mono-font)[PENDING REVIEW]
      )
    ),
    align(right, text(fill: c-dim, size: 7pt, font: mono-font)[gate threshold: 0.70])
  )
  #v(0.2cm)

  #let rrow(inc, job, conf, is-auto) = {
    let bg    = if is-auto { rgb("#F0FAF0") } else { rgb("#FFFAED") }
    let lcol  = if is-auto { c-green } else { c-amber }
    let ocol  = if is-auto { c-auto } else { c-pend }
    let label = if is-auto { "AUTO-EXECUTE" } else { "PENDING REVIEW" }
    let obg   = if is-auto { rgb("#E8F5E8") } else { rgb("#FFF8E6") }
    (
      block(fill: bg, stroke: (left: 2pt + lcol, rest: 0.3pt + c-border),
        inset:(x:5pt,y:3pt), width:100%,
        text(fill:c-text, size:7pt)[#inc]),
      block(fill: bg, stroke: 0.3pt + c-border, inset:(x:5pt,y:3pt), width:100%,
        text(fill:c-dim, size:6.5pt, font:mono-font)[#job]),
      block(fill: bg, stroke: 0.3pt + c-border, inset:(x:5pt,y:3pt),
        grid(columns:(40pt, 4pt, auto), gutter:4pt, align: center+horizon,
          conf-bar(conf, is-auto),
          [],
          text(fill:ocol, size:7pt, weight:"bold", font:mono-font)[#str(conf)]
        )
      ),
      block(fill: bg, stroke: 0.3pt + c-border, inset:(x:5pt,y:3pt),
        block(fill:obg, stroke:0.4pt+ocol, radius:10pt, inset:(x:5pt,y:2pt),
          text(fill:ocol, size:6pt, weight:"bold", font:mono-font)[#label]
        )
      ),
    )
  }

  #table(
    columns: (1.7fr, 2.1fr, 1fr, 1.2fr),
    gutter: 2pt, fill: none, stroke: none, inset: 0pt,
    block(fill:bg-dark, inset:(x:5pt,y:4pt), width:100%, text(fill:c-green,size:7pt,weight:"bold",font:mono-font)[INCIDENT]),
    block(fill:bg-dark, inset:(x:5pt,y:4pt), width:100%, text(fill:c-green,size:7pt,weight:"bold",font:mono-font)[RECOMMENDED JOB]),
    block(fill:bg-dark, inset:(x:5pt,y:4pt), text(fill:c-green,size:7pt,weight:"bold",font:mono-font)[CONFIDENCE]),
    block(fill:bg-dark, inset:(x:5pt,y:4pt), width:100%, text(fill:c-green,size:7pt,weight:"bold",font:mono-font)[OUTCOME]),
    ..rrow("checkout-service OOM kill",              "restart-service-with-memory-bump", 0.95, true),
    ..rrow("payment-processor 500 errors",           "rollback-to-previous-version",     0.95, true),
    ..rrow("product-search unresponsive after deploy","reindex-elasticsearch",            0.75, true),
    ..rrow("inventory sync stalled",                 "force-inventory-sync",             0.66, false),
    ..rrow("store POS tills unresponsive",           "rollback-to-previous-version",     0.75, true),
    ..rrow("loyalty service not awarding points",    "restart-service-rolling",          0.35, false),
    ..rrow("order fulfilment latency spike",         "scale-up-replicas",                0.75, true),
    ..rrow("notification service dup emails",        "restart-service-with-memory-bump", 0.35, false),
    ..rrow("supplier EDI orders dropped",            "force-inventory-sync",             0.65, false),
    ..rrow("recommendation engine degraded",         "reindex-elasticsearch",            0.45, false),
  )
  #v(0.15cm)
  #text(fill: c-dim, size: 6.5pt, font: mono-font)["The gate is discriminating by design — weak RAG similarity or ambiguous root cause correctly suppresses auto-execution"]
]
#pagebreak()

// ══════════════════════════════════════════════════════════════════
// FEATURED TERMINAL SLIDES Q1, Q3, Q6
// ══════════════════════════════════════════════════════════════════

#let q-slide(qnum, title, confidence, outcome-col, body) = dark-slide[
  #slide-label[Live Output — Query #qnum / 10]
  #v(0.15cm)
  #text(fill: c-green, size: 10.5pt, weight: "bold", font: mono-font)[#title]
  #h(8pt)
  #text(fill: outcome-col, size: 8.5pt, font: mono-font)[confidence #confidence]
  #v(0.2cm)
  #block(fill: bg-panel, stroke: 0.4pt + c-green, radius: 4pt,
    inset: (x: 9pt, y: 7pt), width: 100%,
    text(fill: c-term, size: 6.2pt, font: mono-font, body)
  )
]

#q-slide("1", "checkout-service OOM kill", "0.95 -> AUTO-EXECUTE", c-teal)[
\$ python query_live.py "checkout service OOM kill, container hitting memory limit and restarting repeatedly under load"

  RAG Top 3:
  1  incidents.json   0.797 ✓ strong match   [INC0043096] checkout-service OOM kill
  2  incidents.json   0.796 ✓ strong match   [INC0043144] checkout-service OOM kill
  3  incidents.json   0.795 ✓ strong match   [INC0043048] checkout-service OOM kill

  ✓ Strong precedent found — incidents.json (similarity 0.797)

  Recommended Job  : restart-service-with-memory-bump   |  Confidence : 0.95
  Decision Gate    : AUTO-EXECUTE
  Reasoning        : OOM kills due to memory limits directly align with the job purpose.
                     Runbook context explicitly confirms memory threshold breach as trigger.

  ✓ WOULD AUTO-EXECUTE — restart-service-with-memory-bump (confidence 0.95 ≥ 0.70 gate)
  Total runtime: 8.7s
]
#pagebreak()

#q-slide("3", "product-search unresponsive after deploy", "0.75 -> AUTO-EXECUTE", c-teal)[
\$ python query_live.py "product search returning empty results, search index unresponsive after deployment"

  RAG Top 3:
  1  product-search.md   0.575 ~ partial match   Service Overview: ES-backed search service
  2  incidents.json      0.571 ~ partial match   [INC0043346] product-search slow query (1352ms)
  3  product-search.md   0.570 ~ partial match   Diagnostic Steps: kubectl exec cache hit rate

  ⚠ No close precedent — best match 0.575 in product-search.md. AI will deduce a remediation.

  Recommended Job  : reindex-elasticsearch   |  Confidence : 0.75
  Decision Gate    : ABOVE GATE -> AUTO-EXECUTE
  Reasoning        : Unresponsive ES index directly maps to reindexing as remediation step.
                     Runbook + incident context both confirm the service architecture.

  ✓ WOULD AUTO-EXECUTE — reindex-elasticsearch (confidence 0.75 ≥ 0.70 gate)
  Total runtime: 9.9s
]
#pagebreak()

#q-slide("6", "loyalty service not awarding points", "0.35 -> PENDING REVIEW", c-pend)[
\$ python query_live.py "loyalty service not awarding points after purchase, customer accounts not updating"

  RAG Top 3:
  1  incidents.json   0.642 ~ partial   [INC0042145] loyalty-service failing to award pts (click-and-collect)
  2  incidents.json   0.562 ~ partial   [INC0041652] reward redemption API 500 (DB connection pool exhausted)
  3  incidents.json   0.561 ~ partial   [INC0041134] points returning negatives (bulk redemption event)

  ⚠ No close precedent — best match 0.642. AI will deduce a remediation.

  Recommended Job  : restart-service-rolling   |  Confidence : #text(fill: c-amber)[0.35  \<-- MODEL SELF-DOWNGRADED]
  Decision Gate    : RULE-BASED FALLBACK
  Reasoning        : Past loyalty-service issues resolved via restarts or config updates.
                     Runbook context references backfill scripts — not a restart path.
                     Semantic mismatch between query and available context. Self-downgraded.

  ⏸  PENDING HUMAN REVIEW — restart-service-rolling (confidence 0.35 < 0.70 gate)
  Total runtime: 14.6s
]
#pagebreak()

// ══════════════════════════════════════════════════════════════════
// SLIDE 7 — WHY PENDING REVIEW IS A FEATURE (light)
// ══════════════════════════════════════════════════════════════════
#light-slide[
  #slide-label[Design Philosophy]
  #v(0.2cm)
  #sh[The Gate is the Point]

  #grid(columns: (1fr, 1fr, 1fr), gutter: 0.5cm,
    block(fill: bg-light2, stroke: (top: 1.5pt + c-amber, rest: 0.5pt + c-border),
      radius: 4pt, inset: 8pt, width: 100%)[
      #text(fill: c-amber, weight: "bold", size: 8pt, font: mono-font)[loyalty-service · 0.35]
      #v(0.15cm)
      #text(fill: c-text, size: 8pt)[RAG matched but runbook referenced a backfill script, not a restart. ]
      #text(fill: c-amber, weight: "bold", size: 8pt)[Model self-downgraded.]
    ],
    block(fill: bg-light2, stroke: (top: 1.5pt + c-amber, rest: 0.5pt + c-border),
      radius: 4pt, inset: 8pt, width: 100%)[
      #text(fill: c-amber, weight: "bold", size: 8pt, font: mono-font)[notification-service · 0.35]
      #v(0.15cm)
      #text(fill: c-text, size: 8pt)[Matched incident was push notifications, not email. ]
      #text(fill: c-amber, weight: "bold", size: 8pt)[Semantic mismatch caught.]
    ],
    block(fill: bg-light2, stroke: (top: 1.5pt + c-amber, rest: 0.5pt + c-border),
      radius: 4pt, inset: 8pt, width: 100%)[
      #text(fill: c-amber, weight: "bold", size: 8pt, font: mono-font)[supplier-EDI · 0.65]
      #v(0.15cm)
      #text(fill: c-text, size: 8pt)[Schema validation failure; force-inventory-sync plausible but not certain. ]
      #text(fill: c-amber, weight: "bold", size: 8pt)[Correctly held for review.]
    ]
  )

  #v(0.3cm)
  #block(fill: bg-panel, stroke: 0.5pt + c-green, radius: 4pt,
    inset: (x: 10pt, y: 8pt), width: 100%,
    text(fill: c-term, size: 6.5pt, font: mono-font)[
\$ python query_live.py "loyalty service not awarding points after purchase, customer accounts not updating"

  RAG Top 3:
  1  incidents.json   0.642 ~ partial  [INC0042145] loyalty-service failing to award pts (click-and-collect)
  2  incidents.json   0.562 ~ partial  [INC0041652] reward redemption API 500 (DB connection pool exhausted)
  3  incidents.json   0.561 ~ partial  [INC0041134] points returning negatives (bulk redemption event)

  ⚠ No close precedent — best match 0.642. AI will deduce a remediation.

  Recommended Job  : restart-service-rolling
  Confidence       : #text(fill: c-amber)[0.35  \<-- MODEL SELF-DOWNGRADED]
  Decision Gate    : #text(fill: c-amber)[RULE-BASED FALLBACK]
  Reasoning        : Runbook context references a backfill script — not a restart path.
                     Semantic mismatch between query and available context.

  ⏸  PENDING HUMAN REVIEW — restart-service-rolling (conf 0.35 \< 0.70 gate)  |  Runtime: 14.6s
    ]
  )

  #v(0.25cm)
  #line(length: 100%, stroke: 0.4pt + c-border)
  #v(0.15cm)
  #text(fill: c-teal, size: 8.5pt, style: "italic")["A system that knows what it doesn't know is more useful than one that always fires"]
]
#pagebreak()

// ══════════════════════════════════════════════════════════════════
// SLIDE OBS — OBSERVABILITY (light)
// ══════════════════════════════════════════════════════════════════
#light-slide[
  #slide-label[Production Readiness]
  #v(0.2cm)
  #sh[Observability]

  #grid(columns: (1fr, 1fr, 1fr), gutter: 0.5cm,
    block(fill: bg-light2, stroke: (top: 1.5pt + c-teal, rest: 0.5pt + c-border),
      radius: 4pt, inset: 8pt, width: 100%)[
      #text(fill: c-teal, weight: "bold", size: 8pt, font: mono-font)[Log Every Step]
      #v(0.15cm)
      #text(fill: c-text, size: 8pt)[RAG top-K + similarity scores, LLM token counts + latency, every gate confidence and outcome, every Rundeck execution result.]
    ],
    block(fill: bg-light2, stroke: (top: 1.5pt + c-teal, rest: 0.5pt + c-border),
      radius: 4pt, inset: 8pt, width: 100%)[
      #text(fill: c-teal, weight: "bold", size: 8pt, font: mono-font)[Dashboards]
      #v(0.15cm)
      #text(fill: c-text, size: 8pt)[Confidence distribution over time, auto-execution rate, false positive rate, and P99 latency per pipeline stage.]
    ],
    block(fill: bg-light2, stroke: (top: 1.5pt + c-teal, rest: 0.5pt + c-border),
      radius: 4pt, inset: 8pt, width: 100%)[
      #text(fill: c-teal, weight: "bold", size: 8pt, font: mono-font)[Alerts]
      #v(0.15cm)
      #text(fill: c-text, size: 8pt)[Confidence distribution shift, fallback rate increase, and any Rundeck failure without a subsequent human resolution.]
    ]
  )
  #v(0.25cm)
  #line(length: 100%, stroke: 0.4pt + c-border)
  #v(0.15cm)
  #text(fill: c-dim, size: 7.5pt, font: mono-font)[Sudden confidence drops are a production smell: stale knowledge base, model version drift, or a retrieval-quality regression.]
]
#pagebreak()

// ══════════════════════════════════════════════════════════════════
// SLIDE 8 — TECH STACK (light)
// ══════════════════════════════════════════════════════════════════
#light-slide[
  #slide-label[Technology]
  #v(0.2cm)
  #sh[Stack]

  #let tech(name, desc) = block(
    fill: bg-light2, stroke: 0.5pt + c-border, radius: 4pt,
    inset: (x: 9pt, y: 6pt),
    stack(
      text(fill: c-teal, weight: "bold", size: 8.5pt, font: mono-font)[#name],
      v(3pt),
      text(fill: c-dim, size: 7.5pt)[#desc]
    )
  )

  #grid(
    columns: (1fr, 1fr, 1fr, 1fr),
    gutter: 0.5cm,
    tech("Python 3.11", "Core pipeline"),
    tech("ChromaDB", "Vector store"),
    tech("sentence-transformers", "all-MiniLM-L6-v2 embeddings"),
    tech("Ollama + qwen3:14b", "Local LLM · 9.3 GB · Q4_K_M · RTX 4090"),
    tech("Flask", "Ops dashboard"),
    tech("Rich", "CLI output formatting"),
    tech("ServiceNow API", "Mocked ticket source"),
    tech("Rundeck", "Mocked job execution"),
  )
  #v(0.3cm)
  #callout[#sym.triangle.r Runs entirely on local hardware · Zero external API calls · Zero ongoing cost]
]
#pagebreak()

// ══════════════════════════════════════════════════════════════════
// SLIDE FUTURE — WHERE THIS GOES NEXT (light)
// ══════════════════════════════════════════════════════════════════
#light-slide[
  #slide-label[Roadmap]
  #v(0.2cm)
  #sh[Where This Goes Next]

  #grid(columns: (1fr, 1fr, 1fr), gutter: 0.5cm,
    block(fill: bg-light2, stroke: (top: 1.5pt + c-teal, rest: 0.5pt + c-border),
      radius: 4pt, inset: 8pt, width: 100%)[
      #text(fill: c-teal, weight: "bold", size: 8pt, font: mono-font)[Shadow Deployment Pipeline]
      #v(0.15cm)
      #text(fill: c-text, size: 7.5pt)[A shadow environment mirrors live incidents without acting. Once recommendations earn sufficient confidence, a single approval promotes to production - zero-downtime, ]
      #text(fill: c-auto, weight: "bold", size: 7.5pt)[the system validates itself before it acts.]
    ],
    block(fill: bg-light2, stroke: (top: 1.5pt + c-teal, rest: 0.5pt + c-border),
      radius: 4pt, inset: 8pt, width: 100%)[
      #text(fill: c-teal, weight: "bold", size: 8pt, font: mono-font)[Repository-Aware Context]
      #v(0.15cm)
      #text(fill: c-text, size: 7.5pt)[Continuous indexing of service repos gives the LLM ]
      #text(fill: c-auto, weight: "bold", size: 7.5pt)[code-level context - config files, dependency changes, recent commits -]
      #text(fill: c-text, size: 7.5pt)[ when a root cause needs investigation beyond tickets and runbooks.]
    ],
    block(fill: bg-light2, stroke: (top: 1.5pt + c-teal, rest: 0.5pt + c-border),
      radius: 4pt, inset: 8pt, width: 100%)[
      #text(fill: c-teal, weight: "bold", size: 8pt, font: mono-font)[Living Organisational Memory]
      #v(0.15cm)
      #text(fill: c-text, size: 7.5pt)[Automatic ingestion of JIRA, Confluence, and equivalent knowledge bases keeps RAG context current with ]
      #text(fill: c-auto, weight: "bold", size: 7.5pt)[the team's accumulated decisions and post-mortems.]
      #text(fill: c-text, size: 7.5pt)[ The system learns from every resolved incident.]
    ]
  )
]
#pagebreak()


#q-slide("2", "payment-processor 500 errors", "0.95 -> AUTO-EXECUTE", c-teal)[
\$ python query_live.py "payment processor returning 500 errors, transactions not completing..."

  RAG Top 3:
  1  incidents.json   0.495 ✗ weak match   [INC0043135] payment-processor 5xx spike (70%)
  2  incidents.json   0.492 ✗ weak match   [INC0043231] payment-processor 5xx spike (72%)
  3  incidents.json   0.488 ✗ weak match   [INC0043183] payment-processor 5xx spike (71%)

  ⚠ No close precedent — best match 0.495. AI will deduce a remediation.
  [weak RAG; model returns 0.95 via pattern recognition across three prior resolved incidents]

  Recommended Job  : rollback-to-previous-version   |  Confidence : 0.95
  Decision Gate    : AUTO-EXECUTE
  Reasoning        : Three prior 5xx spikes resolved by rollback; standard mitigation confirmed.

  ✓ WOULD AUTO-EXECUTE — rollback-to-previous-version (conf 0.95 ≥ 0.70 gate)
  Total runtime: 8.2s
]
#pagebreak()

#q-slide("4", "inventory sync stalled", "0.66 -> PENDING REVIEW", c-pend)[
\$ python query_live.py "inventory sync stalled, stock levels on website not updating after warehouse batch job"

  RAG Top 3:
  1  incidents.json   0.675 ~ partial match   [INC0041047] inventory-sync batch job failed silently
  2  incidents.json   0.656 ~ partial match   [INC0043477] inventory-sync data pipeline stall (75 min)
  3  incidents.json   0.639 ~ partial match   [INC0042043] inventory-sync failing for 14 stores

  ✓ Strong precedent found — incidents.json (similarity 0.675)

  Recommended Job  : force-inventory-sync   |  Confidence : #text(fill: c-amber)[0.66  \<-- just below gate]
  Decision Gate    : PENDING REVIEW
  Reasoning        : Stalled sync mirrors INC0043477 pipeline-stall exactly; confidence 0.04 below gate.

  ⏸  PENDING HUMAN REVIEW — force-inventory-sync (conf 0.66 \< 0.70 gate)
  Total runtime: 15.4s
]
#pagebreak()

#q-slide("5", "store POS tills unresponsive", "0.75 -> AUTO-EXECUTE", c-teal)[
\$ python query_live.py "store POS system tills unresponsive, cashiers cannot process customer transactions"

  RAG Top 3:
  1  incidents.json   0.573 ~ partial match   [INC0043165] store-pos-system pipeline stall (75 min)
  2  incidents.json   0.569 ~ partial match   [INC0043333] store-pos-system pipeline stall (75 min)
  3  incidents.json   0.547 ✗ weak match      [INC0041062] store-pos-system API latency (Consul mesh)

  ⚠ No close precedent — best match 0.573. AI will deduce a remediation.
  [model correctly extrapolated from P1 Consul mesh outage (2,300 stores) resolved by config rollback]

  Recommended Job  : rollback-to-previous-version   |  Confidence : 0.75
  Decision Gate    : ABOVE GATE -> AUTO-EXECUTE
  Reasoning        : P1 config rollback pattern matches despite low RAG similarity.

  ✓ WOULD AUTO-EXECUTE — rollback-to-previous-version (conf 0.75 ≥ 0.70 gate)
  Total runtime: 9.9s
]
#pagebreak()

#q-slide("7", "order fulfilment latency spike", "0.75 -> AUTO-EXECUTE", c-teal)[
\$ python query_live.py "order fulfilment delays caused by upstream pricing engine latency spike during peak hours"

  RAG Top 3:
  1  incidents.json   0.571 ~ partial match   [INC0043496] order-fulfilment P99 breach (1102ms)
  2  incidents.json   0.565 ~ partial match   [INC0043448] order-fulfilment P99 breach (4926ms)
  3  incidents.json   0.558 ~ partial match   [INC0043304] order-fulfilment P99 breach (798ms)

  ⚠ No close precedent — best match 0.571. AI will deduce a remediation.

  Recommended Job  : scale-up-replicas   |  Confidence : 0.75
  Decision Gate    : ABOVE GATE -> AUTO-EXECUTE
  Reasoning        : Upstream latency creates downstream throughput pressure;
                     scaling replicas reduces per-instance load while root cause is addressed.

  ✓ WOULD AUTO-EXECUTE — scale-up-replicas (conf 0.75 ≥ 0.70 gate)
  Total runtime: 12.2s
]
#pagebreak()

#q-slide("8", "notification service duplicate emails", "0.35 -> PENDING REVIEW", c-pend)[
\$ python query_live.py "notification service sending duplicate confirmation emails after every order event"

  RAG Top 3:
  1  incidents.json             0.687 ~ partial   [INC0041294] notif-svc duplicate PUSH notifications
  2  incidents.json             0.520 ✗ weak       [INC0041158] notif-svc email queue backed up (6h delay)
  3  INC0042468-notif-svc.md   0.467 ✗ weak       Auto-generated runbook: broken unsubscribe links (P2)

  ✓ Strong precedent found — incidents.json (0.687)
  [but matched push notifications, not email — semantic mismatch]

  Recommended Job  : restart-service-with-memory-bump   |  Confidence : #text(fill: c-amber)[0.35  \<-- SELF-DOWNGRADED]
  Decision Gate    : RULE-BASED FALLBACK
  Reasoning        : Runbook context (INC0042468) used restart-with-memory-bump for config issue.
                     Current incident involves email duplicates, not push notifications.
                     Semantic mismatch between incident type and available context.

  ⏸  PENDING HUMAN REVIEW — restart-service-with-memory-bump (conf 0.35 \< 0.70 gate)
  Total runtime: 22.5s
]
#pagebreak()

#q-slide("9", "supplier EDI orders dropped", "0.65 -> PENDING REVIEW", c-pend)[
\$ python query_live.py "supplier integration service dropping EDI purchase orders during XML schema validation"

  RAG Top 3:
  1  incidents.json   0.705 ~ partial   [INC0041737] supplier-integration EDI batch failure
                                         (Supplier-31 schema version mismatch)
  2  incidents.json   0.561 ~ partial   [INC0043383] supplier-integration ETL failure (11 retries)
  3  incidents.json   0.542 ✗ weak      [INC0041195] supplier-integration EDI timeout (3,200 SKUs)

  ✓ Strong precedent found — incidents.json (similarity 0.705)

  Recommended Job  : force-inventory-sync   |  Confidence : #text(fill: c-amber)[0.65  \<-- plausible but not certain]
  Decision Gate    : PENDING REVIEW
  Reasoning        : EDI orders dropped during XML schema validation matches INC0041737 closely.
                     force-inventory-sync addresses data pipeline stalls, not schema mismatches.
                     Plausible mitigation, but not the correct root-cause fix. Correctly held.

  ⏸  PENDING HUMAN REVIEW — force-inventory-sync (conf 0.65 \< 0.70 gate)
  Total runtime: 25.7s
]
#pagebreak()

#q-slide("10", "recommendation engine degraded", "0.45 -> PENDING REVIEW", c-pend)[
\$ python query_live.py "recommendation engine returning identical product suggestions for all users after model retraining"

  RAG Top 3:
  1  incidents.json   0.393 ✗ weak   [INC0041839] product-search autocomplete empty (Redis cache flush)
  2  incidents.json   0.356 ✗ weak   [INC0043065] product-search feature flag misconfiguration (50%)
  3  incidents.json   0.315 ✗ weak   [INC0043017] product-search feature flag misconfiguration (49%)

  ⚠ No close precedent — best match 0.393. All matches from a different service.
  Zero relevant knowledge base entries for the recommendation engine.

  Recommended Job  : reindex-elasticsearch   |  Confidence : #text(fill: c-amber)[0.45  \<-- ACKNOWLEDGING LIMITS]
  Decision Gate    : RULE-BASED FALLBACK
  Reasoning        : Identical suggestions indicate stale/improperly updated index data.
                     No recommendation-engine incidents in knowledge base. Cross-service inference
                     only. Model self-downgraded — this is the system acknowledging its limits.

  ⏸  PENDING HUMAN REVIEW — reindex-elasticsearch (conf 0.45 \< 0.70 gate)
  Total runtime: 13.8s
]
