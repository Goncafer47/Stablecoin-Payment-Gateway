# -*- coding: utf-8 -*-
"""Configuration loader for Stablecoin Payment Gateway — JSON config + defaults."""

import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"

_DEFAULTS = {'merchant': {'name': 'Demo Store',
                  'pay_to_address': '0xYourWalletAddress',
                  'xpub': '',
                  'callback_url': 'https://merchant.example.com/hooks/invoices'},
     'invoice': {'ttl_minutes': 30,
                 'underpayment_tolerance_pct': 0.5,
                 'overpayment_action': 'credit',
                 'confirmations': {'ethereum': 12,
                                   'base': 12,
                                   'bsc': 15,
                                   'polygon': 64,
                                   'arbitrum': 12,
                                   'tron': 19,
                                   'solana': 32,
                                   'ton': 12}},
     'chains': {'base': {'enabled': True, 'rpc': 'https://mainnet.base.org'},
                'ethereum': {'enabled': True, 'rpc': 'https://eth.llamarpc.com'},
                'bsc': {'enabled': True, 'rpc': 'https://bsc-dataseed.binance.org'},
                'polygon': {'enabled': True, 'rpc': 'https://polygon-rpc.com'},
                'arbitrum': {'enabled': True, 'rpc': 'https://arb1.arbitrum.io/rpc'},
                'tron': {'enabled': True, 'rpc': 'https://api.trongrid.io'},
                'solana': {'enabled': False, 'rpc': 'https://api.mainnet-beta.solana.com'},
                'ton': {'enabled': False, 'rpc': 'https://toncenter.com/api/v2'}},
     'tokens': {'USDC': {'enabled': True, 'decimals': 6},
                'USDT': {'enabled': True, 'decimals': 6},
                'PYUSD': {'enabled': False, 'decimals': 6},
                'DAI': {'enabled': False, 'decimals': 18}},
     'x402': {'enabled': True,
              'facilitator_url': 'https://x402.org/facilitator',
              'scheme': 'exact',
              'paywall_routes': ['/api/premium', '/api/download']},
     'webhooks': {'enabled': True,
                  'secret': '',
                  'retry_backoff_sec': [5, 30, 120],
                  'signing_header': 'X-Signature-256'},
     'server': {'host': '0.0.0.0', 'port': 8080, 'workers': 2},
     'export': {'default_format': 'csv', 'output_directory': './exports'}}


def load_config() -> dict:
    """Load configuration from config.json, merging with defaults."""
    cfg = dict(_DEFAULTS)
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
            _deep_merge(cfg, user_cfg)
        except (json.JSONDecodeError, OSError):
            pass
    return cfg


def _deep_merge(base: dict, override: dict):
    """Recursively merge override into base dict."""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


def save_config(cfg: dict):
    """Persist configuration to config.json."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
