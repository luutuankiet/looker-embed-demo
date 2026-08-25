// The "server". It is a Web Worker: a second thread, with no DOM, that the page
// talks to by message passing. Python runs inside it via Pyodide, so the ~5 MB
// runtime download never freezes the page you are reading.
//
// The secret you type is passed in here and used here. It is not sent anywhere,
// because there is nowhere to send it -- there is no server behind this page.

importScripts('https://cdn.jsdelivr.net/pyodide/v0.28.3/full/pyodide.js');

let pyodide = null;

const say = (stage, detail) => postMessage({ type: 'status', stage, detail });

async function boot() {
  const t0 = performance.now();
  say('boot', 'downloading the Python runtime…');
  pyodide = await loadPyodide({
    indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.28.3/full/',
  });

  // hmac and hashlib are standard library, already inside the runtime. There
  // is nothing to pip install, which is most of the reason Python is here.
  say('boot', 'loading sign.py…');
  pyodide.FS.writeFile('/sign.py', await (await fetch('sign.py')).text());
  pyodide.runPython('import sys\nsys.path.insert(0, "/")\nimport json, sign');

  say('ready', `Python is running in your browser (${Math.round(performance.now() - t0)} ms).`);
}

const booted = boot().catch((e) => {
  postMessage({ type: 'fatal', error: String(e) });
  throw e;
});

onmessage = async ({ data: { id, args } }) => {
  try {
    await booted;
    say('signing', 'HMAC-SHA1 over the ordered fields…');

    // Cross the boundary as JSON in both directions. Same shape as a real
    // POST body, and it keeps sign.py free of any browser-specific typing.
    pyodide.globals.set('_payload', JSON.stringify(args));
    const out = pyodide.runPython(
      'json.dumps(sign.sign_embed_url(**json.loads(_payload)))'
    );

    postMessage({ type: 'signed', id, ...JSON.parse(out) });
  } catch (err) {
    postMessage({ type: 'error', id, error: String(err) });
  }
};
