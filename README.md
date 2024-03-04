# Drift Protocol v2 Python Keeper Bots

## Set up

1) Run `poetry shell`
2) Run `poetry install`
3) Create `.env` file in `keepyrs` with wallet `PRIVATE_KEY` and your `RPC_URL`

## JIT MAKER

`poetry run python -m jit_maker.src.jit_maker`

You CANNOT make multiple markets with the same sub account on the JIT Maker.  This code does not account for overleveraging as a result of having positions open across several markets on the same sub account id. 

To adjust your account's target leverage, change the TARGET_LEVERAGE_PER_ACCOUNT constant at `jit_maker.py:47`.  The JIT maker will open positions up to this leverage, and once reached, will only open positions that reduce the account's leverage (i.e. if you are max levered long, it'll only open shorts until you're no longer max levered long)


## PERP FILLER

`poetry run python -m perp_filler.src.perp_filler`

WIP


## SIMS

1. `poetry shell`
2. `poetry install`
3. Create `.env` file in `keepyrs` with wallet `PRIVATE_KEY` and `RPC_URL=http://127.0.0.1:8899`
4. `poetry run python main.py`
5. if you get errors before the bot loops start just `control-c` and re-run the script

it seems like for some reason you have to run the script twice for collateral to be recognized by the liquidator

i tried sleeping i don't know what it is