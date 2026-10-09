from __future__ import annotations

import hashlib
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import PurePosixPath
from typing import Any

import javalang

from .git_source import GitSource
from .store import Store


ANDROID_NS = "{http://schemas.android.com/apk/res/android}"
SOURCE_SUFFIXES = (".java", ".kt", ".aidl", ".xml", ".pro", ".gradle", ".gradle.kts")


def stable_id(*parts: str) -> str:
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


def access(modifiers: set[str]) -> str:
    for value in ("public", "protected", "private"):
        if value in modifiers:
            return value
    return "package"


def java_type(node: Any) -> str:
    if node is None:
        return "void"
    name = getattr(node, "name", None) or str(node)
    dimensions = getattr(node, "dimensions", None) or []
    return name + "[]" * len(dimensions)


class Extractor:
    def __init__(self, source: GitSource, store: Store, project_name: str) -> None:
        self.source = source
        self.store = store
        self.project_name = project_name
        self.snapshot_id = source.snapshot.snapshot_id
        self.files = source.files()
        self.module_roots = self._module_roots()
        self.types_by_name: dict[str, list[str]] = defaultdict(list)
        self.methods_by_name: dict[str, list[str]] = defaultdict(list)
        self.methods_by_owner: dict[tuple[str, str], list[str]] = defaultdict(list)
        self.pending_calls: list[tuple[str, str, str | None, str, int | None]] = []
        self.counts: dict[str, int] = defaultdict(int)

    def build(self) -> dict[str, Any]:
        snapshot = self.source.snapshot
        with self.store.transaction():
            self.store.reset(self.snapshot_id)
            self.store.execute(
                "INSERT INTO snapshots VALUES(?,?,?,?,?,?,CURRENT_TIMESTAMP,?)",
                (self.snapshot_id, self.project_name, str(snapshot.repository), snapshot.commit_sha,
                 snapshot.branch, snapshot.revision, "building"),
            )
            paths = [path for path in self.files if path.endswith(SOURCE_SUFFIXES)]
            self.source.preload(paths)
            self._insert_modules()
            for path in paths:
                if path.endswith(".java"):
                    self._java(path)
                elif path.endswith(".kt"):
                    self._kotlin(path)
            self._resolve_calls()
            self._gradle(paths)
            self._aidl(paths)
            self._manifest(paths)
            self._proguard(paths)
            self.store.execute("UPDATE snapshots SET status='ready' WHERE snapshot_id=?", (self.snapshot_id,))
        self.counts["symbols"] = self.store.query(
            "SELECT count(*) value FROM symbols WHERE snapshot_id=?", (self.snapshot_id,)
        )[0]["value"]
        self.counts["relations"] = self.store.query(
            "SELECT count(*) value FROM relations WHERE snapshot_id=?", (self.snapshot_id,)
        )[0]["value"]
        return {"snapshot_id": self.snapshot_id, "commit_sha": snapshot.commit_sha, "counts": dict(self.counts)}

    def _module_roots(self) -> dict[str, str]:
        roots: dict[str, str] = {".": "root"}
        for path in self.files:
            if path.endswith(("build.gradle", "build.gradle.kts")):
                parent = str(PurePosixPath(path).parent)
                roots[parent] = PurePosixPath(parent).name if parent != "." else "root"
        return roots

    def _module(self, path: str) -> tuple[str, str]:
        candidates = [root for root in self.module_roots if path == root or path.startswith(root.rstrip("/") + "/")]
        root = max(candidates, key=len) if candidates else "."
        return self.module_roots[root], root

    def _insert_modules(self) -> None:
        for path, name in sorted(self.module_roots.items()):
            self.store.execute(
                "INSERT OR REPLACE INTO modules VALUES(?,?,?,?)",
                (self.snapshot_id, f"module:{name}:{stable_id(path)[:10]}", name, path),
            )
        self.counts["modules"] = len(self.module_roots)

    def _symbol(self, symbol_id: str, kind: str, language: str, module: str, fqn: str,
                name: str, signature: str, path: str, line: int | None,
                accessibility: str, parser: str) -> None:
        self.store.execute(
            "INSERT OR REPLACE INTO symbols VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (self.snapshot_id, symbol_id, kind, language, module, fqn, name, signature,
             path, line, accessibility, parser, ),
        )
        self.counts[f"{language}_{kind}"] += 1

    def _entity(self, entity_id: str, kind: str, name: str, module: str, path: str,
                line: int | None = None, metadata: dict[str, Any] | None = None) -> None:
        self.store.execute(
            "INSERT OR REPLACE INTO entities VALUES(?,?,?,?,?,?,?,?)",
            (self.snapshot_id, entity_id, kind, name, module, path, line, self.store.json(metadata or {})),
        )
        self.counts[f"entity_{kind}"] += 1

    def _relation(self, source_id: str, target_id: str | None, relation_type: str,
                  path: str, target_text: str | None = None,
                  evidence_kind: str = "STATIC", resolution: str = "RESOLVED") -> None:
        relation_id = stable_id(self.snapshot_id, source_id, target_id or "", target_text or "", relation_type)
        self.store.execute(
            "INSERT OR REPLACE INTO relations VALUES(?,?,?,?,?,?,?,?,?)",
            (self.snapshot_id, relation_id, source_id, target_id, target_text, relation_type,
             evidence_kind, resolution, path),
        )

    def _java(self, path: str) -> None:
        text = self.source.text(path)
        try:
            tree = javalang.parse.parse(text)
        except (javalang.parser.JavaSyntaxError, IndexError, TypeError):
            self.counts["java_parse_failures"] += 1
            return
        package = tree.package.name if tree.package else ""
        module, module_root = self._module(path)
        module_id = f"module:{module}:{stable_id(module_root)[:10]}"
        for _, type_node in tree.filter(javalang.tree.TypeDeclaration):
            kind = type(type_node).__name__.replace("Declaration", "").lower()
            fqn = f"{package}.{type_node.name}" if package else type_node.name
            type_id = f"java:{fqn}"
            modifiers = set(type_node.modifiers or set())
            self._symbol(type_id, kind, "java", module, fqn, type_node.name, fqn, path,
                         getattr(getattr(type_node, "position", None), "line", None),
                         access(modifiers), "javalang")
            self.types_by_name[type_node.name].append(type_id)
            self._relation(type_id, module_id, "DECLARED_IN", path, evidence_kind="DECLARED")
            declarations = list(getattr(type_node, "methods", None) or [])
            declarations += list(getattr(type_node, "constructors", None) or [])
            for method in declarations:
                parameters = [java_type(parameter.type) + ("..." if parameter.varargs else "")
                              for parameter in method.parameters]
                descriptor = "(" + ",".join(parameters) + ")"
                method_id = f"java:{fqn}#{method.name}{descriptor}"
                method_modifiers = set(method.modifiers or set())
                if kind == "interface":
                    method_modifiers.add("public")
                signature = f"{java_type(getattr(method, 'return_type', None))} {method.name}{descriptor}"
                line = getattr(getattr(method, "position", None), "line", None)
                self._symbol(method_id, "method", "java", module, fqn, method.name,
                             signature, path, line, access(method_modifiers), "javalang")
                self.methods_by_name[method.name].append(method_id)
                self.methods_by_owner[(fqn, method.name)].append(method_id)
                self._relation(type_id, method_id, "DECLARES", path)
                for _, invocation in method.filter(javalang.tree.MethodInvocation):
                    invocation_line = getattr(getattr(invocation, "position", None), "line", None)
                    self.pending_calls.append(
                        (method_id, invocation.member, invocation.qualifier, path, invocation_line)
                    )
                for _, creation in method.filter(javalang.tree.ClassCreator):
                    target_name = java_type(creation.type)
                    candidates = self.types_by_name.get(target_name, [])
                    target_id = candidates[0] if len(candidates) == 1 else None
                    self._relation(method_id, target_id, "INSTANTIATES", path, target_name,
                                   resolution="RESOLVED" if target_id else "UNRESOLVED")
        self.counts["java_files"] += 1

    def _kotlin(self, path: str) -> None:
        text = self.source.text(path)
        package_match = re.search(r"^\s*package\s+([\w.]+)", text, re.MULTILINE)
        package = package_match.group(1) if package_match else ""
        module, module_root = self._module(path)
        module_id = f"module:{module}:{stable_id(module_root)[:10]}"
        type_pattern = re.compile(
            r"^\s*(?:(public|internal|private|protected)\s+)?(?:data\s+|sealed\s+|open\s+|abstract\s+)?"
            r"(class|interface|object|enum\s+class)\s+(\w+)", re.MULTILINE,
        )
        owners: list[tuple[int, str, str]] = []
        for match in type_pattern.finditer(text):
            visibility, raw_kind, name = match.groups()
            kind = "enum" if raw_kind.startswith("enum") else raw_kind
            fqn = f"{package}.{name}" if package else name
            symbol_id = f"kotlin:{fqn}"
            line = text[:match.start()].count("\n") + 1
            self._symbol(symbol_id, kind, "kotlin", module, fqn, name, fqn, path, line,
                         visibility or "public", "kotlin-regex")
            self.types_by_name[name].append(symbol_id)
            self._relation(symbol_id, module_id, "DECLARED_IN", path, evidence_kind="DECLARED")
            owners.append((match.start(), fqn, symbol_id))
        function_pattern = re.compile(
            r"^\s*(?:(public|internal|private|protected)\s+)?(?:suspend\s+|inline\s+|open\s+|override\s+)*"
            r"fun\s+(?:<[^>]+>\s*)?(\w+)\s*\(([^)]*)\)", re.MULTILINE,
        )
        for match in function_pattern.finditer(text):
            visibility, name, parameters = match.groups()
            owner = max((item for item in owners if item[0] < match.start()), default=None, key=lambda item: item[0])
            owner_fqn = owner[1] if owner else package
            descriptor = "(" + re.sub(r"\s+", " ", parameters.strip()) + ")"
            symbol_id = f"kotlin:{owner_fqn}#{name}{descriptor}"
            line = text[:match.start()].count("\n") + 1
            self._symbol(symbol_id, "method", "kotlin", module, owner_fqn, name,
                         f"fun {name}{descriptor}", path, line, visibility or "public", "kotlin-regex")
            self.methods_by_name[name].append(symbol_id)
            if owner:
                self._relation(owner[2], symbol_id, "DECLARES", path)
        self.counts["kotlin_files"] += 1

    def _resolve_calls(self) -> None:
        for source_id, name, qualifier, path, _line in self.pending_calls:
            owner = source_id.split("#", 1)[0].removeprefix("java:")
            target_id = None
            if not qualifier or qualifier in {"this", "super"}:
                candidates = self.methods_by_owner.get((owner, name), [])
                target_id = candidates[0] if len(candidates) == 1 else None
            if not target_id and not qualifier:
                candidates = self.methods_by_name.get(name, [])
                target_id = candidates[0] if len(candidates) == 1 else None
            target_text = f"{qualifier + '.' if qualifier else ''}{name}"
            self._relation(source_id, target_id, "CALLS", path, target_text,
                           resolution="RESOLVED" if target_id else "UNRESOLVED")

    def _gradle(self, paths: list[str]) -> None:
        for path in paths:
            if not path.endswith(("build.gradle", "build.gradle.kts")):
                continue
            text = self.source.text(path)
            module, module_root = self._module(path)
            source_id = f"module:{module}:{stable_id(module_root)[:10]}"
            patterns = [
                r"\b(api|implementation|compileOnly|runtimeOnly)\s+project\s*\(?(?:path\s*[=:]\s*)?['\"]:([^'\"]+)",
                r"\b(api|implementation|compileOnly|runtimeOnly)\s*\(project\(['\"]:([^'\"]+)",
            ]
            for pattern in patterns:
                for match in re.finditer(pattern, text):
                    dependency_type, target_name = match.groups()
                    matching = [
                        (root, name) for root, name in self.module_roots.items()
                        if name == target_name or root.endswith("/" + target_name)
                    ]
                    target_id = None
                    if len(matching) == 1:
                        root, name = matching[0]
                        target_id = f"module:{name}:{stable_id(root)[:10]}"
                    self._relation(source_id, target_id, "MODULE_DEPENDS_ON", path,
                                   f"{dependency_type}:{target_name}", "DECLARED",
                                   "RESOLVED" if target_id else "UNRESOLVED")

    def _aidl(self, paths: list[str]) -> None:
        for path in paths:
            if not path.endswith(".aidl"):
                continue
            text = self.source.text(path)
            module, _ = self._module(path)
            package_match = re.search(r"\bpackage\s+([\w.]+)\s*;", text)
            package = package_match.group(1) if package_match else ""
            parcelable = re.search(r"\bparcelable\s+(\w+)\s*;", text)
            if parcelable:
                name = parcelable.group(1)
                self._entity(f"aidl:parcelable:{package}.{name}", "aidl_parcelable", name,
                             module, path, metadata={"package": package})
                continue
            interface = re.search(r"\binterface\s+(\w+)\s*\{", text)
            if not interface:
                continue
            name = interface.group(1)
            interface_id = f"aidl:interface:{package}.{name}"
            self._entity(interface_id, "aidl_interface", name, module, path,
                         metadata={"package": package})
            body = text[interface.end():text.rfind("}")]
            for match in re.finditer(r"([\w.<>\[\]]+)\s+(\w+)\s*\(([^)]*)\)\s*;", body):
                return_type, method_name, parameters = match.groups()
                method_id = f"aidl:method:{package}.{name}#{method_name}"
                line = text[:interface.end() + match.start()].count("\n") + 1
                self._entity(method_id, "aidl_method", method_name, module, path, line,
                             {"return_type": return_type, "parameters": parameters.strip()})
                self._relation(interface_id, method_id, "DECLARES", path, evidence_kind="DECLARED")

    def _manifest(self, paths: list[str]) -> None:
        for path in paths:
            if not path.endswith("AndroidManifest.xml"):
                continue
            text = self.source.text(path)
            module, module_root = self._module(path)
            module_id = f"module:{module}:{stable_id(module_root)[:10]}"
            try:
                root = ET.fromstring(text)
            except ET.ParseError:
                self.counts["manifest_parse_failures"] += 1
                continue
            package = root.attrib.get("package", "")
            for element in root.iter():
                tag = element.tag.rsplit("}", 1)[-1]
                if tag not in {"activity", "service", "receiver", "provider"}:
                    continue
                raw_name = element.attrib.get(ANDROID_NS + "name", "")
                if raw_name.startswith("."):
                    fqn = package + raw_name
                elif raw_name and "." not in raw_name:
                    fqn = f"{package}.{raw_name}"
                else:
                    fqn = raw_name
                entity_id = f"android:{tag}:{fqn}"
                self._entity(entity_id, f"android_{tag}", raw_name, module, path,
                             metadata={"fqn": fqn, "exported": element.attrib.get(ANDROID_NS + "exported")})
                self._relation(module_id, entity_id, "REGISTERS_COMPONENT", path, evidence_kind="DECLARED")
                target = next((item for item in self.types_by_name.get(fqn.rsplit(".", 1)[-1], [])
                               if item.endswith(fqn)), None)
                self._relation(entity_id, target, "IMPLEMENTED_BY", path, fqn, "DECLARED",
                               "RESOLVED" if target else "UNRESOLVED")

    def _proguard(self, paths: list[str]) -> None:
        for path in paths:
            if not path.endswith((".pro", "proguard-rules.pro", "consumer-rules.pro")):
                continue
            text = self.source.text(path)
            module, _ = self._module(path)
            for line_number, raw_line in enumerate(text.splitlines(), 1):
                line = raw_line.strip()
                if not line.startswith("-keep"):
                    continue
                entity_id = f"proguard:{stable_id(path, str(line_number), line)}"
                self._entity(entity_id, "proguard_rule", line.split()[0], module, path,
                             line_number, {"rule": line})
                match = re.search(r"\b(?:class|interface|enum)\s+([\w.$]+)", line)
                if match:
                    fqn = match.group(1).replace("$**", "")
                    target = next((item for item in self.types_by_name.get(fqn.rsplit(".", 1)[-1], [])
                                   if item.endswith(fqn)), None)
                    self._relation(entity_id, target, "PROTECTS", path, fqn, "DECLARED",
                                   "RESOLVED" if target else "UNRESOLVED")
