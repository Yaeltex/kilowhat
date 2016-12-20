############################################
# Code by Martin Sebastian Wain for YAELTEX #
#############################################

import sys
import datetime

# Debug mode: python kilowhat.py -d
DEBUG = False
#print(sys.argv)
if len(sys.argv) >= 2 and sys.argv[1] == "-d":
	DEBUG = True

if not DEBUG:
	sys.stdout = open("kmgui_log.txt", "a", 4)
	print("-----------------------------------")
	print(datetime.datetime.utcnow().ctime())
	print("DEBUG: "+ str(DEBUG))
	print("-----------------------------------")

from PySide.QtCore import *
from PySide.QtGui import *
import rtmidi
import time
import os
import os.path
import pickle
from pprint import pprint

import sysex
import lang
_ = _			#WORKAROUND: _ is globally installed by lang

from model import *
import memory

# General
TITLE = "Kilowhat"
VERSION = "v1.06"

# User interface
COLOR_TIMEOUT = 500						# ms. Background coloring timeout

# Midi
POLL_INTERVAL = 25						# ms. Midi in polling interval
THRESHOLD_SELECT = 16					# Delta threshold for selecting (coloring background and ensuring is visible in scroll area)
MONITOR_CHAN_US = 15					# Ultra sound channel monitoring

# Files
PROTOCOL_VERSION = 1					# For file save/load & EEPROM validation

FILE_AUTOMATIC = "automatic.kmgui"
FILE_RECOVER = "recover.kmgui"


# Combo box indexes
LED_OUTPUT_NORMAL = 0
LED_OUTPUT_MATRIX = 1

import plat
form = None

config = {
	  'file_ver': PROTOCOL_VERSION
	, 'global': GlobalData(PROTOCOL_VERSION)
	, 'file':{'desc':''}
	, 'banks': [Bank() for __ in range(memory.MAX_BANKS) ]
}

def midi_send(msg):
	print("midi_send() ", msg)
	global form
	try:
		midiout.send_message(msg)
	except Exception as e:
		print(e)
		if form:
			form.txt_log.append(_("ERROR OUT: ") + str(e))

class wait_cursor:
	def __enter__(self):
		if not plat._LINUX:
			QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

	def __exit__(self, type, value, traceback):
		if not plat._LINUX:
			QApplication.restoreOverrideCursor()





#print(config['input_cc'])

import platform
if platform.system() == "Windows":
	midi_api = rtmidi.API_WINDOWS_MM
elif platform.system() == "Darwin":
	midi_api = rtmidi.API_MACOSX_CORE
else:
	midi_api = rtmidi.API_UNSPECIFIED

midiout = rtmidi.MidiOut(midi_api)
midiin = rtmidi.MidiIn(midi_api)

 # 0x80     Note Off
 #   0x90     Note On
 #   0xA0     Aftertouch
 #   0xB0     Continuous controller
 #   0xC0     Patch change
 #   0xD0     Channel Pressure
 #   0xE0     Pitch bend
 #   0xF0     Sys ex (non-musical commands)
MIDI_NOTE_OFF	= 0x80
MIDI_NOTE_ON	= 0x90
MIDI_CC			= 0xb0

if False:
	note_on = [0x90, 60, 112] # channel 1, middle C, velocity 112
	note_off = [0x80, 60, 0]
	for __ in range(0,5):
		midi_send(note_on)
		time.sleep(0.5)
		midi_send(note_off)
		time.sleep(0.5)



def send_sysex_dump():
	glob = config['global'];
	data = [glob]
	for i in range(glob.num_banks):
		bank = config['banks'][i]
		data.append(bank.input_us[0])
		for j in range(glob.num_inputs_norm):
			data.append(bank.input_cc[j])
		for j in range(glob.num_outputs):
			data.append(bank.output[j])

	for x in data:
		print("{0} : {1} => SYSEX{2}".format(type(x), vars(x), x.get_sysex()))

	accum = [v for x in data for v in x.get_sysex()]
	try:
		print("FINAL SYSEX DUMP:")
		print(len(accum))
		print(accum)
		pkt_list = sysex.make_sysex_multi_packet(sysex.DUMP_TO_HW, accum)

		print("PKT COUNT ", len(pkt_list))
		for pkt in pkt_list:
			print("SYSEX_PKT ", len(pkt), pkt)
			midi_send(pkt)
			#FIXME: send in multiple packets only in Darwin/MacOS
			#if platform.system() == "Darwin":
			print("Sleep 1 seg")
			time.sleep(1)
	except Exception as e:
		print("Exception", e)


# TODO: stuff is a list of a list with widgets, layouts and tuples for cellspan (w/l, spanx, spany)
def grid_create(grid:QGridLayout, stuff):
	for row in stuff:
		for elem in row:
			if isinstance(elem, QWidget):
				grid.addWidget(elem)

class GridHelper:
	_x = 0
	_y = 0
	def __init__(self, grid):
		self._grid = grid
		#grid.setSizeConstraint(QLayout.SetMaximumSize)


	def _skip(self):
		# asd = self._grid.itemAtPosition(self._y, self._x)
		while self._grid.itemAtPosition(self._y, self._x) is not None:
			self._x += 1		
		
	def widget(self, w, spanx=1, spany=1, width=None, align=0):
		#print("ADD {0} at {1},{2}".format(w, self._x, self._y))
		if width is not None:
			w.setFixedWidth(width)
		self._grid.addWidget(w, self._y, self._x, spany, spanx, align)
		#else:
		w.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
		#if DEBUG and self._x % 2 == 0:
		#	w.setStyleSheet("background-color: #0000ff")
		self._skip()
		return self

	def pic(self, path, spanx=1, spany=1, align=Qt.AlignLeft):
		w = QLabel()
		w.setPixmap(QPixmap(path))
		self.widget(w, spanx, spany, None, align)
		return self

	def label(self, text, spanx=1, spany=1, align=Qt.AlignLeft):
		#print("\nLBALE {0} at {1},{2}".format(text, self._x, self._y))
		lbl = QLabel(text)
		lbl.setStyleSheet("QLabel {font-size: 10pt}")
		self._grid.addWidget(lbl, self._y, self._x, spany, spanx, align)
		self._skip()
		return self

	def newLine(self):
		self._x = 0
		self._y += 1
		self._skip()
		return self




