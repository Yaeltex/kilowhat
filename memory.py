from model import *

KILOMUX_OVERHEAD = 1			#Overhead bytes
HARDWARE = [
	  ("Arduino UNO (1024)", 1024)
	, ("Arduino MEGA (4096)", 4096)
]

DATA_SIZE = {
	  'global': len(GlobalData(0).get_sysex())
	, 'input_cc': len(InputDataCC().get_sysex())
	, 'input_us': len(InputDataUS().get_sysex())
	, 'output': len(OutputData().get_sysex())
}

assert DATA_SIZE['global'] == 16
assert DATA_SIZE['input_us'] == 9
assert DATA_SIZE['input_cc'] == 6
assert DATA_SIZE['output'] == 4

def calc_max_outs(mem, nbanks, ninputs):
	mem -= DATA_SIZE['global'] + KILOMUX_OVERHEAD
	mem -= nbanks * DATA_SIZE['input_us']
	mem -= nbanks * ninputs * DATA_SIZE['input_cc']
	return min(MAX_OUTPUTS, floor(mem / (nbanks * DATA_SIZE['output'])))

def calc_max_ins(mem, nbanks, nouts):
	mem -= DATA_SIZE['global'] + KILOMUX_OVERHEAD
	mem -= nbanks * DATA_SIZE['input_us']
	mem -= nbanks * nouts * DATA_SIZE['output']
	return min(MAX_INPUTS_CC, floor(mem / (nbanks * DATA_SIZE['input_cc'])))

def calc_max_banks(mem, nins, nouts):
	mem -= DATA_SIZE['global'] + KILOMUX_OVERHEAD
	bank_size = DATA_SIZE['input_us'] + nins * DATA_SIZE['input_cc'] + nouts * DATA_SIZE['output']
	return min(MAX_BANKS, floor(mem / bank_size))

def calc_memory(banks, nins, nouts):
	mem = 0
	mem += DATA_SIZE['global'] + KILOMUX_OVERHEAD
	bank_size = DATA_SIZE['input_us'] + nins * DATA_SIZE['input_cc'] + nouts * DATA_SIZE['output']
	mem += bank_size * banks
	return mem
