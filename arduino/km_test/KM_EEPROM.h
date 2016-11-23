
/* * * * * * * * * * * * * * * * * * * * * * *
* Code by Martin Sebastian Wain for YAELTEX *
* contact@2bam.com                     2016 *
* * * * * * * * * * * * * * * * * * * * * * */

#include <Arduino.h>
#include <EEPROM.h>

#define KMS_EEPROM_START		0
#define NUM_INPUTS				32
#define NUM_OUTPUTS				64

namespace KMS {
	enum Mode {
		M_OFF = 0,
		M_NOTE = 1,
		M_CC = 2,
		M_NRPN = 3,
		// Only for inputs (save one bit in outputs)
		M_SHIFTER = 4
	};

	//Structure expandable for future replacement (thats why globals/statics weren't used)
	class EEPROM_IO {
	public:
		void read(int address, byte *buf, int len);
		void write(int address, byte *buf, int len);
	};

	class InputNorm {
	public:
		static const int length = 6;
		byte _p[length];

		byte mode() { return _p[0] & B111; }
		byte channel() { return (_p[0] & B1111000) >> 3; }
		byte param_coarse() { return _p[1]; }		//For Note, CC, NRPN, Shifter (bank)
		byte param_fine() { return _p[2]; }			//For NRPN
		byte param_min_coarse() { return _p[3]; }
		byte param_max_coarse() { return _p[4]; }
		bool analog() { return (_p[5] & 1) != 0; }
	};

	class InputUS {
	public:
		static const int length = 5;
		byte _p[length];

		byte mode() { return _p[0] & B111; }
		byte channel() { return (_p[0] & B1111000) >> 3; }
		byte param_coarse() { return _p[1]; }		//For Note, CC, NRPN, Shifter (bank)
		byte param_fine() { return _p[2]; }			//For NRPN
		byte param_min_coarse() { return _p[3]; }
		byte param_max_coarse() { return _p[4]; }
		//bool analog() { return (_p[5] & 1) != 0; }
	};


	class Output {
	public:
		static const int length = 4;
		byte _p[length];

		bool blink() { return (_p[0] & 1) != 0; }
		byte channel() { return (_p[0] & B1111000) >> 3; }
		byte note() { return _p[1]; }
        byte blink_min() { return _p[2]; }
        byte blink_max() { return _p[3]; }
	};

	extern bool isOutputMatrix;
	extern InputUS input_us;
	extern InputNorm inputs_norm[NUM_INPUTS];
	extern Output outputs[NUM_OUTPUTS];
	extern EEPROM_IO io;

	void loadData();

} //namespace KMS
