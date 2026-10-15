"""Secrets for every environment: mounted files, never environment variables.

Compose mounts one file per secret at ``/run/secrets/<name>`` — Docker's
secrets mechanism — and this module reads them. That is the whole story: no
environment variables, no ``secrets.py`` module in the tree.

Why files and not env vars. An environment variable is visible to anything
that can run ``docker inspect`` or read ``/proc/<pid>/environ``, and it lands
verbatim in crash reports and CI logs. A mounted secret file is per container,
is not printed by inspect, and rotation means rewriting one file instead of
recreating every container.

Why not a ``secrets.py`` module either. That was the old shape here: the whole
secret set was importable by any code in the process, one ``cat`` away on the
server and one ``git add`` away from being committed. Reading a named file per
secret keeps each value where it is used and makes an absent one obvious.

Fail-closed on purpose. A missing or blank secret raises at import, so a
half-provisioned box refuses to serve instead of quietly starting with a
default — which is exactly how production ended up running on the
``padel_prod_change_me`` password that lived as a compose default.

``SECRETS_DIR`` is a path, not a secret: it exists so host-side tooling (a
one-off inspection, a management command run outside a container) can read the
same files the containers see.
"""

from __future__ import annotations

import os
from pathlib import Path

SECRETS_DIR = Path(os.environ.get("SECRETS_DIR") or "/run/secrets")


def read(name: str, default: str | None = None) -> str:
    """Return the trimmed contents of ``<SECRETS_DIR>/<name>``.

    Raises ``RuntimeError`` when the file is missing or blank and no default
    was supplied, so a deployment that lost a secret fails at startup with the
    name of the file it could not read.
    """
    try:
        value = (SECRETS_DIR / name).read_text().strip()
    except FileNotFoundError:
        value = ""
    except PermissionError as exc:
        # Compose mounts file secrets with the host's mode intact, so a 0600
        # file created by root is unreadable by the container's uid 1000 —
        # and it looks identical to a missing file if OSError is swallowed
        # wholesale. Say which it is: the fix is `chmod 644` on the file with
        # the directory kept 0700, not reprovisioning a secret that is there.
        raise RuntimeError(
            f"Secret {name!r} exists in {SECRETS_DIR} but is not readable by "
            f"uid {os.getuid()}. The mount preserves the host's file mode; "
            f"chmod 644 that file (keep the directory 0700)."
        ) from exc
    except OSError:
        value = ""
    if value:
        return value
    if default is not None:
        return default
    raise RuntimeError(
        f"Secret {name!r} is missing or empty in {SECRETS_DIR}. "
        "Provision it as a Docker secret (make secrets-init) before starting."
    )


def optional(name: str) -> str:
    """Read a secret that some environments legitimately do not carry."""
    try:
        return read(name)
    except RuntimeError:
        return ""
