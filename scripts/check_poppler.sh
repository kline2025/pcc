#!/usr/bin/env bash
set -e
pdftotext -v 2>&1 | head -n 1