class MemoryWidget(QWidget):
	def __init__(self, parent):
		print("MemoryWidget() parent ctor")
		super().__init__(parent)
		print("MemoryWidget()")

		self.cmi = cmi = QComboBox()
		self.cmi.setStyleSheet("QComboBox { font-size: 10pt }")
		self.cmo = cmo = QComboBox()
		self.cmo.setStyleSheet("QComboBox { font-size: 10pt }")

		#Reload MIDI ports
		self.btn_reload_midi = QPushButton(_("Scan")) 
		self.btn_reload_midi.setStyleSheet("QPushButton { font-size: 10pt }")
		self.btn_reload_midi.setMinimumWidth(160)
		self.btn_reload_midi.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

		#Create controls
		self.output_matrix = QComboBox()
		self.output_matrix.setStyleSheet("QComboBox { font-size: 10pt }")
		self.hardware = QComboBox()
		self.hardware.setStyleSheet("QComboBox { font-size: 10pt }")
		self.banks = QSpinBox()
		self.banks.setStyleSheet("QSpinBox { font-size: 10pt }")
		self.ins = QSpinBox()
		self.ins.setStyleSheet("QSpinBox { font-size: 10pt }")
		self.outs = QSpinBox()
		self.outs.setStyleSheet("QSpinBox { font-size: 10pt }")
		self.test = QLabel()		#Never added

		self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

		grid = QGridLayout()
		grid.setHorizontalSpacing(15)
		self.setLayout(grid)
		h = GridHelper(grid)

		#Workaround for very small combo boxes
		cmi.view().setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Ignored) #.setSizeAdjustPolicy(QComboBox.AdjustToContents)
		cmo.view().setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Ignored) #.setSizeAdjustPolicy(QComboBox.AdjustToContents)

		tiny = 112		# FIXME: this is not a great way, but layouts are being dicks
		small = None
		h.label(_("MIDI ports")).widget(cmi, spanx=2, width=tiny).widget(cmo, spanx=1, width=tiny)\
			.label(_("Set banks")).widget(self.banks, width=tiny)\
			.newLine()
		h.label(_(" ")).widget(self.btn_reload_midi, spanx=3, width=small).label(_("Set inputs")).widget(self.ins, width=tiny).newLine()
		h.label(_("Hardware")).widget(self.hardware, spanx=3, width=small).label(_("Set outputs")).widget(self.outs, width=tiny).newLine()
		h.label(_("LEDS mode")).widget(self.output_matrix, spanx=3, width=small).label(_(" ")).newLine()

		# Config widgets
		self.output_matrix.addItems([_("Normal"), _("Matrix")])
		for item in memory.HARDWARE:
			self.hardware.addItem(item[0], item[1])
		self.banks.setMinimum(1)
		self.ins.setMinimum(1)
		self.outs.setMinimum(1)

		print("MemoryWidget() populate_ports")

		self.populate_ports()

		print("MemoryWidget() connect signals")

		# Connect signals
		cmi.currentIndexChanged.connect(self.change_midi_in)
		cmo.currentIndexChanged.connect(self.change_midi_out)
		self.btn_reload_midi.pressed.connect( self.reload_midi_ports )
		self.output_matrix.currentIndexChanged.connect(self.on_param_value_changed)
		self.hardware.currentIndexChanged.connect(self.on_param_value_changed)
		self.banks.valueChanged.connect(self.on_param_value_changed)
		self.ins.valueChanged.connect(self.on_param_value_changed)
		self.outs.valueChanged.connect(self.on_param_value_changed)

		# Reset (TODO: done by the Form or here?)
		print("MemoryWidget() reset")
		self.on_param_value_changed()
		self.reopen_ports()

	def reload_midi_ports(self):
		global form
		print("Reloading MIDI ports")
		form.txt_log.clear()
		form.txt_log.append(_("Welcome to Kilowhat!"))
		ports = midiin.get_ports()
		print(ports)
		self.cmi.clear() # Clear items of the ComboBox
		self.cmo.clear()
		#self.reopen_ports() 
		self.populate_ports()

	def populate_ports(self):
		print("populate_ports()")
		ports = midiin.get_ports()
		if ports:
			for i, port in enumerate(ports):
				self.cmi.addItem(_("In {0}: {1}").format(i, port))
		print("midiin ports ", ports)

		ports = midiout.get_ports()
		if ports:
			for i, port in enumerate(ports):
				self.cmo.addItem(_("Out {0}: {1}").format(i, port))
		print("midiout ports ", ports)

	def reopen_ports(self):
		print("MemoryWidget() reopen ports")
		# Workaround: Close both for some enqueued messages in loopbe1 in
		print("reopen_ports: close")
		midiin.close_port()
		midiout.close_port()
		# callback is in a non GUI thread and can't modify widgets
		# midiin.set_callback(lambda msg, t: self.processCommand(msg))
		# Ver timer + poll_in()

		global form

		print("reopen_ports: midi in ", self.cmi.currentIndex(), self.cmo.count())
		# IMPORTANT: First open midi-in to get ACK
		cmi_i = self.cmi.currentIndex()
		if cmi_i >= 0:
			try:
				print("Open in port: ", cmi_i)
				midiin.open_port(cmi_i)
			except Exception as e:
				print('Error al abrir puerto de entrada{0}: {1}'.format(cmi_i, e))
				if form:
					form.txt_log.append(('Error al abrir puerto de entrada {0}: {1}').format(cmi_i, e))
				#QMessageBox.warning(self, _('Error'), _('Error al abrir puerto de salida {0}: {1}').format(cmi_i, e))

		print("reopen_ports: midi out ", self.cmo.currentIndex(), self.cmo.count())
		cmo_i = self.cmo.currentIndex()
		if cmo_i >= 0:
			try:
				print("Open out port: ", cmo_i)
				midiout.open_port(cmo_i)
				#TODO: Unflag as correct device
				print("Send CONFIG_MODE sysex")
				midi_send(sysex.make_sysex_packet(sysex.CONFIG_MODE, []))
			except Exception as e:
				print('Error al abrir puerto de salida {0}: {1}'.format(cmo_i, e))
				if form:
					form.txt_log.append(('Error al abrir puerto de salida {0}: {1}').format(cmi_i, e))
				#QMessageBox.warning(self, _('Error'), _('Error al abrir puerto de salida {0}: {1}').format(cmo_i, e))
		print("reopen_ports: OK")


	def change_midi_in(self, index):
		print("Open IN {0}".format(index))
		self.reopen_ports()

	def change_midi_out(self, index):
		print("Open OUT {0}".format(index))
		global form
		form.txt_log.clear()
		form.txt_log.append(_("Welcome to Kilowhat!"))
		self.reopen_ports()

	def raise_changed_memory_event(self):
		with wait_cursor():
			self.parent().refresh_tabs()
			self.parent().refresh_in_outs()
			pass

	def on_param_value_changed(self):
		print("MemoryWidget() on_param_value_changed")

		mem = self.hardware.itemData(self.hardware.currentIndex())
		self.test.setText("eeprom mem used {0}B/{1}B".format(
			memory.calc_memory(self.banks.value(), self.ins.value(), self.outs.value()),
			mem
		))
		# self.test.setText("max banks {0}  max ins {1}  max outs {2}  eeprom mem used {3}B/{4}B".format(
		# 		memory.calc_max_banks(mem, self.ins.value(), self.outs.value()),
		# 		memory.calc_max_ins(mem, self.banks.value(), self.outs.value()),
		# 		memory.calc_max_outs(mem, self.banks.value(), self.ins.value()),
		# 		memory.calc_memory(self.banks.value(), self.ins.value(), self.outs.value()),
		# 		mem
		# 	)
		# )
		max_banks = memory.calc_max_banks(mem, self.ins.value(), self.outs.value())
		max_ins = memory.calc_max_ins(mem, self.banks.value(), self.outs.value())
		max_outs = memory.calc_max_outs(mem, self.banks.value(), self.ins.value())
		matrix = self.output_matrix # type: QComboBox
		if matrix.currentIndex() == LED_OUTPUT_NORMAL:
			max_outs = min(max_outs, 16)
		self.banks.setMaximum(max(1, max_banks))
		self.banks.setSuffix('/{0}'.format(max_banks))
		self.ins.setMaximum(max(1, max_ins))
		self.ins.setSuffix('/{0}'.format(max_ins))
		self.outs.setMaximum(max(1, max_outs))
		self.outs.setSuffix('/{0}'.format(max_outs))

	def model(self) -> GlobalData:
		return config['global']

	def load_model(self):
		model = self.model()

		self.output_matrix.setCurrentIndex(config['global'].output_matrix);

		# Workaround: Temporary!
		self.banks.setMaximum(10000);
		self.ins.setMaximum(10000);
		self.outs.setMaximum(10000);

		self.hardware.setCurrentIndex(self.hardware.findData(model.memory_mode))
		self.banks.setValue(model.num_banks)
		self.ins.setValue(model.num_inputs_norm)
		self.outs.setValue(model.num_outputs)

		self.on_param_value_changed()	#This will recalculate maximums

		#TODO: if necessary cue  main widget to rebuild tabvs etc

	def save_model(self):
		model = self.model()
		config['global'].output_matrix = self.output_matrix.currentIndex()
		model.hardware_mode = self.hardware.itemData(self.hardware.currentIndex())
		model.num_banks = self.banks.value()
		model.num_inputs_norm = self.ins.value()
		model.num_outputs = self.outs.value()
		self.raise_changed_memory_event()
		#TODO: cue main widget to rebuild tabs and such

