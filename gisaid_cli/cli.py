import asyncio
import time
from datetime import timedelta
from pathlib import Path

import click

from gisaid_cli import jobs
from gisaid_cli.enums import Database, FrameshiftsConfirmation
from gisaid_cli.io_utils import load_metadata, load_sequences
from gisaid_cli.models import AuthToken
from gisaid_cli.submissions import generate_submissions


@click.group()
def cli():
    pass


@cli.command()
@click.argument("token_path")
@click.option("--client_id", "-c", prompt=True)
@click.option("--username", "-u", prompt=True)
@click.option("--password", "-p", prompt=True, hide_input=True)
@click.option("--database", "-d", type=click.Choice(list(Database)))
def authenticate(
    token_path: str, client_id: str, username: str, password: str, database: Database
) -> None:
    """Authenticate and write a token."""
    token = asyncio.run(
        jobs.authenticate(
            database=database, client_id=client_id, username=username, password=password
        )
    )

    with open(token_path, "w") as fo:
        fo.write(token.model_dump_json(indent=2))


@cli.command()
@click.option(
    "--token",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option(
    "--metadata",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option(
    "--fasta",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option(
    "--frameshift",
    type=click.Choice(choices=list([fc.name for fc in FrameshiftsConfirmation])),
    default=FrameshiftsConfirmation.CATCH_ALL.name,
    show_default=True,
)
@click.option(
    "--log",
    type=click.Path(dir_okay=False, path_type=Path),
)
@click.option(
    "--workers",
    type=int,
    default=10,
    show_default=True,
)
def upload(
    token: Path,
    metadata: Path,
    fasta: Path,
    frameshift: str,
    log: Path | None,
    workers: int,
):
    """Upload metadata and fasta."""
    with open(token, "r") as fi:
        auth_token = AuthToken.model_validate_json(fi.read())
    meta = load_metadata(metadata)
    sequences = load_sequences(fasta)
    submissions = generate_submissions(
        metadata=meta,
        sequences=sequences,
        frameshifts_confirmation=FrameshiftsConfirmation[frameshift],
    )
    if log is None:
        log = metadata.with_suffix(".jsonl")

    click.echo(f"Submissions: {len(submissions)}")
    click.echo(f"Log: {log.absolute()}")
    t1 = time.perf_counter()
    asyncio.run(
        jobs.submit(
            submissions=submissions,
            auth_token=auth_token,
            workers_number=workers,
            log_path=log,
        )
    )
    t2 = time.perf_counter()
    duration = timedelta(seconds=t2 - t1)
    click.echo(f"Done in: {duration}")


if __name__ == "__main__":
    cli()
