import os
from dotenv import load_dotenv
from solders.pubkey import Pubkey

# Load environment variables
load_dotenv()

# RPC Connection Endpoints
RPC_URL = os.getenv('RPC_URL', 'https://api.mainnet-beta.solana.com')
WS_RPC_URL = os.getenv('WS_RPC_URL', 'wss://api.mainnet-beta.solana.com')

# Lamports per SOL
LAMPORTS_PER_SOL = 1000000000

# Gas settings (Micro-lamports)
GAS_PRICE = 1000000
# Compute Unit Limit
GAS_LIMIT = 2000000

# Early buy threshold configuration
EARLY_BUY = 10

# Raydium AMM Authority V4
RAY_AUTHORITY_V4 = Pubkey.from_string("5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1")

# OpenBook Program ID
SERUM_PROGRAM_ID = Pubkey.from_string('srmqPvymJeFKQ4zGQed1GFppgkRHL9kaELCbyksJtPX')

# Raydium Liquidity Pool V4 Program ID
RAY_V4 = Pubkey.from_string("675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8")