class PaintWidget(QWidget):
	def paintEvent(self, *args, **kwargs):
		o = QStyleOption()
		o.initFrom(self)
		p = QPainter(self)
		self.style().drawPrimitive(QStyle.PE_Widget, o, p, self)

	def __init__(self, parent=None):
		super().__init__(parent)

class ConfigWidget(QWidget):
	alert_txt = None

	def setAlert(self, txt_or_none):
		self.alert_txt = txt_or_none
		if txt_or_none is not None:
			self.lbl_alert.setText(txt_or_none)
			self.lbl_alert.setVisible(True)
		else:
			self.lbl_alert.setVisible(False)

	def paintEvent(self, *args, **kwargs):
		o = QStyleOption()
		o.initFrom(self)
		p = QPainter(self)
		self.style().drawPrimitive(QStyle.PE_Widget, o, p, self)

	def add(self, w, idx = -1):
		#self.layout().addWidget(w)
		self.h_layout.insertWidget(idx, w)
		w.installEventFilter(self)
		return w

	def addwl(self, label, w, idx = -1):
		idx = self.h_layout.count() if idx < 0 else idx
		self.add(w, idx)
		lbl = QLabel(label, self)
		lbl.setStyleSheet("QLabel {font-size: 10pt}")
		self.add(lbl, idx).setAlignment(Qt.AlignRight | Qt.AlignCenter)
		return w


	def eventFilter(self, obj, ev):
		global form
		if ev.type() == QEvent.MouseButtonPress or ev.type() == QEvent.FocusIn:
			form.select(self)
		return False

	def __init__(self, model_name, index, parent=None):
		super(ConfigWidget, self).__init__(parent)

		self.bank = 0
		self._index = index
		self._model_name = model_name


		v_layout = QVBoxLayout()

		self.h_layout = ll = QHBoxLayout()
		v_layout.addLayout(self.h_layout)
		self.lbl_alert = QLabel()
		self.lbl_alert.setObjectName("alert")
		#self.lbl_alert.setText("Esto es una alerta.")
		#if index % 2 == 0:
		self.lbl_alert.setVisible(False)
		v_layout.addWidget(self.lbl_alert)

		self.setLayout(v_layout)

		timer = QTimer(self)
		timer.setInterval(COLOR_TIMEOUT)
		timer.setSingleShot(True)
		timer.timeout.connect(self.hide_feedback)
		self._color_timer = timer

		self.setAutoFillBackground(True)

		self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)


	def model(self):
		return getattr(config['banks'][self.bank], self._model_name)[self._index]

	def hide_feedback(self):
		stylesheetProp(self.monitor, "feedback", False)

	def show_feedback(self):
		stylesheetProp(self.monitor, "feedback", True)
		self._color_timer.start()

	def unselect(self):
		stylesheetProp(self, "selection", False)
		self.setStyleSheet(self.styleSheet())

	def select(self):
		stylesheetProp(self, "selection", True)
		self.setStyleSheet(self.styleSheet())



class OutputConfig(ConfigWidget):

	current_test = None

	def __init__(self, model_name, index, parent=None):
		super(OutputConfig, self).__init__(model_name, index, parent)

		number = self.add(QLabel(str(index)))
		number.setStyleSheet("QLabel { font-size: 12pt }")

		self.test = self.add(QPushButton(_("Test")))
		self.test.setStyleSheet("QPushButton { font-size: 10pt }")
		self.test.setFixedWidth(70)
		self.test.pressed.connect(self.on_test_press)
		self.test.released.connect(self.on_test_release)
		#self.monitor = add(QLabel())
		#self.monitor.setFixedWidth(60)

		#self.da = addwl(_("D/A"), QCheckBox())
		#self.mode = addwl(_("Mode"), QComboBox())
		#self.mode.addItems((_("Note"), _("CC"), _("NRPN")))

		noteSB = QSpinBox()
		noteSB.setStyleSheet("QLabel { font-size: 10pt }")
		self.param = self.addwl(_("Note"), noteSB)
		self.param.setRange(0, 127)

		chanSB = QSpinBox()
		chanSB.setStyleSheet("QLabel { font-size: 10pt }")
		self.channel = self.addwl(_("Channel"), chanSB)
		self.channel.setRange(0, 15)

		minSB = QSpinBox()
		minSB.setStyleSheet("QLabel { font-size: 10pt }")
		self.min = self.addwl(_("Min."), minSB)
		self.min.setRange(0, 127)

		maxSB = QSpinBox()
		maxSB.setStyleSheet("QLabel { font-size: 10pt }")
		self.max = self.addwl(_("Max."), maxSB)
		self.max.setRange(0, 127)
		self.max.setValue(127)

		self.blink = self.addwl(_("Intermitent"), QCheckBox())

	def load_model(self):
		model = self.model()
		self.param.setValue(model.note)
		self.channel.setValue(model.channel)
		self.min.setValue(model.blink_min)
		self.max.setValue(model.blink_max)
		self.blink.setChecked(model.blink)

	def save_model(self):
		model = self.model()
		model.note = self.param.value()
		model.channel = self.channel.value()
		model.blink_min = self.min.value()
		model.blink_max = self.max.value()
		model.blink = self.blink.isChecked()

	def on_test_press(self):
		print("Test btn press")
		if self.current_test is not None:
			return
		self.save_model()
		m = self.model()
		self.current_test = m.channel, m.note
		print("Press CH{0} N{1}".format(m.channel, m.note))
		midi_send((MIDI_NOTE_ON | m.channel, m.note, 0x7f))

	def on_test_release(self):
		channel, note = self.current_test
		print("Release CH{0} N{1}".format(channel, note))
		midi_send((MIDI_NOTE_OFF | channel, note, 0))
		self.current_test = None

def stylesheetProp(widget, name, value):
	widget.setProperty(name, "true" if value is True else "false" if value is False else value)
	widget.setStyleSheet(widget.styleSheet())		#Force widget stylesheet reload

