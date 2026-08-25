# Looker embedding — live, retargetable demos

One static site, one path per embedding mode. No build step, no package
manager, and no server anywhere.

| path | mode | what it needs |
|---|---|---|
| [`private/`](private/) | private embed | a Looker login you already have |
| [`signed/`](signed/) | signed embed | your instance's embed secret |

Live at **https://luutuankiet.github.io/looker-embed-demo/** (the root
redirects to `private/`, carrying any query string with it).

## private/ — borrowing a login

`embed.html` is the exhibit: a single file that renders a Looker dashboard from
one `<script>` tag on a CDN. Save it, open it locally, change two values, done.
`index.html` wraps it in a form and a code pane that `fetch`es `embed.html` at
runtime, so what you read is exactly what just ran.

It authenticates with your *own* Looker session cookie, issued by Looker to
Looker. The page never sees it, stores it or transmits it. The only two values
involved are a hostname and a dashboard ID, both already visible in the URL bar
of anyone using that instance — nothing to keep secret, nothing to sign.

**The Embedded Domain Allowlist is not consulted for this mode.** Verified
against a live instance: these pages render a private embed from an origin that
is not on that instance's list. That is a genuine surprise, and it is why the
allowlist advice lives on the signed page rather than this one.

## signed/ — manufacturing one

Signed embed mints a session instead of borrowing one, by HMAC-ing an ordered
list of fields with a shared secret. Anyone holding that secret can mint a URL
as any user with any permission, which is normally the end of the story for a
static site.

So the signing runs in **Python, in a Web Worker, in your own browser**:

- `sign.py` — the server half. Nothing in it knows it is in a browser. Paste it
  into Flask and read the secret from the environment instead of a form field;
  it behaves identically.
- `worker.js` — boots Pyodide, imports `sign.py`, answers messages.
- `index.html` — the form, the frame, and a log showing every step including
  the exact bytes that were HMAC'd.

Your secret is typed into a page you loaded from a CDN and handed to a worker on
that same page. It is not transmitted, because there is nothing to transmit it
to. Check that in the network tab — that is the standard everything here is held
to. Even so: use a secret you are willing to rotate.

Signed embed **is** checked against the Embedded Domain Allowlist, and browsers
check `Content-Security-Policy: frame-ancestors` against the entire ancestor
chain. Embedding one of these pages inside another page needs both origins
listed.
