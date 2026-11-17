#!/usr/bin/env python3
"""Shared ticket backlog: one CLI over GitHub Issues or local files.

Every worktree and session of a repo sees the same backlog. A feedback
session files tickets, worker sessions claim packs of them; claims are atomic
between processes on this machine (a mkdir lock in the git common dir).

Backend: PROFILE.md `## Tracker` -> `backend: github|local`, `repo: owner/name`.
Env overrides (tests, one-offs): BACKLOG_BACKEND, BACKLOG_REPO, BACKLOG_DIR.
Contract and state machine: work-tickets/references/backlog.md.

Exit codes: 0 ok, 1 error, 3 `claim` found nothing to claim.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

STATES = ["needs-info", "ready-for-agent", "ready-for-human", "claimed",
          "needs-check", "done", "wontfix"]
CLOSED = {"done", "wontfix"}
TYPES = ["bug", "enhancement", "task"]
PRIORITIES = ["p1", "p2", "p3"]
LOCK_WAIT_S = 60
LOCK_STALE_S = 120
META_RE = re.compile(r"\n*<!-- backlog: (.*?) -->\s*$", re.S)
BLOCKED_RE = re.compile(r"^Blocked by: (.*)$", re.M)


class Fail(Exception):
    pass


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run(*cmd, cwd=None, input=None):
    p = subprocess.run(cmd, cwd=cwd, input=input, capture_output=True, text=True)
    if p.returncode:
        raise Fail(f"{' '.join(cmd[:4])}…: {(p.stderr or p.stdout).strip()[:400]}")
    return p.stdout


def git_common_dir():
    d = run("git", "rev-parse", "--git-common-dir").strip()
    return Path(d if os.path.isabs(d) else os.path.join(os.getcwd(), d)).resolve()


def read_profile():
    try:
        root = Path(run("git", "rev-parse", "--show-toplevel").strip())
    except Fail:
        return {}
    f = root / "PROFILE.md"
    if not f.exists():
        return {}
    conf, inside = {}, False
    for line in f.read_text().splitlines():
        if line.startswith("## "):
            inside = bool(re.match(r"##\s+tracker\b", line, re.I))
            continue
        m = re.match(r"\s*(?:-\s+)?([a-z-]+):\s*([^#\s]+)", line) if inside else None
        if m:
            conf[m.group(1)] = m.group(2)
    return conf


class Lock:
    """mkdir lock holding the owner's pid; a dead or silent owner is broken."""

    def __init__(self, path):
        self.path = Path(path)

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.time() + LOCK_WAIT_S
        while True:
            try:
                self.path.mkdir()
                (self.path / "pid").write_text(str(os.getpid()))
                return self
            except FileExistsError:
                if self._stale():
                    shutil.rmtree(self.path, ignore_errors=True)
                    continue
                if time.time() > deadline:
                    raise Fail(f"backlog locked > {LOCK_WAIT_S}s: {self.path}")
                time.sleep(0.05)

    def _stale(self):
        try:
            age = time.time() - self.path.stat().st_mtime
            pid = int((self.path / "pid").read_text())
        except FileNotFoundError:
            return False  # gone already, or owner between mkdir and pid write
        except ValueError:
            return age > 5
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        except PermissionError:
            pass
        return age > LOCK_STALE_S

    def __exit__(self, *exc):
        shutil.rmtree(self.path, ignore_errors=True)


def new_ticket(**kw):
    t = {"id": "", "title": "", "type": "task", "area": "", "epic": "",
         "priority": "p2", "state": "ready-for-agent", "hands_on": False,
         "blocked_by": [], "claimed_by": "", "claimed_at": "", "created": now(),
         "closed_at": "", "body": ""}
    t.update(kw)
    return t


# ---------------------------------------------------------------- local

