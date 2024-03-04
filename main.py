import asyncio
import os

from dotenv import load_dotenv  # type: ignore

from solana.rpc.async_api import AsyncClient
from anchorpy import Wallet

from driftpy.drift_client import DriftClient
from driftpy.keypair import load_keypair
from driftpy.account_subscription_config import AccountSubscriptionConfig
from driftpy.types import TxParams
from driftpy.user_map.user_map_config import UserMapConfig, WebsocketConfig
from driftpy.user_map.user_map import UserMap
from keepyr_types import LiquidatorConfig, PerpFillerConfig
from perp_filler.src.perp_filler import PerpFiller
from liquidator.src.liquidator import Liquidator

from spl.token.async_client import AsyncToken
from spl.token.constants import TOKEN_PROGRAM_ID
from solana.rpc.core import RPCException


async def main():
    load_dotenv()
    secret = os.getenv("PRIVATE_KEY")
    url = os.getenv("RPC_URL")

    kp = load_keypair(secret)
    wallet = Wallet(kp)

    connection = AsyncClient(url)

    drift_client = DriftClient(
        connection,
        wallet,
        "mainnet",
        account_subscription=AccountSubscriptionConfig("websocket"),
        tx_params=TxParams(1_400_000, 100_000_000),  # crank priority fees way up
    )

    await drift_client.subscribe()

    await connection.request_airdrop(kp.pubkey(), int(10_000 * 1e9))
    print("airdrop received")
    await asyncio.sleep(10)

    token = AsyncToken(connection, kp.pubkey(), TOKEN_PROGRAM_ID, kp)

    while True:
        try:
            ata = await token.create_wrapped_native_account(
                connection, TOKEN_PROGRAM_ID, kp.pubkey(), kp, int(6_000 * 1e9)
            )
            print(str(ata))
            break
        except RPCException:
            print("retrying")
            await asyncio.sleep(5)

    try:
        await drift_client.initialize_user()
        print("user initialized")
    except RPCException:
        print("user already initialized")

    await drift_client.add_user(0)
    print("user added")

    await asyncio.sleep(20)

    while True:
        try:
            num = drift_client.convert_to_spot_precision(5_000, 1)
            await drift_client.deposit(num, 1, ata)
            print("deposited")
            break
        except AttributeError:
            print("retrying")
            await asyncio.sleep(5)

    await asyncio.sleep(30)
    usermap_config = UserMapConfig(drift_client, WebsocketConfig())
    usermap = UserMap(usermap_config)

    await usermap.sync()

    perp_filler_config = PerpFillerConfig(
        "perp filler",
        revert_on_failure=True,
    )

    perp_filler = PerpFiller(perp_filler_config, drift_client, usermap)

    spot = {
        0: 0,
        1: 0,
        2: 0,
        3: 0,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        10: 0,
        11: 0,
    }

    perp = {
        0: 0,
        1: 0,
        2: 0,
        3: 0,
        4: 0,
        5: 0,
        6: 0,
        7: 0,
        8: 0,
        9: 0,
        10: 0,
        11: 0,
        12: 0,
        13: 0,
        14: 0,
        15: 0,
        16: 0,
        17: 0,
        18: 0,
        19: 0,
        20: 0,
        21: 0,
        22: 0,
        23: 0,
        24: 0,
    }

    liquidator_config = LiquidatorConfig(
        "liquidator",
        drift_client,
        usermap,
        [
            0,
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            12,
            13,
            14,
            15,
            16,
            17,
            18,
            19,
            20,
            21,
            22,
            23,
            24,
        ],
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
        0,
        [0],
        perp,
        spot,
    )

    liquidator = Liquidator(liquidator_config)

    await liquidator.init()

    await perp_filler.init()

    for i in range(5):
        print(f"attempting to fill & liquidate: {i}")
        await perp_filler.try_fill()
        await asyncio.sleep(10)
        await liquidator.try_resolve_bankruptcies()
        await asyncio.sleep(10)
        await usermap.sync()

    flag_file = os.path.expanduser("~/file.txt")

    # with open(flag_file, "w") as f:
    #     f.write("done")

    print("keepyrs done")


if __name__ == "__main__":
    asyncio.run(main())
