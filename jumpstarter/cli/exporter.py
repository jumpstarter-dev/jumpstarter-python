from pathlib import Path

import anyio
import click

from jumpstarter.config.exporter import ExporterConfigV1Alpha1

from .util import make_table


@click.group()
def exporter():
    """Manage and run exporters"""
    pass


@exporter.command
@click.argument("alias", default="default")
def create(alias):
    """Create exporter"""
    try:
        ExporterConfigV1Alpha1.load(alias)
    except FileNotFoundError:
        pass
    else:
        raise click.ClickException(f'exporter "{alias}" exists')

    endpoint = click.prompt("controller endpoint")
    token = click.prompt("token")
    config = ExporterConfigV1Alpha1(
        alias=alias,
        endpoint=endpoint,
        token=token,
    )
    config.save()


@exporter.command
@click.argument("alias", default="default")
def delete(alias):
    """Delete exporter"""
    try:
        config = ExporterConfigV1Alpha1.load(alias)
    except FileNotFoundError as err:
        raise click.ClickException(f'exporter "{alias}" does not exist') from err
    config.delete()


@exporter.command
@click.argument("alias", default="default")
def edit(alias):
    """Edit exporter"""
    try:
        config = ExporterConfigV1Alpha1.load(alias)
    except FileNotFoundError as err:
        raise click.ClickException(f'exporter "{alias}" does not exist') from err
    click.edit(filename=config.path)


@exporter.command
def list():
    exporters = ExporterConfigV1Alpha1.list()
    columns = ["ALIAS", "PATH"]
    rows = [
        {
            "ALIAS": exporter.alias,
            "PATH": str(exporter.path),
        }
        for exporter in exporters
    ]
    click.echo(make_table(columns, rows))


@exporter.command
@click.argument("alias", default="default")
@click.option("-c", "--config", "config_path")
def run(alias, config_path):
    """Run exporter"""
    try:
        if config_path:
            config = ExporterConfigV1Alpha1.load_path(Path(config_path))
        else:
            config = ExporterConfigV1Alpha1.load(alias)
    except FileNotFoundError as err:
        raise click.ClickException(f'exporter "{alias}" does not exist') from err

    anyio.run(config.serve)