class Local:
    """One markdown file per ticket under <git-common-dir>/backlog/tickets/."""

    FIELDS = ["id", "title", "type", "area", "epic", "priority", "state", "hands-on",
              "blocked-by", "claimed-by", "claimed-at", "created", "closed-at"]

    def __init__(self, root):
        self.root = Path(root)
        self.dir = self.root / "tickets"

    def init(self):
        self.dir.mkdir(parents=True, exist_ok=True)
        (self.root / "assets").mkdir(exist_ok=True)
        return f"local backlog at {self.root}"

    def norm(self, tid):
        m = re.fullmatch(r"[Tt#]?0*(\d+)", str(tid).strip())
        if not m:
            raise Fail(f"bad ticket id {tid!r} (want T0001)")
        return f"T{int(m.group(1)):04d}"

    def path(self, tid):
        hits = sorted(self.dir.glob(f"{tid}-*.md")) if self.dir.exists() else []
        if not hits:
            raise Fail(f"no ticket {tid}")
        return hits[0]

    def parse(self, text):
        m = re.match(r"---\n(.*?)\n---\n?(.*)", text, re.S)
        if not m:
            raise Fail("ticket file without frontmatter")
        t = new_ticket(body=m.group(2).strip("\n"))
        for line in m.group(1).splitlines():
            k, _, v = line.partition(":")
            k, v = k.strip(), v.strip()
            if k == "blocked-by":
                t["blocked_by"] = [x.strip() for x in v.strip("[]").split(",") if x.strip()]
            elif k == "hands-on":
                t["hands_on"] = v == "true"
            elif k:
                t[k.replace("-", "_")] = "" if v == "none" else json.loads(v) if v.startswith('"') else v
        return t

    def dump(self, t):
        rows = []
        for f in self.FIELDS:
            k = f.replace("-", "_")
            if f == "blocked-by":
                v = "[" + ", ".join(t["blocked_by"]) + "]"
            elif f == "hands-on":
                v = "true" if t["hands_on"] else "false"
            else:
                v = t[k] or "none"
                if f == "title":
                    v = json.dumps(v, ensure_ascii=False)
            rows.append(f"{f}: {v}")
        return "---\n" + "\n".join(rows) + "\n---\n\n" + t["body"].rstrip("\n") + "\n"

    def load_all(self):
        if not self.dir.exists():
            raise Fail(f"no local backlog at {self.root}; run `backlog.py init`")
        return [self.parse(p.read_text()) for p in sorted(self.dir.glob("T*.md"))]

    def get(self, tid):
        return self.parse(self.path(self.norm(tid)).read_text())

    def save(self, t, note=None, who=""):
        if note:
            t["body"] = append_comment(t["body"], note, who)
        try:
            p = self.path(t["id"])
        except Fail:
            p = self.dir / f"{t['id']}-{slug(t['title'])}.md"
        tmp = p.with_suffix(".tmp")
        tmp.write_text(self.dump(t))
        tmp.replace(p)

    def create(self, t):
        nums = [int(p.name[1:5]) for p in self.dir.glob("T[0-9][0-9][0-9][0-9]-*.md")]
        t["id"] = f"T{max(nums, default=0) + 1:04d}"
        self.save(t)
        return t["id"]

    def comment(self, t, note, who):
        self.save(t, note, who)


def append_comment(body, note, who):
    if "\n## Comments" not in "\n" + body:
        body = body.rstrip("\n") + "\n\n## Comments\n"
    return body.rstrip("\n") + f"\n- {now()} {who or 'agent'}: {note}\n"


def slug(title):
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return s[:48].rstrip("-") or "ticket"


# ---------------------------------------------------------------- github

