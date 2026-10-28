#!/bin/bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/python3 app.py