# Subclassed spinbox to show multiplied output in text even if value remains
class QSpinBoxHack(QSpinBox):
	_increments = 1

	def setIncrement(self, inc):
		self._increments = inc
		self.setValue((self.value() // inc) * inc)

	def valueFromText(self, *args, **kwargs):
		try:
			val = int(args[0]) // self._increments
		except:
			val = 0
		return val

	def textFromValue(self, *args, **kwargs):
		return str(args[0] * self._increments)

	def validate(self, *args, **kwargs):
		#Needed to allow any-length input
		return QValidator.Acceptable

	#def valueChanged(self, *args, **kwargs):
	#	x = (args[0] // self._increments) * self._increments
	#	if self.value() != x:
	#		self.setValue(x)
	#	print("PEPE")


	#def setValue(self, *args, **kwargs):

	#def stepBy(self, *args, **kwargs):
	#	print(args)



class InputConfig(ConfigWidget):
	def __init__(self, model_name, index, parent=None):
		super(InputConfig, self).__init__(model_name, index, parent)

		self.number = self.add(QLabel(str(index)))
		self.number.setStyleSheet("QLabel { font-size: 12pt }")

		self.monitor = self.add(QLabel())
		self.monitor.setStyleSheet("QLabel { font-size: 10pt }")
		self.monitor.setFixedWidth(100)
		self.monitor.setAutoFillBackground(True)

		self.enable_monitor = self.addwl(_("Monitor"), QCheckBox())
		self.enable_monitor.setChecked(True)

		modeCB = QComboBox()
		modeCB.setStyleSheet("QComboBox { font-size: 10pt }")
		self.mode = self.addwl(_("Mode"), modeCB)
		for labelIdx in MODE_ENABLED:
			self.mode.addItem(MODE_LABELS[labelIdx])
		self.mode.setCurrentIndex(MODE_NOTE) #Default value
		self.mode.currentIndexChanged.connect(self.on_param_value_changed)

		paramSB = QSpinBox()
		paramSB.setStyleSheet("QSpinBox { font-size: 10pt }")
		self.param =self.addwl(_("Param"), paramSB);
		self.param.valueChanged.connect(self.on_param_value_changed)
		#setWidgetBackground(self.param, Qt.black)
		#self.param.setToolTip(_("El rango para Notas y CC es de 0 a 127"))
		self.param.setRange(0, pow(2, 14)-1)
		
		channelSB = QSpinBox()
		channelSB.setStyleSheet("QSpinBox { font-size: 10pt }")
		self.channel = self.addwl(_("Channel"), channelSB)
		self.channel.setRange(0, 15)
		
		minSB = QSpinBoxHack()
		minSB.setStyleSheet("QSpinBoxHack { font-size: 10pt }")
		self.min = self.addwl(_("Min."), minSB)
		self.min.setRange(0, 127)
		maxSB = QSpinBoxHack()
		maxSB.setStyleSheet("QSpinBoxHack { font-size: 10pt }")
		self.max = self.addwl(_("Max."), maxSB)
		self.max.setRange(0, 127)
		#self.max.valueChanged.connect(self.on_max_value_changed)

		self.max.setValue(127)

		#TODO: On any change: save model? <- NO

	def show_feedback(self):
		#if self.enable_monitor.isChecked():	#Controlado antes de llamar esta funcion
		super().show_feedback()

	def load_model(self):
		model = self.model()
		self.channel.setValue(model.channel)
		self.mode.setCurrentIndex(model.mode)
		self.param.setValue(model.param)
		self.min.setValue(model.min)
		self.max.setValue(model.max)

	def save_model(self):
		model = self.model()
		model.channel = self.channel.value()
		model.mode = self.mode.currentIndex()
		model.param = self.param.value()
		model.min = self.min.value()
		model.max = self.max.value()

	def on_param_value_changed(self):
		#TODO: Shifter lock in to banks
		alertParam = False
		mode = self.mode.currentIndex()
		param = self.param.value()
		max_banks = config['global'].num_banks

		if (mode == MODE_NOTE or mode == MODE_CC or mode == MODE_PC) and param > 127:
			alertParam = True
			self.setAlert(_("Note/CC param {0} outside valid range 0-127").format(param))
		elif mode == MODE_SHIFTER and param >= max_banks:
			alertParam = True
			self.setAlert(_("Shifter param {0} outside bank range 0-{1}").format(param, max_banks-1))
		else:
			repeated = False
			if mode == MODE_SHIFTER:
				for i, w in enumerate(self.window().inputs):
					if self._index != i:
						if w.mode.currentIndex() == MODE_SHIFTER and w.param.value() == param:
							self.setAlert(_("Banco de shifter repetido ({0})").format(param))
							alertParam = True
							repeated = True
							break
			#print(self.window())

			if not repeated:
				self.setAlert(None)

		#HACK: Refresh everything just in case
		self.window().call_on_param_value_changed_on_inputs()

		en = mode != MODE_SHIFTER
		self.min.setEnabled(en)
		self.max.setEnabled(en)
		self.channel.setEnabled(en)

		self.min.setIncrement(127 if mode == MODE_NRPN else 1)
		self.max.setIncrement(127 if mode == MODE_NRPN else 1)


		stylesheetProp(self.param, "alert", alertParam)


	def show_value(self, value):
		self.monitor.setText("({0})".format(value))


class InputConfigCC(InputConfig):
	def __init__(self, model_name, index, parent=None):

		ad = QComboBox()
		ad.setStyleSheet("QComboBox {font-size: 10pt}")
		ad.addItems((_("Analog"), _("Digital")))
		self.analog = ad

		pt = QComboBox()
		pt.setStyleSheet("QComboBox {font-size: 10pt}")
		pt.addItems((_("Toggle"), _("Momentary")))
		self.toggle = pt		# Changes for regular input (pot, slider) and ultrasound config

		super().__init__(model_name, index, parent)
		self.addwl(_("A/D"), ad, 4)		# Changes for regular input (pot, slider) and ultrasound config
		self.addwl(_("Press"), pt, 6)		# Changes for regular input (pot, slider) and ultrasound config

		#After super __init__ is called
		ad.currentIndexChanged.connect(self.on_param_value_changed)
		ad.setCurrentIndex(1)

	def save_model(self):
		super().save_model()
		m = self.model()
		m.analog = self.analog.currentIndex() == 0
		m.toggle = self.toggle.currentIndex() == 0

	def load_model(self):
		super().load_model()
		m = self.model()
		self.analog.setCurrentIndex(0 if m.analog else 1)
		self.toggle.setCurrentIndex(0 if m.toggle else 1)

	def on_param_value_changed(self):
		super().on_param_value_changed()
		mode = self.mode.currentIndex()
		en = mode != MODE_SHIFTER
		self.analog.setEnabled(en)
		self.toggle.setEnabled(self.analog.currentIndex() != 0)		# 0 = Analog
		#self.toggle.setEnabled(en)


class InputConfigUS(InputConfig):
	def __init__(self, model_name, parent=None):

		self.dist_min = QSpinBox()
		self.dist_min.setStyleSheet("QSpinBox {font-size: 10pt}")
		max_uint14 = pow(2, 14)-1
		self.dist_min.setMaximum(max_uint14)
		self.dist_max = QSpinBox()
		self.dist_max.setStyleSheet("QSpinBox {font-size: 10pt}")
		self.dist_max.setMaximum(max_uint14)
		self.dist_max.setValue(max_uint14)

		super().__init__(model_name, 0, parent)
		self.number.setText("")
		self.mode.setCurrentIndex(MODE_OFF);
		self.dist_min = self.addwl(_("Min. Dist."), self.dist_min)
		self.dist_max = self.addwl(_("Max. Dist."), self.dist_max)

		self.mode.removeItem(self.mode.count()-1)

	def save_model(self):
		super().save_model()
		m = self.model() # type: InputDataUS
		m.dist_min = self.dist_min.value()
		m.dist_max = self.dist_max.value()

	def load_model(self):
		super().load_model()
		m = self.model() # type: InputDataUS
		self.dist_min.setValue(m.dist_min)
		self.dist_max.setValue(m.dist_max)

	def on_param_value_changed(self):
		super().on_param_value_changed()
		mode = self.mode.currentIndex()
		en = mode != MODE_SHIFTER
		self.dist_min.setEnabled(en)
		self.dist_max.setEnabled(en)


class Form(QFrame):
	outputs = []
	inputs = []
	input_us = None
	current_bank = 0

	_last_in_values = []

	testing = None
	def on_test_all_press(self):
		to_test = []
		value = self.test_all_velocity.value()
		for i in range(0, config['global'].num_outputs):
			self.outputs[i].save_model()
			m = self.outputs[i].model()
			to_test.append((m.channel, m.note))

		for tuple in to_test:
			midi_send((MIDI_NOTE_ON | tuple[0], tuple[1], value))

		self.testing = to_test

	def on_test_all_release(self):
		if not self.testing:
			return
		for tuple in self.testing:
			midi_send((MIDI_NOTE_OFF | tuple[0], tuple[1], 0))
		self.testing = None

	#def on_set_bank_channels(self):
	#	for i in self.inputs + self.outputs + [self.input_us]:
	#		i.channel.setValue(self.set_chan_channel.value())

	_reentry = 0
	def call_on_param_value_changed_on_inputs(self):
		if self._reentry > 0:
			return

		self._reentry += 1
		print("Refreshing alerts")

		for w in self.inputs:
			w.on_param_value_changed()

		self._reentry -= 1
		
	def __init__(self, parent=None):
		print("Form()  B Form init")
		super(Form, self).__init__(parent)

		print("Form()  2 Form set window title")
		self.setWindowTitle(TITLE + " " + VERSION)
		# Create widgets

		print("Form()  1 Move resize")

		self.move(24, 24)
		self.resize(1024, 600)

		print("Form() 13 Master layout")

		master_layout = QVBoxLayout()
		self.setLayout(master_layout)


		def addLabelWA(layout, text):		#Workaround for labels that resized big time
			lbl = QLabel(text)
			lbl.setStyleSheet("QLabel { font-weight: bold; font-size: 10pt }")
			#lbl.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
			layout.addWidget(lbl)
			

		############## TOP LAYOUT #############

		layout_top = QHBoxLayout()
		master_layout.addLayout(layout_top)

		print("Form() Memory widget")

		self.memory_widget = MemoryWidget(self)

		print("Form() Memory widget ok")

		self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Maximum)
		
		layout_htop = QVBoxLayout()
		layout_htop.addWidget(self.memory_widget)

		layout_apply = QVBoxLayout()
		#layout_top.addLayout(layout_apply)

		self.btn_apply = QPushButton(_("Apply"))
		self.btn_apply.setStyleSheet("QPushButton { font-size: 10pt }")
		self.btn_apply.setMinimumWidth(130)
		self.btn_apply.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
		self.btn_apply.pressed.connect(lambda: self.memory_widget.save_model())
		layout_apply.addStretch()
		layout_apply.addWidget(self.btn_apply)
		layout_apply.addStretch()
		layout_apply.setAlignment(Qt.AlignCenter)

		layout_htop.addLayout(layout_apply)
		
		layout_top.addLayout(layout_htop)
		#layout_top.setAlignment(self.memory_widget, Qt.AlignTop)
		layout_top.addStretch() # space between

		load_save_layout = QGridLayout()
		load_save_layout.setSizeConstraint(QLayout.SetMaximumSize)
		layout_top.addLayout(load_save_layout)
		lsh = GridHelper(load_save_layout)

		print("Form() logo.png")

		lsh.pic("assets/logo.png", spanx=2, align=Qt.AlignRight).newLine()

        #Sizes workaround
		#lsh_w = 384
		#lsh_w2 = lsh_w//2-2
		#lsh_w3 = lsh_w-16
		#lsh_w4 = lsh_w-4

		lsh_w = None
		lsh_w2 = None
		lsh_w3 = None
		lsh_w4 = None

		link = QLabel()
		link.setText(_("<a href=\"http://wiki.yaeltex.com.ar/index.php?title=Kilowhat\" style=\"color: yellow;\">Ayuda</a>"))
		link.setStyleSheet("QLabel { font-size: 10pt }")
		link.setTextInteractionFlags(Qt.TextBrowserInteraction)
		link.setTextFormat(Qt.RichText)
		link.setOpenExternalLinks(True)
		lsh.widget(link, spanx=2, align=Qt.AlignRight).newLine()
	
		lsh.label(_("Config file description"), spanx=2, align=Qt.AlignCenter).newLine()

		self.description = QLineEdit()
		#self.description.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Ignored)
		lsh.widget(self.description, spanx=2, width=lsh_w3).newLine()


		btn = QPushButton(_("Load file"))
		btn.setStyleSheet("QPushButton { font-size: 10pt }")
		btn.pressed.connect(self.on_load_file)
		btn.setIcon(QIcon("assets/load.png"))
		lsh.widget(btn, width=lsh_w2)

		btn = QPushButton(_("Save file"))
		btn.setStyleSheet("QPushButton { font-size: 10pt }")
		btn.setIcon(QIcon("assets/save.png"))
		btn.pressed.connect(self.on_save_file)
		lsh.widget(btn, width=lsh_w2)
		lsh.newLine()

		btn = QPushButton(_("Dump to Arduino"))
		btn.setStyleSheet("QPushButton { font-size: 10pt }")
		btn.setObjectName("DumpBtn")
		#btn.setIcon(QIcon("test.png"))
		btn.setIconSize(QSize(24,24))
		#btn.setStyleSheet("text-align: right;")
		btn.pressed.connect(self.on_dump_sysex)
		load_save_layout.addWidget(btn)
		lsh.widget(btn, spanx=2, width=lsh_w)
		lsh.newLine()

		self.button = QPushButton("DEBUG TEST")
		self.button.setStyleSheet("color: #8080ff")
		if DEBUG:
			master_layout.addWidget(self.button)
		self.button.clicked.connect(self.on_debug_test)

		widget_bank_line = PaintWidget()
		layout_bank_line = QHBoxLayout()
		widget_bank_line.setObjectName("BankLine")
		#widget_bank_line.setStyleSheet(".QWidget { border: 1px solid white }")
		
		widget_bank_line.setLayout(layout_bank_line)
		#master_layout.addLayout(layout_bank_line)
		master_layout.addWidget(widget_bank_line)

		self.tabs = QTabBar()
		self.tabs.setStyleSheet("QTabBar { font-size: 10pt }")
		self.tabs.setUsesScrollButtons(False)
		self.tabs.setBackgroundRole(QPalette.Dark)		#HACK: to hide bottom line
		#self.tabs.setForegroundRole(QPalette.Light)
		#self.tabs.setStyleSheet("QTabBar { bottomborder: 1px solid #ff0000; top: 0px; }")
		self.tabs.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
		layout_bank_line.addWidget(self.tabs)
		self.tabs.currentChanged.connect(self.on_change_tab_bank)
		self.refresh_tabs()
		layout_bank_line.addStretch(1)


		#################################################
		# Set all bank channels
		#################################################
		#set_chan_layout = QHBoxLayout()
		#set_chan_btn = QPushButton(_("Set bank channels"))
		#set_chan_btn.pressed.connect(self.on_set_bank_channels)
		#self.set_chan_channel = QSpinBox()
		#self.set_chan_channel.setValue(0)
		#self.set_chan_channel.setMinimum(0)
		#self.set_chan_channel.setMaximum(15)
		#set_chan_layout.addWidget(set_chan_btn)
		#set_chan_layout.addWidget(self.set_chan_channel)

		#layout_bank_line.addLayout(set_chan_layout)
		#################################################

		if 1: #tabs
			self.tabs_inout = QTabBar()
			# self.tabs_inout.setStyleSheet("QTabBar { font-size: 10pt }")
			self.tabs_inout.setStyleSheet("QTabBar { font-size: 10pt }")
			self.tabs_inout.setUsesScrollButtons(False)
			self.tabs_inout.setBackgroundRole(QPalette.Dark)		#HACK: to hide bottom line
			self.tabs_inout.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
			
			layout_bank_line.addWidget(self.tabs_inout)

			#section_layout = QHBoxLayout()
			section_splitter = QSplitter()
			section_splitter.setChildrenCollapsible(False)
			#section_splitter.setHandleWidth(10)
			section_splitter.setStyleSheet("QSplitter::handle { background-color: gray }");
			section_splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
			master_layout.addWidget(section_splitter)
			
			# section_splitter.addWidget(self.tabs_inout)
			self.tabs_inout.addTab(_("Inputs"))
			self.tabs_inout.addTab(_("Outputs"))
			self.tabs_inout.addTab(_("Distance sensor"))
			self.tabs_inout.currentChanged.connect(self.on_change_tab_inout)
			
			################################
			# Add UltraSonic input widgets #
			################################

			self.us_inputs_side = QFrame()
			inputs_side = self.us_inputs_side
			us_input_layout = QVBoxLayout()
			input_layout = us_input_layout
			inputs_side.setLayout(input_layout)
			section_splitter.addWidget(inputs_side)

			saw = QWidget()
			
			# Add UltraSonic widget
			addLabelWA(input_layout, _("Ultrasound input"))
			
			us_area = QScrollArea()
			lw = InputConfigUS('input_us', self)
			#config['banks'][bankIdx].input_cc
			#lw.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
			#lw.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Ignored)
			#lw.setBackgroundRole(QPalette.Dark)
			lw.setProperty("parity", "even")
			lw.setMinimumHeight(20)
			#input_layout.addWidget(lw)
			self.input_us = lw
			#Pre-config banks
			for bankIdx in range(MAX_BANKS):
				config['banks'][bankIdx].input_us[0].mode = MODE_OFF


			us_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
			us_area.setWidgetResizable(True)
			us_area.setWidget(lw)
			#us_area.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Maximum)
			# us_area.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.MinimumExpanding)
			us_input_layout.addWidget(us_area)
			us_input_layout.addSpacing(390)
			us_input_layout.addStretch()

			#####################
			# Add input widgets #
			#####################
			# Add CC widgets

			self.inputs_side = QFrame()
			inputs_side = self.inputs_side
			input_layout = QVBoxLayout()
			inputs_side.setLayout(input_layout)
			section_splitter.addWidget(inputs_side)
			
			addLabelWA(input_layout, _("Input #"))

			sa_layout = QVBoxLayout()
			sa_layout.setSizeConstraint(QLayout.SetMinimumSize)
			sa_layout.setSpacing(0)
			saw.setLayout(sa_layout)
			# saw.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

			ins_area = QScrollArea()
			ins_area.setWidgetResizable(True)
			ins_area.setWidget(saw)
			self.ins_area = ins_area
			input_layout.addWidget(ins_area)

			for i in range(0, MAX_INPUTS_CC):
				#For each config, pre-config banks
				for bankIdx in range(MAX_BANKS):
					config['banks'][bankIdx].input_cc[i].param = i

				lw = InputConfigCC('input_cc', i, self)
				lw.load_model()
				if i % 2 == 0:
					lw.setProperty("parity", "even")	#For stylesheets
				self.inputs.append(lw)
				self._last_in_values.append(-THRESHOLD_SELECT)
				sa_layout.addWidget(lw)

			######################
			# Add output widgets #
			######################

			self.outputs_side = QFrame()
			outputs_side = self.outputs_side
			output_layout = QVBoxLayout()
			outputs_side.setLayout(output_layout)
			section_splitter.addWidget(outputs_side)


			# Test grid: removed
			#grid = QGridLayout()
			#grid.setSpacin#g(0)
			#gridw = QWidget()
			#gridw.setLayout(grid)
			#gridw.setFixedSize(160, 160)
			## gridw.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
			#for x in range(16):
			#	for y in range(16):
			#		gbtn = QPushButton()
			#		gbtn.setFixedSize(10, 10)
			#		grid.addWidget(gbtn, x, y)
			#output_layout.addWidget(gridw)



			addLabelWA(output_layout, _("Output #"))

			saw = QWidget()
			sa_layout = QVBoxLayout()
			#sa_layout.setSizeConstraint(QLayout.SetMinimumSize)
			sa_layout.setSpacing(0)
			saw.setLayout(sa_layout)
			saw.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

			outs_area = QScrollArea()
			outs_area.setWidgetResizable(True)
			outs_area.setWidget(saw)
			self.outs_area = outs_area
			output_layout.addWidget(outs_area)

			#################################################
			# Test all segment
			#################################################
			test_all_widget = QWidget()
			test_all_widget.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
			test_all_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
			test_all_layout = QHBoxLayout()
			#test_all_layout.addStretch()
			test_all_btn = QPushButton(_("Test all"))
			test_all_btn.setStyleSheet("QPushButton {font-size: 10pt}");
			#test_all_btn.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
			#test_all_btn.setFixedWidth(100)
			test_all_btn.pressed.connect(self.on_test_all_press)
			test_all_btn.released.connect(self.on_test_all_release)
			test_all_layout.addWidget(test_all_btn)
			lbl_test = QLabel(_("with velocity"))
			lbl_test.setStyleSheet("QLabel {font-size: 10pt}");
			test_all_layout.addWidget(lbl_test)

			self.test_all_velocity = QSpinBox()
			self.test_all_velocity.setStyleSheet("QSpinBox {font-size: 10pt}");
			self.test_all_velocity.setValue(64)
			self.test_all_velocity.setMinimum(0)
			self.test_all_velocity.setMaximum(0x7f)
			test_all_btn.setObjectName("TestAll")
			#self.test_all_velocity.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

			test_all_layout.addWidget(self.test_all_velocity)

			#sa_layout.addLayout(test_all_layout)
			sa_layout.addWidget(test_all_widget)
			test_all_widget.setLayout(test_all_layout)
			#################################################

			for i in range(0, MAX_OUTPUTS):
				#For each config, pre-config banks
				for bankIdx in range(MAX_BANKS):
					config['banks'][bankIdx].output[i].note = i

				lw = OutputConfig('output', i)
				lw.load_model()
				#lw.param.setValue(i)
				if i % 2 == 0:
					lw.setProperty("parity", "even")	#For stylesheets
				self.outputs.append(lw)
				sa_layout.addWidget(lw)


			###############

			section_splitter.setSizes([self.width()/2] * 2)
			
			#Default view: inputs
			self.change_views_inout_tab(0)
		else: #old code
			#section_layout = QHBoxLayout()
			section_splitter = QSplitter()
			section_splitter.setChildrenCollapsible(False)
			#section_splitter.setHandleWidth(10)
			section_splitter.setStyleSheet("QSplitter::handle { background-color: gray }");
			section_splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
			master_layout.addWidget(section_splitter)

			#####################
			# Add input widgets #
			#####################

			inputs_side = QFrame()
			input_layout = QVBoxLayout()
			inputs_side.setLayout(input_layout)
			section_splitter.addWidget(inputs_side)

			saw = QWidget()

			# Add US widget
			addLabelWA(input_layout, _("Ultrasound input"))
			
			us_area = QScrollArea()
			lw = InputConfigUS('input_us', self)
			#config['banks'][bankIdx].input_cc
			#lw.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
			#lw.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Ignored)
			#lw.setBackgroundRole(QPalette.Dark)
			lw.setProperty("parity", "even")
			lw.setMinimumHeight(20)
			#input_layout.addWidget(lw)
			self.input_us = lw
			#Pre-config banks
			for bankIdx in range(MAX_BANKS):
				config['banks'][bankIdx].input_us[0].mode = MODE_OFF


			us_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
			us_area.setWidgetResizable(True)
			us_area.setWidget(lw)
			us_area.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Maximum)
			input_layout.addWidget(us_area)


			# Add CC widgets

			addLabelWA(input_layout, _("Input #"))

			sa_layout = QVBoxLayout()
			sa_layout.setSizeConstraint(QLayout.SetMinimumSize)
			sa_layout.setSpacing(0)
			saw.setLayout(sa_layout)
			saw.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

			ins_area = QScrollArea()
			ins_area.setWidgetResizable(True)
			ins_area.setWidget(saw)
			self.ins_area = ins_area
			input_layout.addWidget(ins_area)

			for i in range(0, MAX_INPUTS_CC):
				#For each config, pre-config banks
				for bankIdx in range(MAX_BANKS):
					config['banks'][bankIdx].input_cc[i].param = i

				lw = InputConfigCC('input_cc', i, self)
				lw.load_model()
				if i % 2 == 0:
					lw.setProperty("parity", "even")	#For stylesheets
				self.inputs.append(lw)
				self._last_in_values.append(-THRESHOLD_SELECT)
				sa_layout.addWidget(lw)

			######################
			# Add output widgets #
			######################

			outputs_side = QFrame()
			output_layout = QVBoxLayout()
			outputs_side.setLayout(output_layout)
			section_splitter.addWidget(outputs_side)


			# Test grid: removed
			#grid = QGridLayout()
			#grid.setSpacin#g(0)
			#gridw = QWidget()
			#gridw.setLayout(grid)
			#gridw.setFixedSize(160, 160)
			## gridw.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
			#for x in range(16):
			#	for y in range(16):
			#		gbtn = QPushButton()
			#		gbtn.setFixedSize(10, 10)
			#		grid.addWidget(gbtn, x, y)
			#output_layout.addWidget(gridw)



			addLabelWA(output_layout, _("Output #"))

			saw = QWidget()
			sa_layout = QVBoxLayout()
			#sa_layout.setSizeConstraint(QLayout.SetMinimumSize)
			sa_layout.setSpacing(0)
			saw.setLayout(sa_layout)
			saw.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

			outs_area = QScrollArea()
			outs_area.setWidgetResizable(True)
			outs_area.setWidget(saw)
			self.outs_area = outs_area
			output_layout.addWidget(outs_area)

			#################################################
			# Test all segment
			#################################################
			test_all_widget = QWidget()
			test_all_widget.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
			test_all_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
			test_all_layout = QHBoxLayout()
			#test_all_layout.addStretch()
			test_all_btn = QPushButton(_("Test all"))
			test_all_btn.setStyleSheet("QPushButton {font-size: 10pt}");
			#test_all_btn.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
			#test_all_btn.setFixedWidth(100)
			test_all_btn.pressed.connect(self.on_test_all_press)
			test_all_btn.released.connect(self.on_test_all_release)
			test_all_layout.addWidget(test_all_btn)
			lbl_test = QLabel(_("with velocity"))
			lbl_test.setStyleSheet("QLabel {font-size: 10pt}");
			test_all_layout.addWidget(lbl_test)

			self.test_all_velocity = QSpinBox()
			self.test_all_velocity.setStyleSheet("QSpinBox {font-size: 10pt}");
			self.test_all_velocity.setValue(64)
			self.test_all_velocity.setMinimum(0)
			self.test_all_velocity.setMaximum(0x7f)
			test_all_btn.setObjectName("TestAll")
			#self.test_all_velocity.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

			test_all_layout.addWidget(self.test_all_velocity)

			#sa_layout.addLayout(test_all_layout)
			sa_layout.addWidget(test_all_widget)
			test_all_widget.setLayout(test_all_layout)
			#################################################

			for i in range(0, MAX_OUTPUTS):
				#For each config, pre-config banks
				for bankIdx in range(MAX_BANKS):
					config['banks'][bankIdx].output[i].note = i

				lw = OutputConfig('output', i)
				lw.load_model()
				#lw.param.setValue(i)
				if i % 2 == 0:
					lw.setProperty("parity", "even")	#For stylesheets
				self.outputs.append(lw)
				sa_layout.addWidget(lw)


			###############

			section_splitter.setSizes([self.width()/2] * 2)
		# end in/out config

		self.refresh_in_outs()

		self.txt_log = QTextEdit()
		self.txt_log.setReadOnly(True)
		self.txt_log.setMaximumHeight(120)
		master_layout.addWidget(self.txt_log)
		self.txt_log.append(_("Welcome to Kilowhat!"))
		#self.txt_log.append(">CWD>")
		#self.txt_log.append(os.getcwd())
		#self.txt_log.append(">FD>")
		#self.txt_log.append(os.path.dirname(os.path.realpath(__file__)))
                
		timer = QTimer(self)
		timer.timeout.connect(self.poll_in)
		timer.start(POLL_INTERVAL)

		self.load_model()		# Load defaults in case automatic file loading fails
		if os.path.isfile(FILE_AUTOMATIC):
			self.load_file(FILE_AUTOMATIC, True)

		with open('style.css', 'r') as style_file:
			self.setStyleSheet(style_file.read())

	def on_change_tab_bank(self):
		if self.current_bank != self.tabs.currentIndex():
			self.current_bank = self.tabs.currentIndex()
			print(self.current_bank)
			with wait_cursor():
				self.change_views_bank(self.current_bank)
	
	def change_views_bank(self, bankIdx):
		self.save_model()

		for w in [self.input_us] + self.inputs + self.outputs:
			w.bank = bankIdx

		self.load_model()

	def on_change_tab_inout(self):
		if self.current_inout_tab != self.tabs_inout.currentIndex():
			self.current_inout_tab = self.tabs_inout.currentIndex()
			print("Current IN/OUT tab: %i"%self.current_inout_tab)
			with wait_cursor():
				self.change_views_inout_tab(self.current_inout_tab)

	def change_views_inout_tab(self, bankIdx):
		if bankIdx==0:
			self.inputs_side.show() #load inputs 
			self.outputs_side.hide()
			self.us_inputs_side.hide()
		elif bankIdx==1:
			self.inputs_side.hide()
			self.outputs_side.show() #load outputs 
			self.us_inputs_side.hide()
		else:
			self.inputs_side.hide()
			self.outputs_side.hide()
			self.us_inputs_side.show() #load ultrasonic

	def refresh_tabs(self):
		nbanks = config['global'].num_banks
		for i in range(self.tabs.count(), nbanks):
			self.tabs.addTab(_("Bank {0}").format(i))

		while self.tabs.count() > nbanks:
			self.tabs.removeTab(nbanks)


	def refresh_in_outs(self):
		gd = config['global'] # type: GlobalData
		for i, w in enumerate(self.inputs):
			w.setVisible(i < gd.num_inputs_norm)
			w.parent().adjustSize()

		for i, w in enumerate(self.outputs):
			w.setVisible(i < gd.num_outputs)
			w.parent().adjustSize()



	def save_model(self):
		config['file']['desc'] = self.description.text()
		#Fixme: NUM BANKS ETC.

		for w in [self.memory_widget, self.input_us] + self.inputs + self.outputs:
			w.save_model()

	def on_dump_sysex(self):
		self.save_model()
		self.txt_log.setText(_("Starting Dump"))

		stuff = (
			("Ultrasound", [self.input_us]),
			("Input", self.inputs),
			("Output", self.outputs)
		)
		warnings = 0
		errors = 0

		for name, lst in stuff:
			for i, w in enumerate(lst):
				if w.alert_txt is not None:
					self.txt_log.append("{0} #{1}: {2}".format(name, i, w.alert_txt))
					errors += 1

				# Check redundancies for warnings
				# for j, w2 in enumerate(lst):
				# 	if w.alert_txt is not None:
				# 		if(w,)
				# 		self.txt_log.append("{0} #{1}: {2}".format(name, i, w.alert_txt))
				# 		warnings += 1



		if errors != 0:
			QMessageBox.critical(self, _("Dump error"), _("{0} errors trying to dump.").format(errors))
			self.txt_log.append(_("<b>Dump aborted</b>"))
			return
		elif warnings != 0:
			if QMessageBox.warning(self, _("Dump error"), _("{0} warnings trying to dump, continue anyway?").format(warnings), QMessageBox.Yes, QMessageBox.No) != QMessageBox.Yes:
				self.txt_log.append(_("<b>Dump aborted</b>"))
				return
				
		send_sysex_dump()
		self.txt_log.append(_("Dump sent"))

	def on_load_file(self):
		# TODO: Check if it was saved!
		fileName, __ = QFileDialog.getOpenFileName(self, _("Open kmgui configuration file"),  filter = _("kmgui file (*.kmgui)"))
		if not fileName:
			return
		self.load_file(fileName)


	def closeEvent(self, event):
		self.save_file(FILE_AUTOMATIC)
		event.accept() 	# let the window close

	def load_model(self):
		self.description.setText(config['file']['desc'])
		for w in [self.memory_widget, self.input_us] + self.inputs + self.outputs:
			w.load_model()

	def load_file(self, fileName, automatic = False):
		try:
			file = open(fileName, 'rb')
			global config
			config2 = pickle.load(file)
			file_ver = config2['file_ver'] if 'file_ver' in config2 else 0
			if file_ver != PROTOCOL_VERSION:
				if not automatic:
					QMessageBox.warning(self, _('Error'),
										_('Invalid version of kmgui configuration file "{0}"\nVersion {1} should be {2} ')
										.format(fileName, file_ver, PROTOCOL_VERSION))
			else:
				config = config2
				self.current_bank = 0
				self.current_inout_tab = 0
				self.load_model()
				self.refresh_tabs()
				self.refresh_in_outs()
			file.close()
		except Exception as e:
			QMessageBox.warning(self, _('Error'), _('Error opening kmgui configuration file "{0}"\n{1}').format(fileName, e))

	def save_file(self, fileName):
		try:
			if 1:
				file = open(fileName, 'wb')
				self.save_model()
				pickle.dump(config, file)
				file.close()
		except Exception as e:
			QMessageBox.warning(self, _('Error'), _('Error writing kmgui configuration file "{0}"\n{1}').format(fileName, e))

	def on_save_file(self):
		# TODO: Check if it was saved!
		fileName, __ = QFileDialog.getSaveFileName(self, _("Save kmgui configuration file"),  filter = _("kmgui file (*.kmgui)"))
		if not fileName:
			return

		try:
			self.save_file(fileName)
		finally:
			self.save_file(FILE_RECOVER)

	def processCommand(self, cmd):

		print("Received command")
		print(cmd)

		#TODO: make packets static once
		if cmd == sysex.make_sysex_packet(sysex.CONFIG_ACK, []):
			self.txt_log.append(_("ACK Received. Kilomux connected"))

		if cmd == sysex.make_sysex_packet(sysex.DUMP_OK, []):
			self.txt_log.append(_("Dump OK"))

		type_chn, param, value = cmd
		cmd_type = type_chn & 0xf0
		chn = type_chn & 0xf

		target = None
		if chn == MONITOR_CHAN_US:
			target = self.input_us
		else:
			#if (type == MIDI_NOTE_ON or type == MIDI_CC) and param < len(self.inputs) and value > 0:
			if param < len(self.inputs):
				if cmd_type == MIDI_NOTE_OFF:	#Force note-off to value = 0
					value = 0

				target = self.inputs[param]

		if target is not None:
			target.show_value((_("CC") if cmd_type == MIDI_CC else _("Note")) + " " + str(value))
			last_value = self._last_in_values[param]
			if abs(last_value - value) > THRESHOLD_SELECT:
				self._last_in_values[param] = value
				# sarea = self.ins_area

				if target.enable_monitor.isChecked() and target.mode.currentIndex() != MODE_OFF:
					target.show_feedback()
					ancestor = target.parent()
					while ancestor is not None:
						if isinstance(ancestor, QScrollArea):
							break
						ancestor = ancestor.parent()

					if ancestor is not None:
						ancestor.ensureWidgetVisible(target)
						ancestor.horizontalScrollBar().setValue(0)

	def poll_in(self):
		# TODO: freeze ctl
		try:
			msg = midiin.get_message()
			while msg:
				self.processCommand(msg[0])
				msg = midiin.get_message()
		except Exception as e:
			print(e)
			self.txt_log.append(_("ERROR IN: ") + str(e))

	prev_selected = None
	def select(self, widget):
		if self.prev_selected is not None:
			self.prev_selected.unselect()
		widget.select()
		self.prev_selected = widget


	def on_debug_test(self):
		target = self.inputs[16]
		target.show_feedback()
		target.show_value(_("CC") + " " + str(123))
		self.ins_area.ensureWidgetVisible(target)
		self.ins_area.horizontalScrollBar().setValue(0)
		self.select(self.inputs[15])
		pass

