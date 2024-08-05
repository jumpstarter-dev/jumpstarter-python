import sys
from threading import Thread

import click

from jumpstarter.common import MetadataFilter
from jumpstarter.common.utils import lease


def monitor_power(client):
    try:
        for reading in client.power.read():
            click.secho(f"{reading}", fg="green")
    except Exception:
        pass


with lease(MetadataFilter(name="dutlink")) as client:
    click.secho("Connected to Dutlink", fg="red")
    Thread(target=monitor_power, args=[client]).start()
    with client.console.expect() as expect:
        expect.logfile = sys.stdout.buffer

        client.power.off()

        click.secho("Writing system image", fg="red")
        client.storage.write_local_file("/home/nickcao/Downloads/sdcard.img")
        click.secho("Written system image", fg="red")

        client.storage.dut()

        click.secho("Powering on DUT", fg="red")
        client.power.on()

        expect.expect("StarFive #")
        click.secho("Working around u-boot usb initialization issue", fg="red")
        expect.sendline("usb reset")

        expect.expect("StarFive #")
        expect.sendline("boot")

        expect.expect("Enter choice:")
        click.secho("Selecting boot entry", fg="red")
        expect.sendline("1")

        expect.expect("NixOS Stage 1")

        click.secho("Reached initrd", fg="red")

        client.power.off()
