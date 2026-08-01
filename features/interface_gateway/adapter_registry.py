from __future__ import annotations

from typing import Any, Optional


class AdapterRegistry:

    def __init__(self):
        self._adapters: dict[str, Any] = {}

    def register(self, interface: str, adapter: Any) -> None:
        self._adapters[interface] = adapter

    def get(self, interface: str) -> Optional[Any]:
        return self._adapters.get(interface)

    def list_interfaces(self) -> list[str]:
        return list(self._adapters.keys())

    def has_interface(self, interface: str) -> bool:
        return interface in self._adapters

    def unregister(self, interface: str) -> bool:
        if interface in self._adapters:
            del self._adapters[interface]
            return True
        return False

    def clear(self) -> None:
        self._adapters.clear()
