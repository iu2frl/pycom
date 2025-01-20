from ..device_base import DeviceBase
from ..utils import Utils
from ..enums import OperatingMode, VFOOperation


class IC706MKII(DeviceBase):
    def __init__(
        self,
        radio_address: str,
        port = "/dev/ttyUSB0",
        baudrate: int = 19200,
        debug = False,
        controller_address = "0xE0",
        timeout = 1,
        attempts = 3):

        super().__init__(
            radio_address=radio_address,
            port=port,
            baudrate=baudrate,
            debug=debug,
            controller_address=controller_address,
            timeout=timeout,
            attempts=attempts
        )

        self.utils = Utils(
            self._ser,
            self.transceiver_address,
            self.controller_address,
            self._read_attempts
        )

    def read_operating_frequency(self) -> int:
        """
        Read the operating frequency
        
        Returns: the currently tuned frequency in Hz
        """
        try:
            reply = self.utils.send_command(b"\x03")
            return self.utils.decode_frequency(reply[5:10])
        except:
            return -1

    def read_operating_mode(self) -> OperatingMode:
        """
        Read the operating mode
        
        Returns: the current mode
        """
        reply = self.utils.send_command(b"\x04")
        if len(reply) == 8:
            mode = OperatingMode(int(reply[5:6].hex()))
            return mode
    
    def set_operating_mode(self, mode: OperatingMode):
        """Sets the operating mode and filter."""
        # Command 0x06 with mode and filter data
        data = bytes(mode.value)
        self.utils.send_command(b"\x06", data=data)

    def send_operating_frequency(self, frequency_hz: int) -> bool:
        """
        Send the operating frequency
        
        Returns: True if the frequency was properly sent
        """
        # Validate input
        if not (10_000 <= frequency_hz <= 74_000_000):  # IC-7300 frequency range in Hz
            raise ValueError("Frequency must be between 10 kHz and 74 MHz")
        # Encode the frequency
        data = self.utils.encode_frequency(frequency_hz)

        # Use the provided _send_command method to send the command
        reply = self.utils.send_command(b"\x05", data=data)
        if len(reply) > 0:
            return True
        else:
            return False
    
    def set_vfo_mode(self, vfo_mode: VFOOperation = VFOOperation.SELECT_VFO_A):
        """Sets the VFO mode."""
        if vfo_mode in VFOOperation:
            self.utils.send_command(b"\x07", data=vfo_mode.value)
        else:
            raise ValueError("Invalid vfo_mode")
    
    def stop_scan(self):
        """Stops the scan."""
        self.utils.send_command(b"\x0E\x00")

    def start_scan(self):
        """
        Starts scanning, different types available according to the sub command
        
        Note: this always returns some error
        """
        self.utils.send_command(b"\x0E\x01")

    def set_memory_mode(self, memory_channel: int):
        """Sets the memory mode, accepts values from 1 to 101"""
        if not (1 <= memory_channel <= 101):
            raise ValueError("Memory channel must be between 1 and 101")
        # 0001 to 0109 Select the Memory channel *(0001=M-CH01, 0099=M-CH99)
        # 0100 Select program scan edge channel P1
        # 0101 Select program scan edge channel P2
        
        if 0 < memory_channel < 100:
            hex_list = ["0x00"]
        elif memory_channel in [100, 101]:
            hex_list = ["0x01"]
        else:
            raise ValueError("Memory channel must be between 1 and 101")
        number_as_string = str(memory_channel).rjust(3, "0")
        hex_list.append(f"0x{number_as_string[1]}{number_as_string[2]}")
        self.utils.send_command(b"\x08", data=bytes([int(hx, 16) for hx in hex_list]))

    def memory_copy_to_vfo(self):
        """Copies memory to VFO"""
        self.utils.send_command(b"\x0A")

    def memory_clear(self):
        """Clears the memory"""
        self.utils.send_command(b"\x0B")