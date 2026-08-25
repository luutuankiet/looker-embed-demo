# Looker private embed — a live, retargetable demo

Two files, no build step, no server, no secret.

- **`embed.html`** — the exhibit. A single HTML file that renders a Looker
  dashboard using one `<script>` tag from a CDN. Save it, open it locally,
  change two values: it works.
- **`index.html`** — a shell around it. A form that points the exhibit at *your*
  instance, and a code pane that `fetch`es `embed.html` at runtime so what you
  read is exactly what just ran.

Live at **https://luutuankiet.github.io/looker-embed-demo/**

## Why this mode needs nothing

Private embed authenticates with the reader's *own* Looker session cookie,
issued by Looker to Looker. This page never sees it, stores it or transmits it.
The only two values here are a hostname and a dashboard ID, both already visible
in the URL bar of anyone using that instance — so there is nothing to keep
secret and nothing to sign, which is why the whole thing fits in a static file.

Signed embedding is the opposite: it manufactures a login instead of borrowing
one, and manufacturing it requires an HMAC over the embed URL with a shared
secret. That secret cannot live in a page the reader can view-source. Private
embed is free because it borrows someone else's login; signed embed costs a
server because it makes one.

## If the frame comes up blank

Looker sends `Content-Security-Policy: frame-ancestors`, built from the
**Embedded Domain Allowlist** (Admin → Platform → Embed). Browsers check that
header against the *entire* ancestor chain, not just the immediate parent — so
embedding this page inside another page needs **both** origins allowlisted:

- `https://luutuankiet.github.io` — the page holding the Looker iframe
- the origin of whatever holds *this* page (a Confluence site, say)

You also need a live session on the instance in the box, and third-party cookies
have to reach Looker — use Chrome or Firefox.