class GitHub:
    """One issue per ticket; fields in labels, claim in a body meta line."""

    def __init__(self, repo):
        self.repo = repo

    def gh(self, *args, input=None):
        extra = ["-R", self.repo] if self.repo else []
        return run("gh", args[0], args[1], *extra, *args[2:], input=input)

    def init(self):
        for name, color in ([(f"state:{s}", "c5def5") for s in STATES] +
                            [(f"type:{t}", "fbca04") for t in TYPES] +
                            [(p, "d93f0b") for p in PRIORITIES] + [("hands-on", "0e8a16")]):
            self.label(name, color)
        return f"github backlog labels ready{' on ' + self.repo if self.repo else ''}"

    def label(self, name, color="ededed"):
        self.gh("label", "create", name, "--color", color, "--force")

    def norm(self, tid):
        m = re.fullmatch(r"#?(\d+)", str(tid).strip())
        if not m:
            raise Fail(f"bad issue id {tid!r} (want #123)")
        return f"#{m.group(1)}"

    def from_issue(self, i):
        labels = [l["name"] for l in i.get("labels", [])]
        body = i.get("body") or ""
        meta = {}
        m = META_RE.search(body)
        if m:
            meta = dict(kv.split("=", 1) for kv in m.group(1).split() if "=" in kv)
            body = body[:m.start()]
        b = BLOCKED_RE.search(body)
        blocked = [x.strip() for x in b.group(1).split(",") if x.strip()] if b else []
        if b:
            body = (body[:b.start()] + body[b.end():])
        pick = lambda pre: next((l[len(pre):] for l in labels if l.startswith(pre)), "")
        state = pick("state:") or ("done" if i.get("state") == "CLOSED" else "ready-for-agent")
        return new_ticket(
            id=f"#{i['number']}", title=i["title"], type=pick("type:") or "task",
            area=pick("area:"), epic=pick("epic:"),
            priority=next((l for l in labels if l in PRIORITIES), "p2"), state=state,
            hands_on="hands-on" in labels, blocked_by=blocked,
            claimed_by=meta.get("claimed-by", ""), claimed_at=meta.get("claimed-at", ""),
            created=i.get("createdAt", ""), closed_at=i.get("closedAt") or "",
            body=body.strip("\n"), labels=labels)

    def load_all(self):
        rows = json.loads(self.gh("issue", "list", "--state", "all", "--limit", "1000", "--json",
                                  "number,title,body,labels,state,createdAt,closedAt"))
        return [self.from_issue(i) for i in rows]

    def get(self, tid):
        n = self.norm(tid)[1:]
        return self.from_issue(json.loads(self.gh(
            "issue", "view", n, "--json", "number,title,body,labels,state,createdAt,closedAt")))

    def render_body(self, t):
        body = t["body"].rstrip("\n")
        if t["blocked_by"]:
            body += "\n\nBlocked by: " + ", ".join(t["blocked_by"])
        if t["claimed_by"]:
            body += f"\n\n<!-- backlog: claimed-by={t['claimed_by']} claimed-at={t['claimed_at']} -->"
        return body + "\n"

    def want_labels(self, t):
        ls = [f"state:{t['state']}", f"type:{t['type']}", t["priority"]]
        ls += [f"area:{t['area']}"] if t["area"] else []
        ls += [f"epic:{t['epic']}"] if t["epic"] else []
        ls += ["hands-on"] if t["hands_on"] else []
        return ls

    def create(self, t):
        for l in self.want_labels(t):
            if l.startswith(("area:", "epic:")):
                self.label(l)
        url = self.gh("issue", "create", "--title", t["title"], "--body-file", "-",
                      *sum((["--label", l] for l in self.want_labels(t)), []),
                      input=self.render_body(t)).strip()
        m = re.search(r"/issues/(\d+)", url)
        if not m:
            raise Fail(f"gh issue create returned no issue URL: {url[:200]}")
        t["id"] = f"#{m.group(1)}"
        return t["id"]

    def save(self, t, note=None, who=""):
        n = t["id"][1:]
        old = self.get(t["id"])
        have, want = set(old["labels"]), set(self.want_labels(t))
        managed = lambda l: l.startswith(("state:", "type:", "area:", "epic:")) or l in PRIORITIES or l == "hands-on"
        args = []
        for l in sorted(want - have):
            if l.startswith(("area:", "epic:")):
                self.label(l)
            args += ["--add-label", l]
        for l in sorted(l for l in have - want if managed(l)):
            args += ["--remove-label", l]
        if self.render_body(old) != self.render_body(t):
            args += ["--body-file", "-"]
        if args:
            self.gh("issue", "edit", n, *args, input=self.render_body(t))
        if t["state"] in CLOSED and old["state"] not in CLOSED:
            reason = ["--reason", "not planned"] if t["state"] == "wontfix" else []
            self.gh("issue", "close", n, *reason)
        elif t["state"] not in CLOSED and old["state"] in CLOSED:
            self.gh("issue", "reopen", n)
        if note:
            self.comment(t, note, who)

    def comment(self, t, note, who):
        self.gh("issue", "comment", t["id"][1:], "--body-file", "-",
                input=f"{who or 'agent'}: {note}\n")


# ---------------------------------------------------------------- shared ops

def backend():
    conf = read_profile()
    kind = os.environ.get("BACKLOG_BACKEND") or conf.get("backend") or "local"
    if kind == "github":
        return GitHub(os.environ.get("BACKLOG_REPO") or conf.get("repo", ""))
    if kind == "local":
        return Local(os.environ.get("BACKLOG_DIR") or git_common_dir() / "backlog")
    raise Fail(f"unknown tracker backend {kind!r} (github | local)")


def lock_path():
    base = os.environ.get("BACKLOG_DIR")
    return Path(base) / ".lock" if base else git_common_dir() / "backlog" / ".lock"


