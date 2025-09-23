from __future__ import annotations
from typing import Dict, Optional
from discord import SyncWebhook


def build_webhooks(env_map: Dict[str, str]) -> Dict[str, SyncWebhook]:
    hooks: Dict[str, SyncWebhook] = {}
    for key, url in env_map.items():
        try:
            hooks[key] = SyncWebhook.from_url(url)
        except Exception:
            pass
    return hooks


def get_hook(hooks: Dict[str, SyncWebhook], *keys: str) -> Optional[SyncWebhook]:
    for k in keys:
        if k in hooks:
            return hooks[k]
    return None
