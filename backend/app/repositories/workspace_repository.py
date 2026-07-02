import os
import stat
from datetime import datetime, timezone
from pathlib import Path

from app.schemas.workspace import (
    FileMetadataResponse,
    FolderEntry,
    SearchResult,
    TreeEntry,
)


class WorkspaceRepository:
    def __init__(self, workspace_path: Path):
        self.workspace = workspace_path.resolve()

    def _resolve_path(self, relative_path: str) -> Path:
        if not relative_path or relative_path == "":
            return self.workspace

        sep = relative_path.replace("\\", "/")
        cleaned = os.path.normpath(sep)

        if cleaned.startswith("..") or cleaned.startswith("/"):
            raise PermissionError(f"Invalid path: {relative_path}")

        resolved = (self.workspace / cleaned).resolve()
        if not str(resolved).startswith(str(self.workspace)):
            raise PermissionError(f"Path traversal detected: {relative_path}")

        return resolved

    def get_tree(self) -> TreeEntry:
        return self._build_tree(self.workspace)

    def _build_tree(self, directory: Path) -> TreeEntry:
        name = "" if directory == self.workspace else directory.name
        rel_path = (
            ""
            if directory == self.workspace
            else str(directory.relative_to(self.workspace))
        )
        entry = TreeEntry(name=name, path=rel_path, type="directory", children=[])

        try:
            items = sorted(
                directory.iterdir(),
                key=lambda x: (not x.is_dir(), x.name.lower()),
            )
        except PermissionError:
            entry.children = []
            return entry

        for item in items:
            if item.name.startswith("."):
                continue

            item_rel = str(item.relative_to(self.workspace))
            if item.is_dir():
                child = self._build_tree(item)
                entry.children.append(child)
            else:
                entry.children.append(
                    TreeEntry(
                        name=item.name,
                        path=item_rel,
                        type="file",
                        children=None,
                    )
                )

        return entry

    def list_folder(self, relative_path: str) -> list[FolderEntry]:
        target = self._resolve_path(relative_path)

        if not target.exists():
            raise FileNotFoundError(f"Path not found: {relative_path}")

        if not target.is_dir():
            raise NotADirectoryError(f"Not a directory: {relative_path}")

        entries: list[FolderEntry] = []
        try:
            items = sorted(
                target.iterdir(),
                key=lambda x: (not x.is_dir(), x.name.lower()),
            )
        except PermissionError:
            return entries

        for item in items:
            if item.name.startswith("."):
                continue

            item_rel = str(item.relative_to(self.workspace))
            st = item.stat()
            entry = FolderEntry(
                name=item.name,
                path=item_rel,
                type="directory" if item.is_dir() else "file",
                size=st.st_size if item.is_file() else None,
                extension=item.suffix.lower() if item.is_file() else None,
                modified_at=datetime.fromtimestamp(st.st_mtime, tz=timezone.utc),
            )
            entries.append(entry)

        return entries

    def get_metadata(self, relative_path: str) -> FileMetadataResponse:
        target = self._resolve_path(relative_path)

        if not target.exists():
            raise FileNotFoundError(f"Path not found: {relative_path}")

        st = target.stat()
        return FileMetadataResponse(
            name=target.name,
            path=str(target.relative_to(self.workspace)),
            extension=target.suffix.lower() if target.is_file() else "",
            size=st.st_size,
            created_at=datetime.fromtimestamp(
                st.st_birthtime if hasattr(st, "st_birthtime") else st.st_ctime,
                tz=timezone.utc,
            ),
            modified_at=datetime.fromtimestamp(st.st_mtime, tz=timezone.utc),
            is_directory=target.is_dir(),
            relative_path=str(target.relative_to(self.workspace)),
        )

    def search(self, query: str) -> list[SearchResult]:
        results: list[SearchResult] = []
        query_lower = query.lower()

        for root, dirs, files in os.walk(self.workspace):
            rel_root = os.path.relpath(root, self.workspace)
            if rel_root == ".":
                rel_root = ""

            dirs[:] = [d for d in dirs if not d.startswith(".")]

            for dir_name in dirs:
                if query_lower in dir_name.lower():
                    dir_rel = (
                        os.path.join(rel_root, dir_name) if rel_root else dir_name
                    )
                    results.append(
                        SearchResult(
                            name=dir_name,
                            path=dir_rel,
                            type="directory",
                        )
                    )

            for file_name in files:
                if file_name.startswith("."):
                    continue
                if query_lower in file_name.lower():
                    file_rel = (
                        os.path.join(rel_root, file_name) if rel_root else file_name
                    )
                    results.append(
                        SearchResult(
                            name=file_name,
                            path=file_rel,
                            type="file",
                        )
                    )

        results.sort(key=lambda r: (r.type, r.name.lower()))
        return results
