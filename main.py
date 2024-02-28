import asyncio
import os
import subprocess

from dotenv import load_dotenv  # type: ignore

from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair  # type: ignore
from anchorpy import Wallet, Provider

from driftpy.drift_client import DriftClient
from driftpy.keypair import load_keypair
from driftpy.account_subscription_config import AccountSubscriptionConfig
from driftpy.types import TxParams
from driftpy.constants.numeric_constants import QUOTE_PRECISION
from driftpy.user_map.user_map_config import UserMapConfig, WebsocketConfig
from driftpy.user_map.user_map import UserMap
from perp_filler.src.perp_filler import PerpFiller
from liquidator.src.liquidator import Liquidator

from keepyr_types import PerpFillerConfig, LiquidatorConfig
from driftpy.setup.helpers import _create_and_mint_user_usdc, _create_mint, _create_wsol


async def main():
    load_dotenv()
    secret = os.getenv("PRIVATE_KEY")
    url = os.getenv("RPC_URL")

    kp = load_keypair(secret)
    wallet = Wallet(kp)

    connection = AsyncClient(url)

    provider = Provider(connection, wallet)

    drift_client = DriftClient(
        connection,
        wallet,
        "mainnet",
        account_subscription=AccountSubscriptionConfig("websocket"),
        tx_params=TxParams(1_400_000, 20_000),  # crank priority fees way up
    )

    await drift_client.subscribe()

    sig = await connection.request_airdrop(kp.pubkey(), int(10_000 * 1e9))
    print("airdrop received")
    await asyncio.sleep(3)

    # command = ["solana", "confirm", f"{str(sig.value)}"] # do it manually because confirm transaction lies
    # output = subprocess.run(command, capture_output=True, text=True).stdout.strip()
    # if "Confirmed" in output or "Processed" in output or "Finalized" in output:
    #     print(f"confirmed airdrop tx: {sig}")
    # else:
    #     raise Exception("failed to confirm airdrop tx")

    # usdc_mint = await _create_mint(provider)

    # print("usdc mint created")

    # USDC_AMOUNT = 10_000 * QUOTE_PRECISION
    # usdc_acc = await _create_and_mint_user_usdc(usdc_mint, provider, USDC_AMOUNT, provider.wallet.public_key)
    # print("ata created and minted USDC")
    # await drift_client.initialize_user()
    # print("user initialized")

    await drift_client.add_user(0)
    print("user added")
    # await asyncio.sleep(10)
    # await drift_client.get_user(0).account_subscriber.update_cache()
    # print("cache updated")
    # wsol = Keypair()
    # tx = await _create_wsol(wsol, provider, wallet.public_key)
    # tx.recent_blockhash = (
    #     await provider.connection.get_latest_blockhash()
    # ).value.blockhash
    # tx.sign_partial(wsol)
    # provider.wallet.sign_transaction(tx)
    # await provider.send(tx)

    # num = drift_client.convert_to_spot_precision(10_000, 1)
    # await drift_client.deposit(num, 1, wsol.pubkey())
    # print("deposited")

    # sig = await drift_client.initialize_user()
    # print(sig)
    # command = ["solana", "confirm", f"{str(sig)}"] # do it manually because confirm transaction lies
    # output = subprocess.run(command, capture_output=True, text=True).stdout.strip()
    # if "Confirmed" in output or "Processed" in output or "Finalized" in output:
    #     print(f"confirmed init user tx: {sig}")
    # else:
    #     raise Exception("failed to confirm init user tx")

    # raise Exception

    await asyncio.sleep(30)
    usermap_config = UserMapConfig(drift_client, WebsocketConfig())
    usermap = UserMap(usermap_config)

    await usermap.sync()

    perp_filler_config = PerpFillerConfig(
        "perp filler",
        revert_on_failure=True,
    )

    perp_filler = PerpFiller(perp_filler_config, drift_client, usermap)

    liquidator_config = LiquidatorConfig(
        "liquidator",
        drift_client,
        usermap,
        [0],
        [0],
        0,
        [0],
        {9: 0},
        {0: 0},
    )

    liquidator = Liquidator(liquidator_config)

    await liquidator.init()

    await perp_filler.init()

    for i in range(5):
        print(f"attempting to fill & liquidate: {i}")
        await perp_filler.try_fill()
        await asyncio.sleep(10)
        await liquidator.try_liquidate()
        await asyncio.sleep(10)
        await usermap.sync()

    flag_file = os.path.expanduser("~/file.txt")

    with open(flag_file, "w") as f:
        f.write("done")

    print("keepyrs done")


if __name__ == "__main__":
    asyncio.run(main())
