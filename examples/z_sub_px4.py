#
# Copyright (c) 2022 ZettaScale Technology
#
# This program and the accompanying materials are made available under the
# terms of the Eclipse Public License 2.0 which is available at
# http://www.eclipse.org/legal/epl-2.0, or the Apache License, Version 2.0
# which is available at https://www.apache.org/licenses/LICENSE-2.0.
#
# SPDX-License-Identifier: EPL-2.0 OR Apache-2.0
#
# Contributors:
#   ZettaScale Zenoh Team, <zenoh@zettascale.tech>
#

import argparse
import json
import time

import zenoh

try:
    from px4.msg import VehicleStatus, SensorCombined
except Exception:
    print("""You need to generate the idlc messages SensorCombined and VehicleStatus.
This can be generated using your build from PX4.
export PX4_BUILD_LOCATION=~/work/PX4-Autopilot/build/px4_fmu-v6x_zenoh

$PX4_BUILD_LOCATION/msg/idlc/bin/idlc -l py $PX4_BUILD_LOCATION/uORB/idl/px4/msg/SensorCombined.idl
$PX4_BUILD_LOCATION/msg/idlc/bin/idlc -l py $PX4_BUILD_LOCATION/uORB/idl/px4/msg/VehicleStatus.idl""")

    exit(1)
# --- Command line argument parsing --- --- --- --- --- ---
parser = argparse.ArgumentParser(prog="z_sub", description="zenoh sub example")
parser.add_argument(
    "--mode",
    "-m",
    dest="mode",
    choices=["peer", "client"],
    type=str,
    help="The zenoh session mode.",
)
parser.add_argument(
    "--connect",
    "-e",
    dest="connect",
    metavar="ENDPOINT",
    action="append",
    type=str,
    help="Endpoints to connect to.",
)
parser.add_argument(
    "--listen",
    "-l",
    dest="listen",
    metavar="ENDPOINT",
    action="append",
    type=str,
    help="Endpoints to listen on.",
)
parser.add_argument(
    "--key",
    "-k",
    dest="key",
    default="rc/vehicle_status",
    type=str,
    help="The key expression to subscribe to.",
)
parser.add_argument(
    "--config",
    "-c",
    dest="config",
    metavar="FILE",
    type=str,
    help="A configuration file.",
)

args = parser.parse_args()
conf = (
    zenoh.Config.from_file(args.config) if args.config is not None else zenoh.Config()
)
if args.mode is not None:
    conf.insert_json5("mode", json.dumps(args.mode))
if args.connect is not None:
    conf.insert_json5("connect/endpoints", json.dumps(args.connect))
if args.listen is not None:
    conf.insert_json5("listen/endpoints", json.dumps(args.listen))
key = args.key


# Zenoh code  --- --- --- --- --- --- --- --- --- --- ---
def main():
    # initiate logging
    zenoh.try_init_log_from_env()

    print("Opening session...")
    with zenoh.open(conf) as session:

        print("Declaring Subscriber on '{}'...".format(key))

        def listener(sample: zenoh.Sample):
            print(sample.key_expr)
            print(
                f">> [Subscriber] Received {sample.kind} ('{sample.key_expr}': '{sample.payload}')"
            )
            if sample.key_expr.__str__().endswith("vehicle_status"):
                data = VehicleStatus.deserialize(sample.payload.__bytes__())
            else:
                data = SensorCombined.deserialize(sample.payload.__bytes__())
            print(data)

        session.declare_subscriber(
            key, listener, reliability=zenoh.Reliability.RELIABLE
        )

        print("Press CTRL-C to quit...")
        while True:
            time.sleep(1)


if __name__ == "__main__":
    main()