def assets_dir(tid):
    base = Path(os.environ["BACKLOG_DIR"]) if os.environ.get("BACKLOG_DIR") else git_common_dir() / "backlog"
    return base / "assets" / tid.lstrip("#")


def frontier(tickets, area="", type_="", epic="", ids=None):
    state = {t["id"]: t["state"] for t in tickets}
    out = []
    for t in tickets:
        if t["state"] != "ready-for-agent":
            continue
        if any(state.get(b) != "done" for b in t["blocked_by"]):
            continue
        if ids is not None and t["id"] not in ids:
            continue
        if (area and t["area"] != area) or (type_ and t["type"] != type_) or (epic and t["epic"] != epic):
            continue
        out.append(t)
    return sorted(out, key=lambda t: (t["priority"], t["created"], t["id"]))


def line(t):
    extra = []
    if t["blocked_by"]:
        extra.append("blocked-by " + ",".join(t["blocked_by"]))
    if t["claimed_by"]:
        extra.append(f"claimed-by {t['claimed_by']} since {t['claimed_at']}")
    if t["hands_on"]:
        extra.append("hands-on")
    tail = f"  [{'; '.join(extra)}]" if extra else ""
    return f"{t['id']}\t{t['state']}\t{t['priority']} {t['type']}\t{t['area'] or '-'}\t{t['title']}{tail}"


def public(t):
    return {k: v for k, v in t.items() if k != "labels"}


def cmd_init(b, a):
    print(b.init())


def cmd_new(b, a):
    body = sys.stdin.read() if a.body_file == "-" else Path(a.body_file).read_text()
    blocked = [b.norm(x) for x in a.blocked_by.split(",") if x.strip()] if a.blocked_by else []
    t = new_ticket(title=a.title, type=a.type, area=a.area, epic=a.epic or "",
                   priority=a.priority, state=a.state, hands_on=a.hands_on,
                   blocked_by=blocked, body=body)
    with Lock(lock_path()):
        tid = b.create(t)
    if a.attach:
        attach(b, tid, a.attach, a.who)
    print(tid)


def attach(b, tid, files, who):
    d = assets_dir(tid)
    d.mkdir(parents=True, exist_ok=True)
    kept = []
    for f in files:
        src = Path(f)
        if not src.is_file():
            raise Fail(f"no file {f}")
        dst = d / src.name
        shutil.copy2(src, dst)
        kept.append(str(dst))
    with Lock(lock_path()):
        b.comment(b.get(tid), "attached " + ", ".join(kept), who)
    return kept


def cmd_attach(b, a):
    for p in attach(b, b.norm(a.id), a.files, a.who):
        print(p)


def cmd_show(b, a):
    t = b.get(a.id)
    if a.json:
        print(json.dumps(public(t), indent=1, ensure_ascii=False))
    else:
        print(line(t) + "\n\n" + t["body"])


def cmd_list(b, a):
    ts = b.load_all()
    if a.frontier:
        ts = frontier(ts, a.area, a.type, a.epic)
    else:
        if a.state:
            ts = [t for t in ts if t["state"] == a.state]
        elif not a.all:
            ts = [t for t in ts if t["state"] not in CLOSED]
        ts = [t for t in ts if (not a.area or t["area"] == a.area) and
              (not a.type or t["type"] == a.type) and (not a.epic or t["epic"] == a.epic)]
    if a.closed_since:
        ts = [t for t in ts if t["closed_at"] and t["closed_at"][:10] >= a.closed_since]
    if a.search:
        words = a.search.lower().split()
        ts = [t for t in ts if all(w in (t["title"] + " " + t["body"]).lower() for w in words)]
    if a.json:
        print(json.dumps([public(t) for t in ts], indent=1, ensure_ascii=False))
    else:
        for t in ts:
            print(line(t))


def cmd_claim(b, a):
    ids = {b.norm(x) for x in a.ids.split(",") if x.strip()} if a.ids else None
    claimed = []
    with Lock(lock_path()):
        for t in frontier(b.load_all(), a.area, a.type, a.epic, ids)[:a.max]:
            t.update(state="claimed", claimed_by=a.who, claimed_at=now())
            b.save(t, f"claimed by {a.who}", a.who)
            claimed.append(t)
    if a.json:
        print(json.dumps([public(t) for t in claimed], indent=1, ensure_ascii=False))
    else:
        for t in claimed:
            print(f"{t['id']}\t{t['title']}")
    if not claimed:
        print("nothing to claim", file=sys.stderr)
        return 3


