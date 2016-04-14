# STM32f2xx core implementation
#
# Author: Kevin Townsend, Markus Becker
import os

import click

from ..core import Core
from ..programmers import JLink, STLink


# DEVICE ID register valueto name mapping
DEVICEID_CHIPNAME_LOOKUP = {
    0x423: 'STM32F401xB/C',
    0x433: 'STM32F401xD/E'
}

# DEVICE ID register value to Segger '-device' name mapping
# Segger ID List: https://www.segger.com/jlink_supported_devices.html
DEVICEID_SEGGER_LOOKUP = {
    0x423: 'STM32F401xB/C', #TODO
    0x433: 'STM32F401RE',
}

# REV_D name mapping
# See Section 23.6.1 of the STM32F401 Reference Manual (DBGMDU_IDCODE)
DEVICEID_CHIPREV_LOOKUP = {
    0x1000: 'A (0x1000)',
    0x1001: 'Z (0x1001)',
}


class STLink_STM32F4(STLink):
    # STM32F4-specific STLink-based programmer.  Required to add custom mass
    # erase command logic to wiping.

    def __init__(self):
        # Call base STLink initializer and set it up to program the STM32F4.
        super(STLink_STM32F4, self).__init__(params='-f interface/stlink-v2.cfg -f target/stm32f4x.cfg')

    def wipe(self):
        # Run OpenOCD commands to wipe STM32F2 memory.
        commands = [
            'init',
            'reset init',
            'halt',
            'stm32f4x mass_erase 0',
            'exit'
        ]
        self.run_commands(commands)


class STM32F4(Core):
    """STMicro STM32F4 CPU."""
    # Note that the docstring will be used as the short help description.

    def __init__(self):
        # Call base class constructor.
        super(STM32F4, self).__init__()

    def list_programmers(self):
        """Return a list of the programmer names supported by this CPU."""
        return ['jlink','stlink']

    def create_programmer(self, programmer):
        """Create and return a programmer instance that will be used to program
        the core.  Must be implemented by subclasses!
        """
        if programmer == 'jlink':
            return JLink('Cortex-M4 r0p1, Little endian',
                         params='-device STM32F401RE -if swd -speed 2000')
        elif programmer == 'stlink':
            return STLink_STM32F4()

    def info(self, programmer):
        """Display info about the device."""
        # [0xE0042000] = CHIP_REVISION[31:16] + RESERVED[15:12] + DEVICE_ID[11:0]
        deviceid = programmer.readmem32(0xE0042000) & 0xFFF
        chiprev  = (programmer.readmem32(0xE0042000) & 0xFFFF0000) >> 16
        click.echo('Device ID : {0}'.format(DEVICEID_CHIPNAME_LOOKUP.get(deviceid,
                                                   '0x{0:03X}'.format(deviceid))))
        click.echo('Chip Rev  : {0}'.format(DEVICEID_CHIPREV_LOOKUP.get(chiprev,
                                                   '0x{0:04X}'.format(chiprev))))
        # Try to detect the Segger Device ID string and print it if using JLink
        if isinstance(programmer, JLink):
            hwid = programmer.readmem32(0xE0042000) & 0xFFF
            hwstring = DEVICEID_SEGGER_LOOKUP.get(hwid, '0x{0:03X}'.format(hwid))
            if '0x' not in hwstring:
                click.echo('Segger ID : {0}'.format(hwstring))
