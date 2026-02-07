#!/usr/bin/env python3
"""
fetch-data.py — Downloads public USDA/FDA directories and converts them
to compact JSON for the 68R Source Awareness app.

Run this on your Mac:
    python3 fetch-data.py

It will create/update:
    data/mpi_directory.json   — FSIS Meat, Poultry & Egg Inspection Directory
    data/ims_shippers.json    — FDA Interstate Milk Shippers list

Requirements: Python 3 (pre-installed on macOS). No pip packages needed.
"""

import csv
import json
import os
import re
import sys
import urllib.request
from html.parser import HTMLParser

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

# ── FSIS MPI Directory ──────────────────────────────────────────────

MPI_CSV_URL = (
    'https://www.fsis.usda.gov/sites/default/files/media_file/documents/'
    'MPI_Directory_by_Establishment_Number.csv'
)

def fetch_mpi():
    print('Downloading FSIS MPI Directory CSV...')
    req = urllib.request.Request(MPI_CSV_URL, headers={'User-Agent': 'Mozilla/5.0'})
    print('  (This is a large file — may take a few minutes...)')
    with urllib.request.urlopen(req, timeout=300) as resp:
        raw = resp.read().decode('utf-8-sig')

    reader = csv.DictReader(raw.splitlines())
    entries = []
    for row in reader:
        # Normalize column names (they vary slightly between releases)
        r = {k.strip().lower().replace(' ', '_'): v.strip() for k, v in row.items() if k}
        entry = {
            'est': r.get('establishment_number', r.get('est_number', '')),
            'name': r.get('establishment_name', r.get('company', r.get('dba_name', ''))),
            'city': r.get('city', ''),
            'state': r.get('state', ''),
            'zip': r.get('zip', r.get('zip_code', '')),
            'activities': r.get('activities', r.get('grant_activities', '')),
        }
        if entry['est'] or entry['name']:
            entries.append(entry)

    print(f'  Parsed {len(entries)} establishments.')
    return entries


# ── FDA Interstate Milk Shippers ─────────────────────────────────────

IMS_BASE = 'https://hfpappexternal.fda.gov/scripts/ims/mkex/ims'
IMS_STATES_URL = f'{IMS_BASE}/imsss-ce.cfm'

# All US states + territories that may appear
STATE_CODES = [
    'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN',
    'IA','KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV',
    'NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN',
    'TX','UT','VT','VA','WA','WV','WI','WY','DC','PR','VI','GU','AS'
]


class IMSTableParser(HTMLParser):
    """Simple HTML table parser for IMS state pages."""

    def __init__(self):
        super().__init__()
        self.in_table = False
        self.in_row = False
        self.in_cell = False
        self.rows = []
        self.current_row = []
        self.current_cell = ''
        self.table_count = 0

    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            self.table_count += 1
            self.in_table = True
        elif tag == 'tr' and self.in_table:
            self.in_row = True
            self.current_row = []
        elif tag in ('td', 'th') and self.in_row:
            self.in_cell = True
            self.current_cell = ''

    def handle_endtag(self, tag):
        if tag == 'table':
            self.in_table = False
        elif tag == 'tr' and self.in_row:
            self.in_row = False
            if self.current_row:
                self.rows.append(self.current_row)
        elif tag in ('td', 'th') and self.in_cell:
            self.in_cell = False
            self.current_row.append(self.current_cell.strip())

    def handle_data(self, data):
        if self.in_cell:
            self.current_cell += data


def fetch_ims_state(state):
    """Fetch IMS shippers for a single state."""
    url = f'{IMS_BASE}/imssl-ce.cfm?state={state}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode('utf-8', errors='replace')
    except Exception as e:
        print(f'    Warning: Could not fetch {state}: {e}')
        return []

    parser = IMSTableParser()
    parser.feed(html)

    entries = []
    for row in parser.rows:
        # Skip header rows and rows that are too short
        if len(row) < 3:
            continue
        # Skip if first cell looks like a header
        first = row[0].lower()
        if 'name' in first or 'plant' in first or 'city' in first:
            continue

        entry = {
            'name': row[0] if len(row) > 0 else '',
            'plant_id': row[1] if len(row) > 1 else '',
            'products': row[2] if len(row) > 2 else '',
            'state': state,
        }
        if entry['name'] and entry['name'] != '\xa0':
            entries.append(entry)

    return entries


def fetch_ims():
    print('Downloading FDA Interstate Milk Shippers list...')
    all_entries = []
    total = len(STATE_CODES)
    for i, state in enumerate(STATE_CODES):
        sys.stdout.write(f'\r  Fetching {state} ({i+1}/{total})...')
        sys.stdout.flush()
        entries = fetch_ims_state(state)
        all_entries.extend(entries)

    print(f'\n  Parsed {len(all_entries)} shippers across all states.')
    return all_entries


# ── Main ─────────────────────────────────────────────────────────────

def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    # Fetch MPI
    try:
        mpi = fetch_mpi()
        mpi_path = os.path.join(DATA_DIR, 'mpi_directory.json')
        with open(mpi_path, 'w') as f:
            json.dump(mpi, f, separators=(',', ':'))
        size_mb = os.path.getsize(mpi_path) / (1024 * 1024)
        print(f'  Saved {mpi_path} ({size_mb:.1f} MB)')
    except Exception as e:
        print(f'  ERROR fetching MPI directory: {e}')
        print('  You can retry later. The app will work without this data.')

    # Fetch IMS
    try:
        ims = fetch_ims()
        ims_path = os.path.join(DATA_DIR, 'ims_shippers.json')
        with open(ims_path, 'w') as f:
            json.dump(ims, f, separators=(',', ':'))
        size_mb = os.path.getsize(ims_path) / (1024 * 1024)
        print(f'  Saved {ims_path} ({size_mb:.1f} MB)')
    except Exception as e:
        print(f'  ERROR fetching IMS list: {e}')
        print('  You can retry later. The app will work without this data.')

    print('\nDone! Now commit and push to update your app:')
    print('  git add data/')
    print('  git commit -m "Update reference data"')
    print('  git push')


if __name__ == '__main__':
    main()
