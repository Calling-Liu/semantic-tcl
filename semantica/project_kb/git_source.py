from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


class GitSourceError(RuntimeError):
    pass


@dataclass(frozen=True)
class Snapshot:
    repository: Path
    revision: str
    commit_sha: str
    branch: str

    @property
    def snapshot_id(self) -> str:
        return f"git:{self.commit_sha}"


class GitSource:
    def __init__(self, repository: Path, revision: str = "HEAD") -> None:
        self.repository = repository.resolve()
        self._text_cache: dict[str, str] = {}
        commit_sha = self._run("rev-parse", revision).strip()
        branch = self._run("branch", "--show-current").strip() or "detached"
        self.snapshot = Snapshot(self.repository, revision, commit_sha, branch)

    def _run(self, *args: str, text: bool = True) -> str | bytes:
        result = subprocess.run(
            ["git", "-C", str(self.repository), *args],
            check=False,
            capture_output=True,
            text=text,
            encoding="utf-8" if text else None,
            errors="replace" if text else None,
        )
        if result.returncode:
            message = result.stderr.strip() if text else result.stderr.decode(errors="replace")
            raise GitSourceError(message)
        return result.stdout

    def files(self) -> dict[str, str]:
        output = self._run("ls-tree", "-r", self.snapshot.commit_sha)
        result: dict[str, str] = {}
        for line in output.splitlines():
            metadata, path = line.split("\t", 1)
            _mode, object_type, sha = metadata.split(" ", 2)
            if object_type == "blob":
                result[path.replace("\\", "/")] = sha
        return result

    def preload(self, paths: list[str]) -> None:
        blobs = self.files()
        requested = [(path, blobs[path]) for path in paths if path in blobs and path not in self._text_cache]
        if not requested:
            return
        process = subprocess.run(
            ["git", "-C", str(self.repository), "cat-file", "--batch"],
            input=("\n".join(sha for _, sha in requested) + "\n").encode("ascii"),
            capture_output=True,
            check=False,
        )
        if process.returncode:
            raise GitSourceError(process.stderr.decode(errors="replace"))
        output = process.stdout
        offset = 0
        for path, expected_sha in requested:
            header_end = output.index(b"\n", offset)
            sha, object_type, size_text = output[offset:header_end].decode("ascii").split(" ", 2)
            if sha != expected_sha or object_type != "blob":
                raise GitSourceError(f"Unexpected Git object for {path}")
            size = int(size_text)
            start = header_end + 1
            data = output[start:start + size]
            offset = start + size + 1
            if data.startswith(b"%TSD-Header-###%"):
                raise GitSourceError(f"Git object remains TSD protected: {path}")
            self._text_cache[path] = data.decode("utf-8", errors="replace")

    def text(self, path: str) -> str:
        normalized = path.replace("\\", "/")
        if normalized not in self._text_cache:
            self.preload([normalized])
        if normalized not in self._text_cache:
            raise GitSourceError(f"Path not found in snapshot: {normalized}")
        return self._text_cache[normalized]
