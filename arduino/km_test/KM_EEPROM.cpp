
/* * * * * * * * * * * * * * * * * * * * * * *
* Code by Martin Sebastian Wain for YAELTEX *
* contact@2bam.com                     2016 *
* * * * * * * * * * * * * * * * * * * * * * */

#include "KM_EEPROM.h"

namespace KMS {

	void EEPROM_IO::read(int address, byte *buf, int len) {
		address += KMS_EEPROM_START;
		while(len--)
			*(buf++) = EEPROM.read(address++);
	}
	void EEPROM_IO::write(int address, byte *buf, int len) {
		address += KMS_EEPROM_START;
		while(len--)
			EEPROM.update(address++, *(buf++));		//Update only writes if the value changed (extends EEPROM lifetime)
	}

	bool isOutputMatrix;
	InputUS input_us;
	InputNorm inputs_norm[NUM_INPUTS];
	Output outputs[NUM_OUTPUTS];
	EEPROM_IO io;

	void loadData() {
		byte b;
		io.read(0, &b, 1);
		isOutputMatrix = b == 1;
		io.read(1, input_us._p, InputUS::length);
		int i;
		for(i = 0; i<NUM_INPUTS; i++)
			io.read(1 + InputUS::length + i*InputNorm::length, inputs_norm[i]._p, InputNorm::length);
		for(i = 0; i<NUM_OUTPUTS; i++)
			io.read(1 + InputUS::length + NUM_INPUTS * InputNorm::length + i * Output::length, outputs[i]._p, Output::length);
	}

} //namespace KMS
