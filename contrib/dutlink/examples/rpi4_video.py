#!/usr/bin/env python
import logging
import sys
import time

import click

from jumpstarter.client.adapters import PexpectAdapter

# initialize client from exporter config
from jumpstarter.common import MetadataFilter
from jumpstarter.common.utils import env
from jumpstarter.config.client import ClientConfigV1Alpha1


def on_rpi4(client):
    dutlink = client.dutlink
    video = client.video
    camera = client.camera
    with PexpectAdapter(client=dutlink.console) as console:
        # stream console output to stdout
        console.logfile = sys.stdout.buffer
        # ensure DUT is powered off
        dutlink.power.off()
        with open("camera_off.jpeg", "wb") as f:
            f.write(camera.snapshot())
        click.secho("Writing system image", fg="red")

        dutlink.storage.write_local_file("2024-07-04-raspios-bookworm-arm64-lite.img")

        dutlink.storage.dut()
        click.secho("Connected storage device to DUT", fg="green")

        dutlink.power.on()
        click.secho("Powered DUT on", fg="green")

        time.sleep(8)
        with open("camera_on.jpeg", "wb") as f:
            f.write(camera.snapshot())

        with open("test_booting.jpeg", "wb") as f:
          f.write(video.snapshot())

        dutlink.power.off()

        click.secho("Waiting for login...", fg="red")
        console.expect("login:", timeout=240)
        console.sendline("root")

        print(video.state())
        with open("test2.jpeg", "wb") as f:
          f.write(video.snapshot())


        click.secho("Waiting for password prompt", fg="red")
        console.expect("Password:")
        console.sendline("changeme")
        time.sleep(3)

        reading = next(dutlink.power.read())
        click.secho(f"Current power reading: {reading}", fg="blue")

        console.expect("@rpitest:~#", timeout=200)
        console.sendline("uname -a")
        console.expect("aarch64")

        console.expect("@rpitest:~#", timeout=200)
        console.sendline("apt-get install -y tpm2-tools")

        lines = ["tpm2_createprimary -C e -c primary.ctx",
                 "tpm2_create -G rsa -u key.pub -r key.priv -C primary.ctx",
                 "tpm2_load -C primary.ctx -u key.pub -r key.priv -c key.ctx",
                 "echo my message > message.dat",
                 "tpm2_sign -c key.ctx -g sha256 -o sig.rssa message.dat",
                 "tpm2_verifysignature -c key.ctx -g sha256 -s sig.rssa -m message.dat"]
        for line in lines:
            console.expect("@rpitest:~#", timeout=200)
            console.sendline(line)

        console.sendline("echo result: $?")
        console.expect("result: 0", timeout=200)

        console.expect("@rpitest:~#")
        console.sendline("poweroff")

        time.sleep(15)

        dutlink.power.off()


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
try:
    with env() as client:
        on_rpi4(client.dutlink)
except RuntimeError as e:
    if "JUMPSTARTER_HOST" not in str(e):
        raise e

    with ClientConfigV1Alpha1.load("default").lease(metadata_filter=MetadataFilter(labels={"board":"rpi4"})) as lease:
        with lease.connect() as client:
            click.secho("Connected to Dutlink", fg="green")
            on_rpi4(client)
