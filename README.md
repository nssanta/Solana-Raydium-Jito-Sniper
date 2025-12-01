# Solana Raydium Sniper Bot (V1)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Solana](https://img.shields.io/badge/Solana-Verified-green.svg)](https://solana.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A **high-performance**, **asynchronous** Python bot for sniping new liquidity pools on the Solana Raydium DEX.

[Русская версия](README.ru.md) | [English](README.md)

---

## 🎯 Key Features

This project demonstrates a production-ready architecture for real-time blockchain interaction:

✅ **Real-time Scanning** - Listens to Solana WebSocket logs (`logsSubscribe`) to detect `InitializeInstruction2` events on Raydium V4 instantly.  
✅ **Async Architecture** - Built entirely on `asyncio` and `solana-py` for non-blocking high-throughput performance.  
✅ **MEV Protection** - Integrated with **Jito Labs** block engine to send transactions as bundles, protecting against sandwich attacks.  
✅ **Direct RPC Interaction** - Uses `solders` and `solana.rpc` for low-level, efficient transaction construction and signing.  
✅ **Configurable Filters** - Automatically filters pools based on liquidity amount (SOL reserves) and launch time.

---

## 🛠️ Tech Stack

- **Language:** Python 3.11+
- **Blockchain Interaction:** `solana-py`, `solders`, `websockets`
- **MEV/Bundling:** Jito (Block Engine)
- **Concurrency:** `asyncio`

---

## 🚀 Quick Start

### Installation

1. **Clone the repository:**

```bash
git clone https://github.com/your-username/solana-sniper-v1.git
cd solana-sniper-v1
```

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

3. **Configuration:**

Copy the example environment file and add your RPC credentials and Private Key.

```bash
cp .env.example .env
```

> **Note:** Never commit your real `.env` file to version control.

### Usage

To run the main asynchronous sniper loop:

```bash
python main_async.py
```

---

## 🏗️ Architecture Overview

The project is structured for modularity and speed:

*   **`Scanner/`** - Handles WebSocket connections and parses program logs to find new pools.
*   **`SWAP/`** - Contains logic for building Swap instructions (Buy/Sell) on Raydium.
*   **`Jito/`** - Interface for sending transaction bundles to the Jito Block Engine.
*   **`Data/`** - Configuration and constant management.

---

## ⚠️ Disclaimer

This software is for educational purposes only. Cryptocurrency trading involves significant risk. The authors are not responsible for any financial losses incurred while using this bot.

---

*Refactored 2024*