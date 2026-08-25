"""The server half of a signed Looker embed.

Nothing in this file knows it is running in a browser. Paste it into Flask,
FastAPI or a Lambda, hand it a secret from the environment instead of a form
field, and it behaves identically. That portability is the whole point: the
signing rules are fussy enough that you want to learn them once.

Private embed borrows a login that already exists. Signed embed manufactures
one -- and manufacturing it is what costs you a server, because the secret
below can mint a URL as any user with any permission.
"""

import base64
import hashlib
import hmac
import json
import secrets
import time
from urllib.parse import quote


def _encode(value):
    """Every signed field except the host and the path is JSON first.

    Compact separators are not cosmetic. Looker's own generator emits
    ["a","b"] with no space after the comma; json.dumps defaults to
    ["a", "b"], and those are different bytes going into the HMAC.
    """
    return json.dumps(value, separators=(",", ":"))


def sign_embed_url(
    host,
    secret,
    target,                    # e.g. "/embed/dashboards/223"
    embed_domain=None,         # usually None: the v2 SDK adds its own
    external_user_id="demo-reader",
    permissions=None,
    models=None,
    group_ids=None,
    external_group_id="",
    user_attributes=None,
    session_length=900,
    first_name="Demo",
    last_name="Reader",
    force_logout_login=True,
    ca_chat=False,
    include_ca_chat=False,     # see the note below the field list
    nonce=None,
    now=None,
):
    permissions = permissions or ["access_data", "see_lookml_dashboards",
                                  "see_user_dashboards"]
    models = models or []
    group_ids = group_ids or []
    user_attributes = user_attributes or {}
    nonce = nonce or secrets.token_hex(16)
    now = int(now if now is not None else time.time())

    # If you do pass embed_domain it rides INSIDE the encoded target, never as
    # a sibling query parameter -- outside, Looker answers
    # invalid params: ["embed_domain"]. Asked for one, this instance's own
    # generator dropped it: the v2 embed SDK supplies the value itself.
    embed_url = target if embed_domain is None else f"{target}?embed_domain={embed_domain}"

    # quote() emits uppercase hex. Lowercase %2f yields a 404 on /login/embed/,
    # which does not look like an encoding problem at all.
    embed_path = "/login/embed/" + quote(embed_url, safe="")

    access_filters = {}        # deprecated, still mandatory in the signature

    fields = [
        host,                  # not JSON-encoded
        embed_path,            # not JSON-encoded
        _encode(nonce),
        _encode(now),
        _encode(session_length),
        _encode(external_user_id),
        _encode(permissions),
        _encode(models),
        _encode(group_ids),
        _encode(external_group_id),
        _encode(user_attributes),
        _encode(access_filters),
    ]
    # The published field list ends with a 13th field, ca_chat. This
    # instance's own URL generator emits twelve and no ca_chat at all, so
    # twelve is the default and the 13th is a switch you can flip to watch
    # the signature get rejected.
    if include_ca_chat:
        fields.append(_encode(ca_chat))

    # Order is the entire contract. Drop a field and every field after it
    # shifts up one; the only feedback is a generic signature rejection.
    string_to_sign = "\n".join(fields)

    digest = hmac.new(
        secret.encode("utf-8"), string_to_sign.encode("utf-8"), hashlib.sha1
    ).digest()
    signature = base64.b64encode(digest).decode("utf-8")

    params = {
        "nonce": _encode(nonce),
        "time": _encode(now),
        "session_length": _encode(session_length),
        "external_user_id": _encode(external_user_id),
        "permissions": _encode(permissions),
        "models": _encode(models),
        "group_ids": _encode(group_ids),
        "external_group_id": _encode(external_group_id),
        "user_attributes": _encode(user_attributes),
        "access_filters": _encode(access_filters),
        "first_name": _encode(first_name),
        "last_name": _encode(last_name),
        "force_logout_login": _encode(force_logout_login),
    }
    if include_ca_chat:
        params["ca_chat"] = _encode(ca_chat)

    # Base64 emits '+', '/' and '='. A raw '+' in a query string decodes as a
    # SPACE, so forgetting this step corrupts roughly one signature in four --
    # intermittently, which sends people looking at clocks instead.
    query = "&".join(f"{k}={quote(v, safe='')}" for k, v in params.items())
    query += "&signature=" + quote(signature, safe="")

    return {
        "url": f"https://{host}{embed_path}&{query}"
        if "?" in embed_path
        else f"https://{host}{embed_path}?{query}",
        "string_to_sign": string_to_sign,
        "signature": signature,
    }
