import orekit
from org.orekit.utils import Constants
from orekit.pyhelpers import setup_orekit_curdir

"""
Downloads necessary data and constants needed for Orekit
"""


vm = orekit.initVM()
orekit.pyhelpers.download_orekit_data_curdir()
