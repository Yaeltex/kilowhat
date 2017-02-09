#############################################
# Code by Martin Sebastian Wain for YAELTEX #
# contact@2bam.com                     2016 #
#############################################

#from lang import _
import lang
from math import floor

MODE_OFF    = 0
MODE_NOTE    = 1
MODE_CC        = 2
MODE_NRPN    = 3
MODE_PC     = 4
MODE_SHIFTER= 5
MODE_LABELS = (_("Off"), _("Note"), _("CC"), _("NRPN"),_("Program Change"), _("Shifter"))
MODE_ENABLED = [MODE_OFF, MODE_NOTE, MODE_CC, MODE_NRPN, MODE_PC, MODE_SHIFTER]

MAX_INPUTS_CC    = 32
MAX_OUTPUTS        = 64
MAX_BANKS         = 6

class GlobalData:
    output_matrix = False
    memory_mode = 1024                #memory.HARDWARE[0][1]    # FIXME: MAGIC NUMBER
    version = 0
    num_banks = 1
    num_inputs_norm = MAX_INPUTS_CC
    num_outputs = MAX_OUTPUTS

    def __init__(self, version):
        self.version = version

    def get_sysex(self):
        return [ord('Y'), ord('T'), ord('X'), self.version & 0xff]\
               + [0 for reserved in range(8)]\
               + [1 if self.output_matrix else 0, self.num_banks, self.num_inputs_norm, self.num_outputs]


class Bank:
    def __init__(self):
        self.input_us = [InputDataUS()]
        self.input_cc = [InputDataCC() for __ in range(MAX_INPUTS_CC)]
        self.output = [OutputData() for __ in range(MAX_OUTPUTS)]


class OutputData:
    note = 0
    channel = 0
    blink_min = 42
    blink_max = 84
    blink = True
    shifter = False

    #CHANNEL(4) padding(1) SHIFTER (1) BLINK(1)
    #NOTE(7)
    #BLINK-MIN(7)
    #BLINK-MAX(7)
    def get_sysex(self):
        return [(1 if self.blink else 0) | ((1 if self.shifter else 0) << 1) | ((self.channel-1 & 0xf) << 3),\
            self.note & 0x7f, self.blink_min & 0x7f, self.blink_max & 0x7f]

    def set_sysex(self, msg):
        assert(len(msg) == len(self.get_bytes()))
        self.blink = msg[0] & 1 == 1
        self.shifter = (msg[0]>>1 & 1) == 1
        self.channel = (msg[0] >> 3 & 0xf) + 1                  # channel is 1-16 but sysex uses 0-15
        self.note = msg[1] & 0x7f
        self.blink_min = msg[2] & 0x7f
        self.blink_max = msg[3] & 0x7f


class InputData:
    mode = MODE_NOTE
    param = 0
    channel = 0
    min = 0
    max = 127

    #CHANNEL(4) MODE(3)
    #COARSE(7)
    #FINE(7)
    #MIN(7)
    #MAX(7)
    def get_sysex(self):
        return [(self.mode&0x7) | (self.channel-1 & 0xf) << 3,\
            self.param >> 7 & 0x7f, self.param & 0x7f,  (self.min>>7) & 0x7f if self.mode == MODE_NRPN else self.min,\
                                                        (self.max>>7) & 0x7f if self.mode == MODE_NRPN else self.max]

    def set_sysex(self, msg):
        assert(len(msg) == len(self.get_bytes()))
        self.mode = msg[0] >> 1 & 0x7
        self.channel = (msg[0] >> 3 & 0xf) + 1                  # +1 because channel is 1-16 but protocol uses 0-15
        self.param = msg[1] & 0x7f | (msg[2] & 0x7f) << 7
        self.min = msg[3] & 0x7f
        self.max = msg[4] & 0x7f


class InputDataCC(InputData):
    analog = True
    toggle = False

    #ANALOG(1)
    def get_sysex(self):
        r = super().get_sysex()
        r += [(1 if self.analog else 0) | (2 if self.toggle else 0)]
        return r

    def set_sysex(self, msg):
        super().set_sysex(msg)
        self.analog = (msg[0] & 1) != 0
        self.toggle = (msg[0] & 2) != 0


class InputDataUS(InputData):
    dist_min = 0
    dist_max = 400

    def get_sysex(self):
        r = super().get_sysex()
        r += [(self.dist_min >> 7) & 0x7f, self.dist_min & 0x7f, (self.dist_max >> 7) & 0x7f, self.dist_max & 0x7f]
        return r
