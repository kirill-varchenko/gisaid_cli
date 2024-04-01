import asyncio
import json
import logging
from datetime import date
from pathlib import Path

import aiofiles
import aiohttp

from gisaid_cli.enums import Database
from gisaid_cli.gisaid import GisaidClient, GisaidSession
from gisaid_cli.models import AuthToken, Submission

logger = logging.getLogger("gisaid_cli")


async def authenticate(
    client_id: str, username: str, password: str, database: Database
) -> AuthToken:
    """Authenticate and get token."""
    async with aiohttp.ClientSession() as session:
        gisaid_client = GisaidClient(session)
        return await gisaid_client.request_auth_token(
            database=database, client_id=client_id, username=username, password=password
        )


async def results_logger(log_path: Path, queue: asyncio.Queue) -> None:
    async with aiofiles.open(log_path, mode="a") as fo:
        while True:
            result = await queue.get()
            jsoned = json.dumps(result)
            await fo.write(jsoned + "\n")
            queue.task_done()


async def submission_worker(
    auth_token: AuthToken, in_queue: asyncio.Queue, out_queue: asyncio.Queue
) -> None:
    """Submit items from queue."""
    today = str(date.today())

    async with aiohttp.ClientSession() as session:
        gisaid_client = GisaidClient(session)
        async with GisaidSession(auth_token, gisaid_client) as gisaid_session:
            while True:
                submission: Submission = await in_queue.get()
                try:
                    result = await gisaid_session.submit(submission)
                    result["covv_virus_name"] = submission.covv_virus_name
                    result["submission_date"] = today
                    await out_queue.put(result)
                except Exception as exc:
                    logger.error(
                        "Error with submittion %s: %s",
                        submission.covv_virus_name,
                        str(exc),
                    )
                    await in_queue.put(submission)
                in_queue.task_done()


async def submit(
    submissions: list[Submission],
    auth_token: AuthToken,
    workers_number: int,
    log_path: Path,
) -> None:
    submissions_queue = asyncio.Queue()
    results_queue = asyncio.Queue()

    for submission in submissions:
        await submissions_queue.put(submission)

    workers = [
        asyncio.create_task(
            submission_worker(
                auth_token=auth_token,
                in_queue=submissions_queue,
                out_queue=results_queue,
            )
        )
        for _ in range(workers_number)
    ]
    workers.append(
        asyncio.create_task(results_logger(log_path=log_path, queue=results_queue))
    )

    await submissions_queue.join()
    await results_queue.join()

    for worker in workers:
        worker.cancel()
