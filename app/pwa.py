from __future__ import annotations

import streamlit as st

MANIFEST_CANDIDATES = [
    "/app/static/manifest.json",
    "/app/static/manifest.webmanifest",
    "/static/manifest.json",
    "/manifest.json",
    "./app/static/manifest.json",
]
SW_CANDIDATES = [
    "/app/static/service-worker.js",
    "/static/service-worker.js",
    "/service-worker.js",
    "./app/static/service-worker.js",
]
ICON_192_CANDIDATES = [
    "/app/static/icons/icon-192.png",
    "/static/icons/icon-192.png",
]
ICON_512_CANDIDATES = [
    "/app/static/icons/icon-512.png",
    "/static/icons/icon-512.png",
]


def enable_pwa(*args, **kwargs):
    return