print("Starting App")
#if __name'' == '''main''':
# Create the Qt Application
app = QApplication(sys.argv)

print("Set Icon")
app.setWindowIcon(QIcon("assets/icon.png"))

def set_my_font():
        try:
                font_id = QFontDatabase.addApplicationFont("./assets/Novecento WideLight.otf")
                font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
                print(font_family)
                font = QFont(font_family, 12)

                font.setStyleStrategy(QFont.PreferAntialias)	#
                QApplication.setFont(font)

                app.setStyleSheet("QWidget { font-family: '" + font_family + "' }")
        except Exception as e:
                print("Error loading font")
                print(e)


#Workaround for task-bar icon in windows
import platform
if platform.system() == "Windows":
	print("Win workaround task-bar icons")
	import ctypes
	myappid = 'mycompany.myproduct.subproduct.version' # arbitrary string
	ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)


print("Creating form")

# Create and show the form
form = Form()
#form.resize(1024, 600)
print("Form created")

print("fix combox")
#Workaround for very small combo boxes
def fix_combos(x):
	for w in x.children():
		#print(w)  
		if isinstance(w, QComboBox):
			w.view().setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Ignored) #.setSizeAdjustPolicy(QComboBox.AdjustToContents)
		#if isinstance(w, QWidget):
			#w.adjustSize()
		fix_combos(w)
fix_combos(form)
print("Combos fixed")

print("Setting font")
set_my_font()

print("Show form")
form.showMaximized()

print("Run app")
# Run the main Qt loop
sys.exit(app.exec_())
