

# Header to send/receive sysex messages
HEADER = [ord(ch) for ch in "YTX"]

PACKET_SIZE = 200

_packets_info = ["null", "CONFIG_MODE", "CONFIG_ACK", "DUMP_TO_HW"]

CONFIG_MODE	= 1			# PC->hw : Activate monitor mode
CONFIG_ACK	= 2			# HW->pc : Acknowledge the config mode
DUMP_TO_HW	= 3			# PC->hw : Partial EEPROM dump from PC
DUMP_OK		= 4			# HW->pc : Ack from dump properly saved


def make_sysex_packet(ptype, data):
	try:
		print("SYSEX SENT: " + _packets_info[ptype]);
	except:
		pass

	return [0xf0] + list(HEADER) + [ptype, 0] + list(data) + [0xf7]


import math
def make_sysex_multi_packet(ptype, data):
	try:
		print("SYSEX SENT: " + _packets_info[ptype]);
	except:
		pass

	pc = math.ceil(len(data) / PACKET_SIZE)
	if pc == 0:
		return

	split_list = []
	for i in range(pc):
		split_list.append([0xf0] + list(HEADER) + [ptype, i] + data[i*PACKET_SIZE:(i+1)*PACKET_SIZE] + [0xf7])

	return split_list
