
#include "KM_EEPROM.h"


//PARA PROBAR, DESCOMENTAR ESTE DEFINE LA PRIMERA VEZ QUE SE SUBE/PRUEBA Y LUEGO DEJARLA COMENTADA PARA TESTEAR
//#define WRITE_EEPROM

#define SERIAL_PRINT(lbl, data) { Serial.print(lbl); Serial.print(": "); Serial.println(data); }

byte test_data[] ={
	0, 18, 0, 2, 0, 127, 89, 0, 5, 0, 127, 1, 10, 0, 1, 12, 66, 1, 2, 1, 94, 0, 127, 0, 1, 0, 0, 0, 127, 0, 57, 0, 5, 0, 127, 1, 0, 0, 0, 2, 54, 1, 1, 0, 0, 0, 127, 1, 1, 0, 0, 0, 127, 1, 1, 0, 0, 0, 127, 1, 1, 0, 0, 0, 127, 1, 1, 0, 0, 0, 127, 1, 1, 0, 0, 0, 127, 1, 1, 0, 0, 0, 127, 1, 1, 0, 0, 0, 127, 1, 1, 0, 0, 0, 127, 1, 1, 0, 0, 0, 127, 1, 1, 0, 0, 0, 127, 1, 1, 0, 0, 0, 127, 1, 1, 0, 0, 0, 127, 1, 1, 0, 0, 0, 127, 1, 1, 0, 0, 0, 127, 1, 1, 0, 0, 0, 127, 1, 1, 0, 0, 0, 127, 1, 1, 0, 0, 0, 127, 1, 1, 0, 0, 0, 127, 1, 1, 0, 0, 0, 127, 1, 1, 0, 0, 0, 127, 1, 1, 0, 0, 0, 127, 1, 1, 0, 0, 0, 127, 1, 1, 0, 0, 0, 127, 1, 1, 0, 0, 0, 127, 1, 1, 0, 0, 0, 127, 1, 1, 0, 42, 84, 1, 55, 42, 84, 8, 2, 42, 84, 8, 33, 66, 84, 1, 4, 111, 22, 1, 5, 42, 84, 1, 6, 42, 84, 1, 7, 42, 84, 1, 8, 42, 84, 1, 9, 42, 84, 1, 10, 42, 84, 1, 11, 42, 84, 1, 12, 42, 84, 1, 13, 42, 84, 1, 14, 42, 84, 1, 15, 42, 84, 1, 16, 42, 84, 1, 17, 42, 84, 1, 18, 42, 84, 1, 19, 42, 84, 1, 20, 42, 84, 1, 21, 42, 84, 1, 22, 42, 84, 1, 23, 42, 84, 1, 24, 42, 84, 1, 25, 42, 84, 1, 26, 42, 84, 1, 27, 42, 84, 1, 28, 42, 84, 1, 29, 42, 84, 1, 30, 42, 84, 1, 31, 42, 84, 1, 32, 42, 84, 1, 33, 42, 84, 1, 34, 42, 84, 1, 35, 42, 84, 1, 36, 42, 84, 1, 37, 42, 84, 1, 38, 42, 84, 1, 39, 42, 84, 1, 40, 42, 84, 1, 41, 42, 84, 1, 42, 42, 84, 1, 43, 42, 84, 1, 44, 42, 84, 1, 45, 42, 84, 1, 46, 42, 84, 1, 47, 42, 84, 1, 48, 42, 84, 1, 49, 42, 84, 1, 50, 42, 84, 1, 51, 42, 84, 1, 52, 42, 84, 1, 53, 42, 84, 1, 54, 42, 84, 1, 55, 42, 84, 1, 56, 42, 84, 1, 57, 42, 84, 1, 58, 42, 84, 1, 59, 42, 84, 1, 60, 42, 84, 1, 61, 42, 84, 1, 62, 42, 84, 1, 63, 42, 84
};

void printInputNorm(const char *lbl, KMS::InputNorm &d, int i) {
	SERIAL_PRINT(lbl, i);
	SERIAL_PRINT("\tAnalog", d.analog());
	SERIAL_PRINT("\tMode", d.mode());
	SERIAL_PRINT("\tChannel", d.channel());
	SERIAL_PRINT("\tParam fine (nrpn)", d.param_fine());
    SERIAL_PRINT("\tParam coarse", d.param_coarse());
    SERIAL_PRINT("\tParam full NRPN", (d.param_coarse() << 7) | d.param_fine());
    SERIAL_PRINT("\tMin", d.param_min_coarse());
    SERIAL_PRINT("\tMax", d.param_max_coarse());
}

void printInputUS(const char *lbl, KMS::InputUS &d, int i) {
	SERIAL_PRINT(lbl, i);
	SERIAL_PRINT("\tMode", d.mode());
	SERIAL_PRINT("\tChannel", d.channel());
	SERIAL_PRINT("\tParam fine (nrpn)", d.param_fine());
    SERIAL_PRINT("\tParam coarse", d.param_coarse());
    SERIAL_PRINT("\tParam full NRPN", (d.param_coarse() << 7) | d.param_fine());
    SERIAL_PRINT("\tMin", d.param_min_coarse());
    SERIAL_PRINT("\tMax", d.param_max_coarse());
}

void printOutput(const char *lbl, KMS::Output &d, int i) {
    SERIAL_PRINT(lbl, i);
    SERIAL_PRINT("\tChannel", d.channel());
    SERIAL_PRINT("\tNote", d.note());
    SERIAL_PRINT("\tBlink", d.blink());
    SERIAL_PRINT("\ttBlink Min", d.blink_min());
    SERIAL_PRINT("\ttBlink Max", d.blink_max());
}

void setup() {
	Serial.begin(9600);
	 
	#ifdef WRITE_EEPROM
		KMS::io.write(0, test_data, sizeof(test_data));
		Serial.println("EEPROM escrita");
	#else
		KMS::loadData();
		SERIAL_PRINT("Matrix", KMS::isOutputMatrix);
		printInputUS("Input US", KMS::input_us, 0);
		for(int i = 0; i<NUM_INPUTS; i++) {
			printInputNorm("Input Norm", KMS::inputs_norm[i], i);
		}
		for(int i = 0; i<NUM_OUTPUTS; i++) {
            printOutput("Output", KMS::outputs[i], i);
		}
	#endif
}

void loop() {
}

