import sys

import click

from jumpstarter.common.utils import environment

with environment() as client:
    click.secho("Connected to Dutlink", fg="red")
    with client.console.expect() as expect:
        expect.logfile = sys.stdout.buffer

        client.power.off()

        click.secho("Powering on DUT", fg="red")
        client.power.on()

        expect.expect("U-Boot 2024.07")

        click.secho("Reached U-Boot", fg="red")

        client.power.off()