def cmd_unclaim(b, a):
    with Lock(lock_path()):
        t = b.get(a.id)
        if t["state"] != "claimed":
            raise Fail(f"{t['id']} is {t['state']}, not claimed")
        t.update(state="ready-for-agent", claimed_by="", claimed_at="")
        b.save(t, f"unclaimed: {a.note}", a.who)
    print(f"{t['id']} ready-for-agent")


def cmd_set(b, a):
    if a.state == "claimed":
        raise Fail("use `claim` to claim")
    with Lock(lock_path()):
        t = b.get(a.id)
        t["state"] = a.state
        if a.state in ("needs-info", "ready-for-agent", "ready-for-human"):
            t.update(claimed_by="", claimed_at="")  # back in the pool; needs-check/done keep who did it
        if a.state in CLOSED and not t["closed_at"]:
            t["closed_at"] = now()
        elif a.state not in CLOSED:
            t["closed_at"] = ""
        b.save(t, f"{a.state}: {a.note}", a.who)
    print(f"{t['id']} {a.state}")


def cmd_comment(b, a):
    with Lock(lock_path()):
        b.comment(b.get(a.id), a.note, a.who)
    print(f"{b.norm(a.id)} commented")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    who = argparse.ArgumentParser(add_help=False)
    who.add_argument("--as", dest="who", default=os.environ.get("BACKLOG_WHO", ""),
                     help="session or worker name for claims and comments")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add(name, **kw):
        return sub.add_parser(name, parents=[who], **kw)

    add("init", help="create labels (github) or the backlog dir (local)")

    n = add("new", help="file a ticket; prints its id")
    n.add_argument("--title", required=True)
    n.add_argument("--type", choices=TYPES, required=True)
    n.add_argument("--area", required=True)
    n.add_argument("--epic")
    n.add_argument("--priority", choices=PRIORITIES, default="p2")
    n.add_argument("--state", choices=[s for s in STATES if s not in ("claimed",) + tuple(CLOSED)],
                   default="ready-for-agent")
    n.add_argument("--hands-on", action="store_true", help="only the user can judge the result")
    n.add_argument("--blocked-by", help="comma-separated ids")
    n.add_argument("--body-file", required=True, help="agent brief markdown, or - for stdin")
    n.add_argument("--attach", nargs="+", help="screenshots to keep with the ticket")

    s = add("show")
    s.add_argument("id")
    s.add_argument("--json", action="store_true")

    l = add("list", help="open tickets by default")
    l.add_argument("--state", choices=STATES)
    l.add_argument("--all", action="store_true", help="include done and wontfix")
    l.add_argument("--frontier", action="store_true", help="ready-for-agent and unblocked")
    l.add_argument("--area", default="")
    l.add_argument("--type", choices=TYPES)
    l.add_argument("--epic", default="")
    l.add_argument("--search", help="every word must appear in title or body")
    l.add_argument("--closed-since", help="YYYY-MM-DD")
    l.add_argument("--json", action="store_true")

    c = add("claim", help="atomically claim up to --max frontier tickets")
    c.add_argument("--area", default="")
    c.add_argument("--type", choices=TYPES)
    c.add_argument("--epic", default="")
    c.add_argument("--ids", help="comma-separated ids to claim from the frontier")
    c.add_argument("--max", type=int, default=5)
    c.add_argument("--json", action="store_true")

    u = add("unclaim")
    u.add_argument("id")
    u.add_argument("--note", required=True)

    st = add("set", help="move a ticket to another state")
    st.add_argument("id")
    st.add_argument("--state", choices=STATES, required=True)
    st.add_argument("--note", required=True)

    cm = add("comment")
    cm.add_argument("id")
    cm.add_argument("--note", required=True)

    at = add("attach")
    at.add_argument("id")
    at.add_argument("files", nargs="+")

    a = p.parse_args(argv)
    if a.cmd == "claim" and not a.who:
        p.error("claim needs --as NAME (or BACKLOG_WHO)")
    try:
        b = backend()
        if hasattr(a, "id"):
            a.id = b.norm(a.id)
        return {"init": cmd_init, "new": cmd_new, "show": cmd_show, "list": cmd_list,
                "claim": cmd_claim, "unclaim": cmd_unclaim, "set": cmd_set,
                "comment": cmd_comment, "attach": cmd_attach}[a.cmd](b, a) or 0
    except Fail as e:
        print(f"backlog: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
