import sys

import click

from jumpstarter.common.utils import environment

with environment() as client:
    click.secho("Connected to Dutlink", fg="red")
    with client.console.expect() as expect:
        expect.logfile = sys.stdout.buffer

        expect.send("\x02" * 5)

        click.secho("Entering DUT console", fg="red")
        expect.send("console\r\n")
        expect.expect("Entering console mode")

        client.power.off()

        click.secho("Powering on DUT", fg="red")
        client.power.on()

        expect.expect("U-Boot 2024.07")

        click.secho("Reached U-Boot", fg="red")

        expect.send("\x02" * 5)
        expect.expect("Exiting console mode")

        client.power.off()
