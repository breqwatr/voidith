""" Global voithos constants """

import os

# Major release of this CLI, for use with "voithos version"
VOITHOS_VERSION = "1.00"

# Enabling dev mode toggles some features for developers such as mounting arcus code to docker
DEV_MODE = "VOITHOS_DEV" in os.environ and os.environ["VOITHOS_DEV"].lower() == "true"
