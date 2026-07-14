from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from typing import Callable

from reconciliation.snapshot.file_node import FileNode


@dataclass
class TreeNode:
    name: str
    path: str
    is_dir: bool
    children: dict[str, TreeNode] = field(default_factory=dict)
    file_node: FileNode | None = None


class DirectoryTree:
    def __init__(self) -> None:
        self.root = TreeNode(name=".", path="", is_dir=True)

    def add(self, node: FileNode) -> None:
        parts = node.directory.split("/") if node.directory else []
        current = self.root
        for part in parts:
            if part not in current.children:
                child_path = f"{current.path}/{part}" if current.path else part
                current.children[part] = TreeNode(
                    name=part,
                    path=child_path,
                    is_dir=True,
                )
            current = current.children[part]
        current.children[node.filename] = TreeNode(
            name=node.filename,
            path=node.rel_path,
            is_dir=False,
            file_node=node,
        )

    def lookup(self, path: str) -> TreeNode | None:
        parts = [p for p in path.split("/") if p]
        current: TreeNode | None = self.root
        for part in parts:
            if current is None:
                return None
            current = current.children.get(part)
        return current

    def traverse(self) -> list[TreeNode]:
        result: list[TreeNode] = []

        def _dfs(node: TreeNode) -> None:
            result.append(node)
            for child in node.children.values():
                _dfs(child)

        _dfs(self.root)
        return result

    def filter(self, predicate: Callable[[FileNode], bool]) -> list[FileNode]:
        result: list[FileNode] = []
        for node in self.traverse():
            if node.file_node is not None and predicate(node.file_node):
                result.append(node.file_node)
        return result

    def glob(self, pattern: str) -> list[FileNode]:
        result: list[FileNode] = []
        for node in self.traverse():
            if node.file_node is not None and fnmatch.fnmatch(
                node.file_node.rel_path, pattern
            ):
                result.append(node.file_node)
        return result
