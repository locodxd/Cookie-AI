# tremenda forma cagada a palos para poder tener un json store simple 
# mañana no amanece esto


import os
import json
import time
from pathlib import Path
from contextlib import contextmanager
try:
    import fcntl 
    HAS_FCNTL = True
except Exception:
    HAS_FCNTL = False

import threading
class JsonChatStore:
    def __init__(
        self,
        root_dir: str = "data/store",
        compact_every_events: int = 25,
        compact_if_wal_kb: int = 512,
        max_messages_per_session: int = 200,
    ):
        self.root = Path(root_dir)
        self.root.mkdir(parents=True, exist_ok=True)
        self.snapshot_path = self.root / "snapshot.json"
        self.wal_path = self.root / "wal.jsonl"
        self.lock_path = self.root / "store.lock"
        self.compact_every_events = max(1, int(compact_every_events))
        self.compact_if_wal_kb = max(64, int(compact_if_wal_kb))
        self.max_messages_per_session = max(20, int(max_messages_per_session))

        self._events_since_compact = 0
        self._mem_lock = threading.RLock()
        self.state = {"sessions": {}}
        self._lock_fd = open(self.lock_path, "a+", encoding="utf-8")

        self._load_from_disk()

    @contextmanager
    def _lock(self):
        with self._mem_lock:
            if HAS_FCNTL:
                fcntl.flock(self._lock_fd.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                if HAS_FCNTL:
                    fcntl.flock(self._lock_fd.fileno(), fcntl.LOCK_UN)

    def _readear_json(self, path: Path, default):
        try:
            if not path.exists():
                return default
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
        
    def _load_from_disk(self):
        with self._lock():
            self.state = self._read_json(self.snapshot_path, {"sessions": {}})
            if self.wal_path.exists():
                try:
                    with open(self.wal_path, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                evt = json.loads(line)
                                self._apply_event(evt, from_replay=True)
                            except Exception:
                                continue
                except Exception:
                    pass
            self._maybe_compact(force=False)
    def _fsync_file(self, f):
        f.flush()
        os.fsync(f.fileno())

    def _fsync_dir(self, path: Path):
        try:
            dir_fd = os.open(str(path), os.O_DIRECTORY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        except Exception:
            pass
    def _atomic_write_json(self, path: Path, data: dict):
        tmp = path.with_suffix(path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            self._fsync_file(f)
        os.replace(tmp, path)
        self._fsync_dir(path.parent)
    def _append_wal(self, evt: dict):
        self.wal_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.wal_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(evt, ensure_ascii=False) + "\n")
            self._fsync_file(f)

    def _apply_event(self, evt: dict, from_replay: bool = False):
        t = evt.get("type")
        if t == "append_message":
            sid = evt["session_id"]
            msg = evt["message"]
            sess = self.state["sessions"].setdefault(
                sid,
                {"created_at": evt.get("ts"), "messages": [], "meta": {}},
            )
            sess["messages"].append(msg)
            if len(sess["messages"]) > self.max_messages_per_session:
                sess["messages"] = sess["messages"][-self.max_messages_per_session :]

        elif t == "clear_session":
            sid = evt["session_id"]
            if sid in self.state["sessions"]:
                self.state["sessions"][sid]["messages"] = []

        elif t == "set_session_meta":
            sid = evt["session_id"]
            meta = evt.get("meta", {})
            sess = self.state["sessions"].setdefault(
                sid,
                {"created_at": evt.get("ts"), "messages": [], "meta": {}},
            )
            sess["meta"].update(meta)
        if not from_replay:
            self._events_since_compact += 1

    def _maybe_compact(self, force: bool):
        wal_kb = (self.wal_path.stat().st_size // 1024) if self.wal_path.exists() else 0
        if force or (self._events_since_compact >= self.compact_every_events) or (wal_kb >= self.compact_if_wal_kb):
            self._atomic_write_json(self.snapshot_path, self.state)
            tmp = self.wal_path.with_suffix(".jsonl.tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                self._fsync_file(f)
            os.replace(tmp, self.wal_path)
            self._fsync_dir(self.wal_path.parent)

            self._events_since_compact = 0
    def append_message(self, session_id: str, role: str, content: str, attachments: dict | None = None, model: str | None = None):
        evt = {
            "type": "append_message",
            "session_id": session_id,
            "ts": time.time(),
            "message": {
                "role": role,
                "content": content,
                "model": model,
                "attachments": attachments or {},
                "ts": time.time(),
            },
        }
        with self._lock():
            self._append_wal(evt)
            self._apply_event(evt)
            self._maybe_compact(force=False)

    def set_session_meta(self, session_id: str, meta: dict):
        evt = {
            "type": "set_session_meta",
            "session_id": session_id,
            "ts": time.time(),
            "meta": meta,
        }
        with self._lock():
            self._append_wal(evt)
            self._apply_event(evt)
            self._maybe_compact(force=False)

    def clear_session(self, session_id: str):
        evt = {"type": "clear_session", "session_id": session_id, "ts": time.time()}
        with self._lock():
            self._append_wal(evt)
            self._apply_event(evt)
            self._maybe_compact(force=True)

    def get_history(self, session_id: str, limit: int = 10):
        with self._lock():
            sess = self.state["sessions"].get(session_id)
            if not sess:
                return []
            msgs = sess.get("messages", [])
            out = []
            for m in msgs[-limit:]:
                role = m.get("role")
                content = (m.get("content") or "").strip()
                if not content:
                    continue
                out.append({"role": role, "content": content})
            return out