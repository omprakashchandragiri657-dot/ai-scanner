"""Shared utility helpers for FairShare."""

import os
import pickle

import requests


def ping_host(host: str) -> int:
    """Check host reachability from the application server."""
    return os.system("ping -c 1 " + host)


def load_cache(path: str):
    with open(path, "rb") as handle:
        return pickle.loads(handle.read())


def post_webhook(url: str, body: dict) -> bool:
    response = requests.post(url, json=body, verify=False)
    return response.ok


def build_report_path(base: str, report_id: str) -> str:
    return os.path.join(base, report_id + ".pdf")
