###################################################################################
# Original code by Martin Sebastian Wain for YAELTEX - 2016
# Revisions by Hernan Ordiales and Franco Grassano - 2016/2017
###################################################################################

import sys
import datetime
import os
import configparser

# Debug mode: python kilowhat.py -d
DEBUG = False
#print(sys.argv)
if len(sys.argv) >= 2 and sys.argv[1] == "-d":
    DEBUG = True

if not DEBUG:
    sys.stdout = open("kwt_log.txt", "a", 4)
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
_ = _            #WORKAROUND: _ is globally installed by lang

from model import *
import memory

# General
TITLE = "Kilowhat"
VERSION = "v0.9"

# User interface
COLOR_TIMEOUT = 500                        # ms. Background coloring timeout

# Midi
POLL_INTERVAL = 10                        # ms. Midi in polling interval
THRESHOLD_SELECT = 3                    # Delta threshold for selecting (coloring background and ensuring is visible in scroll area)
MONITOR_CHAN_US = 15                    # Ultra sound channel monitoring

# Files
PROTOCOL_VERSION = 1                    # For file save/load & EEPROM validation

FILE_AUTOMATIC = "automatic.kwt"
FILE_RECOVER = "recover.kwt"


# Combo box indexes
LED_OUTPUT_NORMAL = 0
LED_OUTPUT_MATRIX = 1

import plat
form = None
configFile = configparser.ConfigParser()
configFilePath = r'ioconfig.txt'
configFile.readfp(open(configFilePath))

miniblock = configFile.get('YTX Config', 'miniblock')
miniblock = 1 if miniblock == "yes" else 0

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

midiin.ignore_types(False, True, True)        # Sysex enabled

 # 0x80     Note Off
 #   0x90     Note On
 #   0xA0     Aftertouch
 #   0xB0     Continuous controller
 #   0xC0     Patch change
 #   0xD0     Channel Pressure
 #   0xE0     Pitch bend
 #   0xF0     Sys ex (non-musical commands)
MIDI_NOTE_OFF           = 0x80
MIDI_NOTE_ON            = 0x90
MIDI_CC                 = 0xb0
MIDI_PROGRAM_CHANGE     = 0xc0

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
            print("Sleep 0.5 seg")
            time.sleep(0.5)
    except Exception as e:
        print("Exception", e)


# TODO: stuff is a list of a list with widgets, layouts and tuples for cellspan (w/l, spanx, spany)
#def grid_create(grid:QGridLayout, stuff):
#    for row in stuff:
#        for elem in row:
#            if isinstance(elem, QWidget):
#                grid.addWidget(elem)

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
        if width is not None:
            w.setFixedWidth(width)
        self._grid.addWidget(w, self._y, self._x, spany, spanx, align)
        if(w.metaObject().className() == "QSpinBox"):    
            w.setFixedHeight(25)
        
        w.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
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

class PaintWidget(QWidget):
    def paintEvent(self, *args, **kwargs):
        o = QStyleOption()
        o.initFrom(self)
        p = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, o, p, self)

    def __init__(self, parent=None):
        super().__init__(parent)



class MemoryWidget(QWidget):
    firstTimePorts = True
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
        self.output_matrix.setStyleSheet("QComboBox { padding-left: 5px; font-size: 10pt }")
        self.hardware = QComboBox()
        self.hardware.setStyleSheet("QComboBox { font-size: 10pt }")
        self.banks = QSpinBox()
        self.banks.setStyleSheet("QSpinBox { font-size: 10pt }")
        self.ins = QSpinBox()
        self.ins.setStyleSheet("QSpinBox { font-size: 10pt }")
        self.outs = QSpinBox()
        self.outs.setStyleSheet("QSpinBox { font-size: 10pt }")
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.btn_apply = QPushButton(_("Apply changes"))
        self.btn_apply.setStyleSheet("QPushButton { font-size: 10pt; }")
        
        self.midi_thruCB = QCheckBox(_("<- MIDI THRU ->"))
        self.midi_thruCB.setStyleSheet("QCheckBox { font-size: 10pt }")
        
        
        mem_layout = QVBoxLayout()
        
        self.label_config = QLabel(_("General configuration"))
        self.label_config.setStyleSheet("QLabel { font-size: 12pt ; padding-bottom: 5px; border-bottom: 1px solid #505050; }")
        self.label_config.setAlignment(Qt.AlignLeft)
        
        mem_layout.addWidget(self.label_config)
        mem_layout.addSpacing(10)
        
        grid = QGridLayout()
        grid.setObjectName("MemWidget")
        grid.setHorizontalSpacing(16)
        
        mem_layout.addLayout(grid)
        mem_layout.addWidget(self.label_config)
        
        self.setLayout(mem_layout)
        h = GridHelper(grid)

        #Workaround for very small combo boxes
        cmi.view().setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Ignored) #.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        cmo.view().setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Ignored) #.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        tiny = 112        # FIXME: this is not a great way, but layouts are being dicks

        small = None
        h.label(_("MIDI ports")).widget(cmi, spanx=2, width=tiny).widget(cmo, spanx=1, width=tiny)\
            .label(_("Set banks")).widget(self.banks, width=tiny)\
            .newLine()
        h.label(_(" ")).label(_(" ")).widget(self.midi_thruCB, spanx=2, width=small).label(_("Set inputs")).widget(self.ins, width=tiny).newLine()
        h.label(_(" ")).widget(self.btn_reload_midi, spanx=3, width=small).label(_("LEDS mode")).widget(self.output_matrix, spanx=3, width=tiny).newLine()
        h.label(_("Hardware")).widget(self.hardware, spanx=3, width=small).label(_("Set outputs")).widget(self.outs, width=tiny).newLine()
        h.label(_(" ")).label(_(" ")).label(_(" ")).label(_(" ")).widget(self.btn_apply, spanx=2, width=small).newLine()       
        
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
        self.btn_apply.pressed.connect(lambda: self.save_model())
        self.midi_thruCB.clicked.connect(self.on_midi_thru_press)

        # Reset (TODO: done by the Form or here?)
        print("MemoryWidget() reset")
        self.on_param_value_changed()
        self.reopen_ports()

    def reload_midi_ports(self):
        global form
        print("Reloading MIDI ports")
        form.txt_log.clear()
        form.midi_monitor.clear()
        form.midi_monitor.append(_("MIDI Monitor")) 
        form.txt_log.append(_("Welcome to Kilowhat!"))
        form.config_modeCB.setChecked(False)
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
                self.cmi.addItem(_("I{0}: {1}").format(i, port))
        print("midiin ports ", ports)

        ports = midiout.get_ports()
        if ports:
            for i, port in enumerate(ports):
                self.cmo.addItem(_("O{0}: {1}").format(i, port))
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
        form.midi_monitor.clear()
        form.midi_monitor.append(_("MIDI Monitor")) 
        midi_send(sysex.make_sysex_packet(sysex.EXIT_CONFIG, []))
        self.reopen_ports()
        #Send Sysex - CONFIG_MODE
        pNameIn = midiin.get_port_name(abs(index))
        pNameOut = midiout.get_port_name(abs(index))
        if not pNameIn == pNameOut: 
            #form.midi_monitor.append("Send CONFIG")
            midi_send(sysex.make_sysex_packet(sysex.CONFIG_MODE, []))
        else:
            #form.midi_monitor.append("First Time")
            self.firstTimePorts = False

    def raise_changed_memory_event(self):
        with wait_cursor():
            self.parent().refresh_tabs()
            self.parent().refresh_in_outs()
            pass
     
    def on_midi_thru_press(self):
        global form
        if self.midi_thruCB.isChecked():
            form.midi_thru = True
            return
        else:
            form.midi_thru = False
            return
            
    def on_param_value_changed(self):
        print("MemoryWidget() on_param_value_changed")

        mem = self.hardware.itemData(self.hardware.currentIndex())
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
        lambda: self.save_model()

    def model(self) -> GlobalData:
        return config['global']

    def load_model(self):
        model = self.model()

        self.output_matrix.setCurrentIndex(config['global'].output_matrix)

        # Workaround: Temporary!
        self.banks.setMaximum(10000)
        self.ins.setMaximum(10000)
        self.outs.setMaximum(10000)

        self.hardware.setCurrentIndex(self.hardware.findData(model.memory_mode))
        self.banks.setValue(model.num_banks)
        self.ins.setValue(model.num_inputs_norm)
        self.outs.setValue(model.num_outputs)

        self.on_param_value_changed()    #This will recalculate maximums

        #TODO: if necessary cue  main widget to rebuild tabvs etc

    def save_model(self):
        global form
        model = self.model()
        config['global'].output_matrix = self.output_matrix.currentIndex()
        model.hardware_mode = self.hardware.itemData(self.hardware.currentIndex())
        model.num_banks = self.banks.value()
        model.num_inputs_norm = self.ins.value()
        model.num_outputs = self.outs.value()
        self.raise_changed_memory_event()
        max_banks = config['global'].num_banks
        
        for i, w in enumerate(form.inputs): 
            w.on_param_value_changed()
            
        for i, w in enumerate(form.outputs): 
            w.on_param_value_changed()
            
        #TODO: cue main widget to rebuild tabs and such
        #TODO: cue main widget to rebuild tabs and such
 
    def copy_values_from(self, origin):
        raise Exception("Needs to be implemented")


class ConfigWidget(QWidget):
    alert_txt = None
    multiple_edition_mode = False
    _first_time = True
    
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
        self.h_layout.insertWidget(idx, w, 1)
        if isinstance(self, InputConfigUS):
            w.installEventFilter(self)
        return w

    def addwl(self, label, w, idx = -1):
        idx = self.h_layout.count() if idx < 0 else idx
        self.add(w, idx)
        lbl = QLabel(label, self)
        lbl.setStyleSheet("QLabel {font-size: 10pt}")
        self.add(lbl, idx).setAlignment(Qt.AlignRight | Qt.AlignCenter)
            
        if isinstance(self, InputConfigUS):
            w.installEventFilter(self)
        return w

    def eventFilter(self, obj, ev):
        global form
        if ev.type() == QEvent.MouseButtonPress or ev.type() == QEvent.FocusIn:
            modifiers = QApplication.keyboardModifiers()
            if modifiers == Qt.ShiftModifier:
                # form.txt_log.append("SHFT")
                form.multiple_edition_mode = True
                form.multiple_select_shft(self)
            elif modifiers == Qt.ControlModifier:
                # form.txt_log.append("CTRL")
                form.multiple_edition_mode = True
                form.multiple_select_ctrl(self)
            else:
                form.select(self)
        return False

    def copy_values_from(self, origin, value="all"):   
        raise Exception("Not implemented. Must be implemented in a subclass")
             
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
        
        self.lbl_alert.setVisible(False)
        v_layout.addWidget(self.lbl_alert)

        self.setLayout(v_layout)

        timer = QTimer(self)
        timer.setInterval(COLOR_TIMEOUT)
        timer.setSingleShot(True)
        timer.timeout.connect(self.hide_feedback)
        self._color_timer = timer

        self.setAutoFillBackground(True)
        
        #self.setMinimumHeight(40)
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
        if not isinstance(self, InputConfigUS):
            stylesheetProp(self, "selection", True)
            self.setStyleSheet(self.styleSheet())
        # self.setFocus()
    
    def update_grouped_widgets(self, value):
        """
            Update all the selected widgets with the same values
            Multiple selection mode
        """
        global form
        if form and form.multiple_edition_mode:
            # form.txt_log.append("Updating * %s * in all widgets (copying values)"%value)
            form.multiple_select_copy_values(self, value)

class OutputConfig(ConfigWidget):

    current_test = None

    def __init__(self, model_name, index, parent=None):
        super(OutputConfig, self).__init__(model_name, index, parent)

        number = self.add(QLabel(str(index)))
        number.setStyleSheet("QLabel { font-size: 12pt }")

        number.installEventFilter(self)

        self.test = self.add(QPushButton(_("Test")))
        self.test.setStyleSheet("QPushButton { font-size: 9pt; margin: 2px; padding: 2px }")
        self.test.setFixedWidth(80)
        self.test.setFixedHeight(22)
        #self.test.setAlignment(Qt.AlignVCenter)
        self.test.pressed.connect(self.on_test_press)
        self.test.released.connect(self.on_test_release)
        #self.monitor = add(QLabel())
        #self.monitor.setFixedWidth(60)

        #self.test.installEventFilter(self)

        #self.da = addwl(_("D/A"), QCheckBox())
        #self.mode = addwl(_("Mode"), QComboBox())
        #self.mode.addItems((_("Note"), _("CC"), _("NRPN")))

        self.h_layout.addSpacing(20)
        
        self.shifter = self.addwl(_("Shifter"), QCheckBox())
        self.shifter.setChecked(False)
        if not miniblock:
            self.shifter.stateChanged.connect(self.on_param_value_changed)
            self.shifter.stateChanged.connect(lambda: self.update_grouped_widgets("shifter") )
        else:
            self.shifter.toggled.connect(self.checkbox_disabled)
            
        self.h_layout.addSpacing(-50)
        
        noteSB = QSpinBox()
        noteSB.setStyleSheet("QLabel { font-size: 10pt }")
        self.param = self.addwl(_("Param"), noteSB)
        self.param.setRange(0, 127)
        self.param.valueChanged.connect(self.on_param_value_changed)
        
        self.h_layout.addSpacing(10)
        
        chanSB = QSpinBox()
        chanSB.setStyleSheet("QLabel { font-size: 10pt }")
        self.channel = self.addwl(_("Channel"), chanSB)
        self.channel.setRange(1, 16)
        self.channel.valueChanged.connect(lambda: self.update_grouped_widgets("channel") )
        
        self.h_layout.addSpacing(50)
        self.blink = self.addwl(_("Intermitent"), QCheckBox())
        self.blink.stateChanged.connect(self.on_param_value_changed)
        self.blink.stateChanged.connect(lambda: self.update_grouped_widgets("blink"))
        
        self.h_layout.addSpacing(-60)
        minSB = QSpinBox()
        minSB.setStyleSheet("QLabel { font-size: 10pt }")
        self.min = self.addwl(_("Min."), minSB)
        self.min.setRange(0, 127)
        self.min.valueChanged.connect(lambda: self.update_grouped_widgets("min") )

        maxSB = QSpinBox()
        maxSB.setStyleSheet("QLabel { font-size: 10pt }")
        self.max = self.addwl(_("Max."), maxSB)
        self.max.setRange(0, 127)
        self.max.setValue(127)
        self.max.valueChanged.connect(lambda: self.update_grouped_widgets("max") )

    def checkbox_disabled(self):
        if self.shifter.isChecked():
            self.shifter.setChecked(False)
            return
        else:
            self.shifter.setChecked(False)
            return
            
    def on_param_value_changed(self):
        global form
        glob = config['global'];
        alertParam = False
        repeated = False
        is_shifter = self.shifter.isChecked()
        param = self.param.value()
        max_banks = config['global'].num_banks
        
        if self._first_time:
            self._first_time = False
            return
        
        if is_shifter and max_banks == 1:
            alertParam = True
            self.setAlert(_("There is no use for a shifter, if you only have one bank").format(param, max_banks-1))        
        elif is_shifter and param >= max_banks:
            alertParam = True
            self.setAlert(_("Shifter param {0} outside bank range 0-{1}").format(param, max_banks-1))
        else:
            if is_shifter:
                repeated = False
                for bankIdx in range(MAX_BANKS):
                    config['banks'][bankIdx].output[self._index].shifter = True                         # si es shifter en un banco, lo es en todos
                    config['banks'][bankIdx].output[self._index].param = param                               # copiar parametro de shifter en todos los bancos

                for i, w in enumerate(self.window().outputs):
                    if self._index != i and i < glob.num_outputs:
                        if w.shifter.isChecked() and w.param.value() == param:
                            self.setAlert(_("Shifter param repeated({0})").format(param))
                            w.setAlert(_("Shifter param repeated({0})").format(param))
                            alertParam = True
                            repeated = True  
                            w.alertParam = True
                            w.repeated = True  
                            stylesheetProp(w.param, "alert", w.alertParam)
                        else:   
                            w.alertParam = False
                            w.repeated = False
                            stylesheetProp(w.param, "alert", w.alertParam)
                            w.setAlert(None)
            else:
                for bankIdx in range(MAX_BANKS):
                    if config['banks'][bankIdx].output[self._index].shifter == True:
                        config['banks'][bankIdx].output[self._index].shifter = False
                            
        if not repeated and not alertParam:
            self.setAlert(None)
            
        #HACK: Refresh everything just in case
        #self.window().call_on_param_value_changed_on_outputs()
        
        en = self.blink.isChecked() and (not self.shifter.isChecked())
        self.min.setEnabled(en)
        self.max.setEnabled(en)
        
        en = not self.shifter.isChecked()
        self.channel.setEnabled(en)
        
        stylesheetProp(self.param, "alert", alertParam)
        
    def load_model(self):
        model = self.model()
        self.param.setValue(model.param)
        self.channel.setValue(model.channel)
        self.min.setValue(model.blink_min)
        self.max.setValue(model.blink_max)
        self.blink.setChecked(model.blink)
        self.shifter.setChecked(model.shifter)

    def save_model(self):
        model = self.model()
        model.param = self.param.value()
        model.channel = self.channel.value()
        model.blink_min = self.min.value()
        model.blink_max = self.max.value()
        model.blink = self.blink.isChecked()
        model.shifter = self.shifter.isChecked()

    def on_test_press(self):
        global form
        print("Test btn press")
        if self.current_test is not None:
            return
        self.save_model()
        m = self.model()
        if form.config_mode:
            self.current_test = 1, self._index
            midi_send((MIDI_NOTE_ON | 0, self._index, 0x7f))
        else:    
            self.current_test = m.channel, m.param
            midi_send((MIDI_NOTE_ON | m.channel-1, m.param, 0x7f))
        print("Press CH{0} N{1}".format(m.channel, m.param))


    def on_test_release(self):
        channel, note = self.current_test
        print("Release CH{0} N{1}".format(channel, note))
        
        if form.config_mode:
            midi_send((MIDI_NOTE_OFF | channel, note, 0))
        else:
            midi_send((MIDI_NOTE_OFF | channel-1, note, 0))
        self.current_test = None
    
    def copy_values_from(self, origin, value="all"):
        # print("Updating output widget ", self._index)
        if value=="blink":
            self.blink.setChecked( origin.blink.isChecked() )
        elif value=="shifter":
            self.shifter.setChecked( origin.shifter.isChecked() )
        elif value=="channel":
            self.channel.setValue( origin.channel.value() )
        elif value=="min":
            self.min.setValue( origin.min.value() )
        elif value=="max":
            self.max.setValue( origin.max.value() )


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

    #def setValue(self, *args, **kwargs):

    #def stepBy(self, *args, **kwargs):
    #	print(args)

class InputConfig(ConfigWidget):
    _prev_mode = MODE_OFF
    
    def __init__(self, model_name, index, parent=None):
        super(InputConfig, self).__init__(model_name, index, parent)
        
        self._index = index
        
        self.number = self.add(QLabel(str(index)))
        self.number.setStyleSheet("QLabel { font-size: 12pt }")
        self.number.installEventFilter(self)
        
        self.monitor = self.add(QLabel())
        self.monitor.setStyleSheet("QLabel { font-size: 10pt }")
        self.monitor.setFixedWidth(100)
        self.monitor.setAutoFillBackground(True)

        self.monitor.installEventFilter(self)

        self.enable_monitor = self.addwl(_("Monitor"), QCheckBox())
        self.enable_monitor.setChecked(True)
        self.monitor.installEventFilter(self)

        self.enable_monitor.stateChanged.connect(lambda: self.update_grouped_widgets("monitor"))
        
        modeCB = QComboBox()
        modeCB.setStyleSheet("QComboBox { font-size: 10pt }")
        self.mode = self.addwl(_("Mode"), modeCB)
        for labelIdx in MODE_ENABLED:
            self.mode.addItem(MODE_LABELS[labelIdx])
        self.mode.setCurrentIndex(MODE_NOTE) #Default value
        self.mode.currentIndexChanged.connect(self.on_param_value_changed)

        self.mode.currentIndexChanged.connect(lambda: self.update_grouped_widgets("mode"))
        
        paramSB = QSpinBox()
        paramSB.setStyleSheet("QSpinBox { font-size: 10pt }")
        self.param = self.addwl(_("Param"), paramSB);
        self.param.valueChanged.connect(self.on_param_value_changed)
        #WARNING: param does not update grouped widgets values
        #setWidgetBackground(self.param, Qt.black)
        #self.param.setToolTip(_("El rango para Notas y CC es de 0 a 127"))
        self.param.setRange(0, pow(2, 14)-1)
        self.param.installEventFilter(self)

        channelSB = QSpinBox()
        channelSB.setStyleSheet("QSpinBox { font-size: 10pt }")
        self.channel = self.addwl(_("Channel"), channelSB)
        self.channel.setRange(1, 16)
        self.channel.valueChanged.connect(lambda: self.update_grouped_widgets("channel"))
        
        minSB = QSpinBoxHack()
        minSB.setStyleSheet("QSpinBoxHack { font-size: 10pt }")
        self.min = self.addwl(_("Min."), minSB)
        self.min.setRange(0, 127)

        self.min.valueChanged.connect(lambda: self.update_grouped_widgets("min"))

        maxSB = QSpinBoxHack()
        maxSB.setStyleSheet("QSpinBoxHack { font-size: 10pt }")
        self.max = self.addwl(_("Max."), maxSB)
        self.max.setRange(0, 127)
        #self.max.valueChanged.connect(self.on_max_value_changed)

        self.max.valueChanged.connect(lambda: self.update_grouped_widgets("max"))

        self.max.setValue(127)

        #TODO: On any change: save model? <- NO

    def show_feedback(self):
        #if self.enable_monitor.isChecked():	#Controlado antes de llamar esta funcion
        super().show_feedback()

    def load_model(self):
        global form
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
        global form
        alertParam = False
        glob = config['global'];
        mode = self.mode.currentIndex()
        param = self.param.value()
        max_banks = config['global'].num_banks
        
        if self._first_time:
            self._first_time = False
            return
        
        if (mode == MODE_NOTE or mode == MODE_CC or mode == MODE_PC) and param > 127:
            alertParam = True
            self.setAlert(_("Note/CC param {0} outside valid range 0-127").format(param))
        elif mode == MODE_SHIFTER and max_banks == 1:
            alertParam = True
            self.setAlert(_("There is no use for a shifter, if you only have one bank").format(param, max_banks-1))            
        elif mode == MODE_SHIFTER and param >= max_banks:
            alertParam = True
            self.setAlert(_("Shifter param {0} outside bank range 0-{1}").format(param, max_banks-1))
        else:
            repeated = False
            if mode == MODE_SHIFTER:                
                for i, w in enumerate(self.window().inputs):
                    if self._index != i and i < glob.num_inputs_norm:
                        if w.mode.currentIndex() == MODE_SHIFTER and w.param.value() == param:
                            self.setAlert(_("Banco de shifter repetido ({0})").format(param))
                            alertParam = True
                            repeated = True
                            break
                            
                for bankIdx in range(max_banks):
                    config['banks'][bankIdx].input_cc[self._index].mode = MODE_SHIFTER
                    config['banks'][bankIdx].input_cc[self._index].param = param
                    
            elif self._prev_mode == MODE_SHIFTER:
                for bankIdx in range(MAX_BANKS):
                    if config['banks'][bankIdx].input_cc[self._index].mode == MODE_SHIFTER:
                        config['banks'][bankIdx].input_cc[self._index].mode = mode
                        
            #print(self.window())
            
            if not repeated:
                self.setAlert(None)
                
        #HACK: Refresh everything just in case
        self.window().call_on_param_value_changed_on_inputs()
        
        en = not (mode == MODE_SHIFTER or mode == MODE_OFF or mode==MODE_PC or mode == MODE_PC_MINUS or mode == MODE_PC_PLUS)
        self.min.setEnabled(en)
        self.max.setEnabled(en)
        self.channel.setEnabled(not (mode == MODE_SHIFTER or mode == MODE_OFF))
        
        en = not (mode == MODE_PC_MINUS or mode == MODE_PC_PLUS or (mode == MODE_PC and self.analog.currentIndex() == 0))
        self.param.setEnabled(en)
        
        self.min.setRange(0, 16383 if mode == MODE_NRPN else 127)
        self.min.setSingleStep(128 if mode == MODE_NRPN else 1)
        
        self.max.setRange(0, 16383 if mode == MODE_NRPN else 127)
        self.max.setSingleStep(128 if mode == MODE_NRPN else 1)
        #self.max.setValue((self.max.value()<<7) if mode == MODE_NRPN else self.max.value())

        stylesheetProp(self.param, "alert", alertParam)
        
        self._prev_mode = mode

    def show_value(self, value):
        self.monitor.setText("({0})".format(value))

class InputConfigCC(InputConfig):
    def __init__(self, model_name, index, parent=None):

        ad = QComboBox()
        ad.setStyleSheet("QComboBox {font-size: 10pt}")
        ad.setMinimumWidth(80)
        ad.addItems((_("Analog"), _("Digital")))
        self.analog = ad

        pt = QComboBox()
        pt.setStyleSheet("QComboBox {font-size: 10pt}")
        pt.setMinimumWidth(120)
        pt.addItems((_("Toggle"), _("Momentary")))

        self.toggle = pt		# Changes for regular input (pot, slider) and ultrasound config

        super().__init__(model_name, index, parent)
        self.addwl(_("A/D"), ad, 4)		# Changes for regular input (pot, slider) and ultrasound config
        self.addwl(_("Press"), pt, 6)		# Changes for regular input (pot, slider) and ultrasound config

        self.analog.currentIndexChanged.connect(lambda: self.update_grouped_widgets("a/d"))
        self.toggle.currentIndexChanged.connect(lambda: self.update_grouped_widgets("press"))
        
        #After super __init__ is called
        ad.currentIndexChanged.connect(self.on_param_value_changed)
        ad.setCurrentIndex(1)
        pt.currentIndexChanged.connect(self.on_param_value_changed)
        pt.setCurrentIndex(1)

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
        max_banks = config['global'].num_banks
            
        if mode == MODE_SHIFTER:
            self.analog.setCurrentIndex(1)
            for bankIdx in range(max_banks):
                config['banks'][bankIdx].input_cc[self._index].analog = 0                                  # setear como digital en todos los bancos
            config['banks'][bankIdx].input_cc[self._index].toggle = self.toggle.currentIndex() == 0
        elif mode == MODE_PC_MINUS or mode == MODE_PC_PLUS:
            self.analog.setCurrentIndex(1)
            self.toggle.setCurrentIndex(0)
        
        self.analog.setEnabled(not (mode == MODE_SHIFTER or mode == MODE_OFF or mode == MODE_PC_MINUS or mode == MODE_PC_PLUS))      
        self.toggle.setEnabled(not (self.analog.currentIndex() == 0 or mode == MODE_OFF or mode == MODE_PC_MINUS or mode == MODE_PC_PLUS))		
        #WARNING: param does not update grouped widgets values

    def copy_values_from(self, origin, value="all"):
        print("Updating input widget ", self._index)
        #if value=="all":
            #super().copy_values_from(origin)
            #self.mode.setCurrentIndex( origin.mode.currentIndex() ) #TODO: ver on_param_value_changed
            #self.analog.setCurrentIndex( origin.analog.currentIndex() ) # A/D
            #self.toggle.setCurrentIndex( origin.toggle.currentIndex() )
            # self.pot = origin.pot
            # self.on_param_value_changed()
        if value=="monitor":
            self.enable_monitor.setChecked( origin.enable_monitor.isChecked() )
        elif value=="a/d":
            self.analog.setCurrentIndex( origin.analog.currentIndex() )
        elif value=="press": # action
            self.toggle.setCurrentIndex( origin.toggle.currentIndex() )
        elif value=="mode":
            self.mode.setCurrentIndex( origin.mode.currentIndex() ) #TODO: ver on_param_value_changed
        elif value=="channel":
            self.channel.setValue( origin.channel.value() )
        elif value=="min":
            self.min.setValue( origin.min.value() )
        elif value=="max":
            self.max.setValue( origin.max.value() )

class InputConfigUS(InputConfig):
    def __init__(self, model_name, parent=None):

        self.dist_min = QSpinBox()
        self.dist_min.setStyleSheet("QSpinBox {font-size: 10pt}")
        max_uint14 = 400
        self.dist_min.setMaximum(max_uint14)
        self.dist_max = QSpinBox()
        self.dist_max.setStyleSheet("QSpinBox {font-size: 10pt}")
        self.dist_max.setMaximum(max_uint14)
        self.dist_max.setValue(max_uint14)

        super().__init__(model_name, 0, parent)
        self.number.setText("")

        self.mode.setCurrentIndex(MODE_OFF);
        
        self.dist_min.valueChanged.connect(self.on_param_value_changed)
        self.dist_max.valueChanged.connect(self.on_param_value_changed)

        self.dist_min = self.addwl(_("Min. Dist."), self.dist_min)
        self.dist_max = self.addwl(_("Max. Dist."), self.dist_max)

        self.mode.removeItem(MODE_SHIFTER);
        self.mode.removeItem(MODE_PC_PLUS);
        self.mode.removeItem(MODE_PC);
        self.mode.removeItem(MODE_PC_MINUS);

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
        min = self.dist_min.value()
        max = self.dist_max.value()
        alertParam = False
        
        if min > max-10:
            self.setAlert(_("MAX value should be at lease 10cm greater than MIN value"))
            alertParam = True
            
        stylesheetProp(self.dist_min, "alert", alertParam)
        stylesheetProp(self.dist_max, "alert", alertParam)

class MyQGridLayout(QGridLayout):
    def __init__(self, parent = None):
        QGridLayout.__init__(self, parent) 
        self.maximumSize = 250
        
class MonitorTextEdit(QTextEdit):
    def __init__(self, parent = None):
        QTextEdit.__init__(self, parent) 
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        copyAction = menu.addAction(_("Copy"))
        selAllAction = menu.addAction(_("Select all"))
        separator = menu.addSeparator()
        clearAction = menu.addAction(_("Clear"))
        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == clearAction:
            self.clear()
            self.setText(_("MIDI Monitor"))
        elif action == copyAction:
            self.copy()
        elif action == selAllAction:
            self.selectAll()
            

class Form(QFrame):
    outputs = []
    inputs = []
    input_us = None
    current_bank = 0
    current_inout_tab = 0
    prev_param = 0
    nrpn_param_coarse = 0
    nrpn_param_complete = 0
    nrpn_val_coarse = 0
    nrpn_val_complete = 0
    
    _last_in_values = []

    pressedKeys = set()
    
    multiple_edition_mode = False
    
    config_mode = False
    midi_thru = False
    
    testing = None
    
    def on_test_all_press(self):
        to_test = []
        value = self.test_all_velocity.value()
        for i in range(0, config['global'].num_outputs):
            self.outputs[i].save_model()
            m = self.outputs[i].model()
            if self.config_mode:
                to_test.append((0, i))
            else:
                to_test.append((m.channel-1, m.param))

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
    #    for i in self.inputs + self.outputs + [self.input_us]:
    #        i.channel.setValue(self.set_chan_channel.value())

    _reentry_inputs = 0
    def call_on_param_value_changed_on_inputs(self):
        if self._reentry_inputs > 0:
            return

        self._reentry_inputs += 1
        #print("Refreshing alerts")

        for w in self.inputs:
            w.on_param_value_changed()

        self._reentry_inputs -= 1
    
    # _reentry_outputs = 0
    # def call_on_param_value_changed_on_outputs(self):
        # if self._reentry_outputs > 0:
            # return

        # self._reentry_outputs += 1
        # #print("Refreshing alerts")

        # for w in self.outputs:
            # w.on_param_value_changed()

        # self._reentry_outputs -= 1
        
    def __init__(self, parent=None):
        print("Form()  B Form init")
        super(Form, self).__init__(parent)

        print("Form()  2 Form set window title")
        self.setWindowTitle(TITLE + " " + VERSION)
        # Create widgets

        print("Form()  1 Move resize")

        self.move(24, 24)
        self.resize(1280, 720)

        print("Form() 13 Master layout")

        master_layout = QVBoxLayout()
        #master_layout.addStretch(1)
        self.setLayout(master_layout)

        def addLabelWA(layout, text):		#Workaround for labels that resized big time
            lbl = QLabel(text)
            lbl.setStyleSheet("QLabel { font-weight: bold; font-size: 10pt }")
            #lbl.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
            layout.addWidget(lbl)
            

        ############## TOP LAYOUT #############

        layout_top = QHBoxLayout()
        layout_top.setAlignment(Qt.AlignTop)
        master_layout.addLayout(layout_top)

        print("Form() Memory widget")
        
        self.memory_widget = MemoryWidget(self)
        #self.memory_widget.setStyleSheet("Mem {border: 1px solid gray}")
        #self.memory_widget.setObjectName("MemWidget")

        print("Form() Memory widget ok")

        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Maximum)
        
        layout_htop = QVBoxLayout()
        layout_htop.addWidget(self.memory_widget)
        
        layout_top.addLayout(layout_htop)
        #layout_top.addLayout(layout_config)
        
        layout_top.addStretch() # space between
        
        widget_save = QWidget()
        widget_save.setMaximumWidth(400)
        load_save_layout = QGridLayout()
        #load_save_layout.setSizeConstraint(QLayout.SetMaximumSize)
        widget_save.setLayout(load_save_layout)
        layout_top.addWidget(widget_save)
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
    
        self.label_file = QLabel("File")
        self.label_file.setStyleSheet("QLabel { font-size: 10pt ; font-style: italic;}")
        lsh.widget(self.label_file, spanx=2, align=Qt.AlignLeft).newLine()
        
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

        btnDump = QPushButton(_("Dump to Arduino"))
        btnDump.setStyleSheet("QPushButton { font-size: 10pt }")
        btnDump.setObjectName("DumpBtn")
        #btn.setIcon(QIcon("test.png"))
        btnDump.setIconSize(QSize(24,24))
        #btn.setStyleSheet("text-align: right;")

        btnDump.pressed.connect(self.on_dump_sysex_press)
        btnDump.released.connect(self.on_dump_sysex_release)

        load_save_layout.addWidget(btnDump)
        lsh.widget(btnDump, spanx=2, width=lsh_w)
        lsh.newLine()
        self.buttonDump = btnDump
        
        link = QLabel()
        link.setText("<a href=\"http://wiki.yaeltex.com.ar/index.php?title=Kilowhat\" style=\"color: yellow;\">" + _("Help") + "</a>")
        link.setStyleSheet("QLabel { font-size: 10pt; padding-right: 3px; }")
        link.setTextInteractionFlags(Qt.TextBrowserInteraction)
        link.setTextFormat(Qt.RichText)
        link.setOpenExternalLinks(True)
        lsh.widget(link, spanx=2, align=Qt.AlignRight).newLine()
        
        master_layout.addStretch(1)

        widget_bank_line = PaintWidget()
        layout_bank_line = QHBoxLayout()
        layout_bank_line.setContentsMargins(9,0,9,1)
        widget_bank_line.setObjectName("BankLine")
        #widget_bank_line.setStyleSheet(".QWidget { border: 1px solid white }")
        layout_bank_line.setAlignment(Qt.AlignLeft)
        widget_bank_line.setLayout(layout_bank_line)
        #master_layout.addLayout(layout_bank_line)
        master_layout.addWidget(widget_bank_line)
        
        ##########################################
        # tabs: inputs/outputs/distance sensor
        ##########################################
        self.tabs_inout = QTabBar()
        self.tabs_inout.setObjectName("inout")
        # self.tabs_inout.setStyleSheet("QTabBar { font-size: 10pt }")
        self.tabs_inout.setStyleSheet("QTabBar { font-size: 10pt }")
        self.tabs_inout.setUsesScrollButtons(False)
        #self.tabs_inout.setAlignment(Qt.AlignLeft)
        self.tabs_inout.setBackgroundRole(QPalette.Dark)		#HACK: to hide bottom line
        self.tabs_inout.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        
        layout_bank_line.addWidget(self.tabs_inout)
        
        self.tabs_inout.addTab(_("Inputs"))
        self.tabs_inout.addTab(_("Outputs"))
        if not miniblock:
            self.tabs_inout.addTab(_("Distance sensor"))
        self.tabs_inout.currentChanged.connect(self.on_change_tab_inout)
        
        layout_bank_line.addStretch()
        layout_bank_line.addStretch()
        
        self.tabs_banks = QTabBar()
        self.tabs_banks.setStyleSheet("QTabBar { font-size: 10pt }")
        self.tabs_banks.setUsesScrollButtons(False)
        #self.tabs_banks.setAlignment(Qt.AlignLeft)
        self.tabs_banks.setBackgroundRole(QPalette.Dark)        #HACK: to hide bottom line     
        self.tabs_banks.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        layout_bank_line.addWidget(self.tabs_banks)
        self.tabs_banks.currentChanged.connect(self.on_change_tab_bank)
        self.refresh_tabs()
        
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
        
        ################################
        # Add UltraSonic input widgets #
        ################################

        section_layout = QVBoxLayout()
        section_layout.setSizeConstraint(QLayout.SetNoConstraint)
        
        master_layout.addLayout(section_layout)
        
        self.us_frame = QFrame()
        us_side = self.us_frame
        us_layout = QVBoxLayout()
        us_layout.setObjectName("USLayout")
        us_side.setLayout(us_layout)
        section_layout.addWidget(us_side)
        
        # Add UltraSonic widget
        us_area = QScrollArea()
        us_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        us_area.setWidgetResizable(True)
        us_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        us_layout.addWidget(us_area)
        us_layout.addSpacing(312)
        
        lw = InputConfigUS('input_us', self)
        lw.setProperty("parity", "even")
        #lw.setMinimumHeight(40)
        self.input_us = lw
        #Pre-config banks
        for bankIdx in range(MAX_BANKS):
            config['banks'][bankIdx].input_us[0].mode = MODE_OFF
        
        us_area.setWidget(lw)

        #####################
        # Add input widgets #
        #####################
        # Add CC widgets

        self.inputs_frame = QFrame()
        inputs_side = self.inputs_frame
        input_layout = QVBoxLayout()
        input_layout.setObjectName("InputLayout")
        #input_layout.setSizeConstraint(QLayout.SetMaximumSize)
        inputs_side.setLayout(input_layout)
        section_layout.addWidget(inputs_side)
        
        saw = QWidget()
        sa_layout = QVBoxLayout()
        sa_layout.setSizeConstraint(QLayout.SetMaximumSize)
        sa_layout.setSpacing(0)
        saw.setLayout(sa_layout)
        saw.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        ins_area = QScrollArea()
        ins_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        ins_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        ins_area.setWidgetResizable(True)
        ins_area.setWidget(saw)
        input_layout.addWidget(ins_area)

        for i in range(0, MAX_INPUTS_CC):
            #For each config, pre-config banks
            for bankIdx in range(MAX_BANKS):
                config['banks'][bankIdx].input_cc[i].param = i

            lw = InputConfigCC('input_cc', i, self)
            lw.load_model()
            #lw.setMinimumHeight(40)
            if i % 2 == 0:
                lw.setProperty("parity", "even")	#For stylesheets
            self.inputs.append(lw)
            self._last_in_values.append(-THRESHOLD_SELECT)
            sa_layout.addWidget(lw)
        
        ######################
        # Add output widgets #
        ######################
        self.outputs_frame = QFrame()
        outputs_side = self.outputs_frame
        output_layout = QVBoxLayout()
        output_layout.setObjectName("OutputLayout")
        #output_layout.setSizeConstraint(QLayout.SetMaximumSize)
        outputs_side.setLayout(output_layout)
        section_layout.addWidget(outputs_side)
        
        saw = QWidget()
        sa_layout = QVBoxLayout()
        sa_layout.setSizeConstraint(QLayout.SetMaximumSize)
        sa_layout.setSpacing(0)
        saw.setLayout(sa_layout)
        saw.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        outs_area = QScrollArea()
        outs_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        outs_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        outs_area.setWidgetResizable(True)
        outs_area.setWidget(saw)
        output_layout.addWidget(outs_area)

        #################################################
        # Test all segment
        #################################################
        test_all_widget = QWidget()
        test_all_widget.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        test_all_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        test_all_layout = QHBoxLayout()
        
        test_all_btn = QPushButton(_("Test all"))
        test_all_btn.setStyleSheet("QPushButton {font-size: 10pt}");
        test_all_btn.pressed.connect(self.on_test_all_press)
        test_all_btn.released.connect(self.on_test_all_release)
        test_all_btn.setObjectName("TestAll")
        
        test_all_layout.addWidget(test_all_btn)
        
        lbl_test = QLabel(_("with velocity"))
        lbl_test.setStyleSheet("QLabel {font-size: 10pt}");
        
        test_all_layout.addWidget(lbl_test)

        self.test_all_velocity = QSpinBox()
        self.test_all_velocity.setStyleSheet("QSpinBox {font-size: 10pt}");
        self.test_all_velocity.setValue(64)
        self.test_all_velocity.setMinimum(0)
        self.test_all_velocity.setMaximum(0x7f)

        test_all_layout.addWidget(self.test_all_velocity)

        #sa_layout.addLayout(test_all_layout)
        sa_layout.addWidget(test_all_widget)
        test_all_widget.setLayout(test_all_layout)
        #################################################
        
        max_outs = 4 if miniblock else MAX_OUTPUTS
        
        for i in range(0, max_outs):
            #For each config, pre-config banks
            for bankIdx in range(MAX_BANKS):
                config['banks'][bankIdx].output[i].note = i

            lw = OutputConfig('output', i)
            lw.load_model()
            
            if i % 2 == 0:
                lw.setProperty("parity", "even")	#For stylesheets
            self.outputs.append(lw)
            sa_layout.addWidget(lw)
            
        if miniblock:
            sa_layout.addSpacing(123)
            self.memory_widget.banks.setEnabled(False)
            self.memory_widget.ins.setEnabled(False)
            self.memory_widget.outs.setEnabled(False)
            self.memory_widget.hardware.setEnabled(False)
            self.memory_widget.output_matrix.setEnabled(False)
            self.memory_widget.btn_apply.setEnabled(False)
        ###############
        
        #end in/out/sensor tab config
        ###############
        #Hack to let the outputs window load with full size
        self.change_views_inout_tab(1)
        #Default view: inputs
        self.change_views_inout_tab(0)
        
        self.refresh_in_outs()
       
        master_layout.addStretch(1)
        
        config_mode_layout = QHBoxLayout()
        config_mode_layout.setAlignment(Qt.AlignBottom)
        config_mode_layout.setObjectName("MidiMonitorConfigCB")
        
        self.config_modeCB = QCheckBox(_("Config Mode"))
        self.config_modeCB.setStyleSheet("QCheckBox { font-size: 10pt }")
        self.config_modeCB.clicked.connect(self.on_config_mode_press)
        
        config_mode_layout.addStretch()
        config_mode_layout.addStretch()
        
        config_mode_layout.addWidget(self.config_modeCB)
        
        config_mode_layout.addSpacing(13)
        
        #master_layout.addSpacing(50)
        master_layout.addLayout(config_mode_layout)
        
        log_widget = QWidget()
        log_layout = QHBoxLayout()
        log_widget.setObjectName("LogArea")
        
        log_widget.setLayout(log_layout)
        master_layout.addWidget(log_widget)
        
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setStyleSheet("QTextEdit {font-size: 10pt}")
        self.txt_log.setMinimumHeight(120)
        self.txt_log.setMaximumHeight(120)
        log_layout.addWidget(self.txt_log)
        self.txt_log.append(_("Welcome to Kilowhat!"))
        #self.txt_log.append(str(self.inputs[2].height()))
        #self.txt_log.append(str(self.outputs[2].height()))
        ###########################               
        self.midi_monitor = MonitorTextEdit()
        self.midi_monitor.setObjectName("MidiMonitor")
        self.midi_monitor.setReadOnly(True)
        self.midi_monitor.setStyleSheet("QTextEdit {font-size: 10pt}")
        self.midi_monitor.append(_("MIDI Monitor")) 
        self.midi_monitor.setMaximumWidth(200)
        self.midi_monitor.setMinimumHeight(120)
        self.midi_monitor.setMaximumHeight(120)
                
        log_layout.addWidget(self.midi_monitor)
        ###########################
        self.selected_list = set()
        
        timer = QTimer(self)
        timer.timeout.connect(self.poll_in)
        timer.start(POLL_INTERVAL)

        self.load_model()        # Load defaults in case automatic file loading fails

        if platform.system() == "Linux":
            if os.path.isfile(FILE_AUTOMATIC):
                self.load_file(FILE_AUTOMATIC, True)

            with open('style-linux.css', 'r') as style_file:
                self.setStyleSheet(style_file.read())
        elif platform.system() == "Darwin":
            if os.path.isfile(FILE_AUTOMATIC):
                self.load_file(FILE_AUTOMATIC, True)

            with open('style-mac.css', 'r') as style_file:
                self.setStyleSheet(style_file.read())
        else:
            if os.path.isfile(FILE_AUTOMATIC):
                self.load_file(FILE_AUTOMATIC, True)

            with open('style-win.css', 'r') as style_file:
                self.setStyleSheet(style_file.read())

    def keyPressEvent(self, e):
        modifiers = QApplication.keyboardModifiers()
        max_banks = config['global'].num_banks
        if modifiers == Qt.ControlModifier:
            if e.key() == Qt.Key_D:
                self.on_dump_sysex_press()
                self.on_dump_sysex_release()
            elif e.key() == Qt.Key_S:
                self.on_save_file()
            elif e.key() == Qt.Key_L:
                self.on_load_file()
        else:
            if e.key() == Qt.Key_E:
                if self.tabs_inout.currentIndex() != 0:
                    self.tabs_inout.setCurrentIndex(0)
            elif e.key() == Qt.Key_S:
                if self.tabs_inout.currentIndex() != 1:
                    self.tabs_inout.setCurrentIndex(1)
            elif e.key() == Qt.Key_D:
                if self.tabs_inout.currentIndex() != 2:
                    self.tabs_inout.setCurrentIndex(2)
            elif e.key() == Qt.Key_0:
                if self.tabs_banks.currentIndex() != 0:
                    self.tabs_banks.setCurrentIndex(0)
            elif e.key() == Qt.Key_1 and max_banks > 0:
                if self.tabs_banks.currentIndex() != 1:
                    self.tabs_banks.setCurrentIndex(1)
            elif e.key() == Qt.Key_2 and max_banks > 1:
                if self.tabs_banks.currentIndex() != 2:
                    self.tabs_banks.setCurrentIndex(2)
            elif e.key() == Qt.Key_3 and max_banks > 2:
                if self.tabs_banks.currentIndex() != 3:
                    self.tabs_banks.setCurrentIndex(3)
            elif e.key() == Qt.Key_4 and max_banks > 3:
                if self.tabs_banks.currentIndex() != 4:
                    self.tabs_banks.setCurrentIndex(4)
            elif e.key() == Qt.Key_5 and max_banks > 4:
                if self.tabs_banks.currentIndex() != 5:
                    self.tabs_banks.setCurrentIndex(5)
                    
    def on_change_tab_bank(self):
        if self.current_bank != self.tabs_banks.currentIndex():
            self.current_bank = self.tabs_banks.currentIndex()
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
            self.inputs_frame.show() #load inputs 
            self.outputs_frame.hide()
            self.us_frame.hide()
        elif bankIdx==1:
            self.inputs_frame.hide()
            self.outputs_frame.show() #load outputs 
            self.us_frame.hide()
        elif not miniblock:
            self.inputs_frame.hide()
            self.outputs_frame.hide()
            self.us_frame.show() #load ultrasonic

    def refresh_tabs(self):
        nbanks = config['global'].num_banks
        for i in range(self.tabs_banks.count(), nbanks):
            self.tabs_banks.addTab(_("Bank {0}").format(i))

        while self.tabs_banks.count() > nbanks:
            self.tabs_banks.removeTab(nbanks)

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
            
    def on_config_mode_press(self):
        if self.config_modeCB.isChecked():
            self.config_mode = True
            midi_send(sysex.make_sysex_packet(sysex.CONFIG_MODE, []))
            return
        else:
            self.config_mode = False
            midi_send(sysex.make_sysex_packet(sysex.EXIT_CONFIG, []))
            return
            
    def on_dump_sysex_press(self):
        self.txt_log.append(_("Starting Dump. Please don't disconnect the usb cable or turn off the device"))
        time.sleep(0.2)
        self.save_model()
        max_banks = config['global'].num_banks        

        stuff = (
            ("Ultrasound", [self.input_us]),
            ("Input", self.inputs),
            ("Output", self.outputs)
        )
        warnings = 0
        errors = 0
            
        for name, lst in stuff:
            for i, w in enumerate(lst): 
                if w.alert_txt is not None :
                    self.txt_log.append("{0} #{1}: {2}".format(name, i, w.alert_txt))
                    errors += 1

        if errors != 0:
            QMessageBox.critical(self, _("Dump error"), _("{0} errors trying to dump.").format(errors))
            self.txt_log.append(_("<b>Dump aborted</b>"))
            return
        elif warnings != 0:
            if QMessageBox.warning(self, _("Dump error"), _("{0} warnings trying to dump, continue anyway?").format(warnings), QMessageBox.Yes, QMessageBox.No) != QMessageBox.Yes:
                self.txt_log.append(_("<b>Dump aborted</b>"))
                return
    
    def on_dump_sysex_release(self):
        send_sysex_dump()
        self.txt_log.append(_("Dump sent"))

    def on_load_file(self):
        # TODO: Check if it was saved!
        fileName, __ = QFileDialog.getOpenFileName(self, _("Open kwt configuration file"),  filter = _("kwt file (*.kwt)"))
        if not fileName:
            return
        self.load_file(fileName)


    def closeEvent(self, event):
        self.save_file(FILE_AUTOMATIC)
        event.accept()     # let the window close

    def load_model(self):
        self.description.setText(config['file']['desc'])
        for w in [self.memory_widget, self.input_us] + self.outputs:
            w._first_time = True
            w.load_model()
        
        for w in self.inputs:
            w._first_time = True
            w.mode.currentIndexChanged.disconnect(w.on_param_value_changed)
            w.param.valueChanged.disconnect(w.on_param_value_changed)
            w.analog.currentIndexChanged.disconnect(w.on_param_value_changed)
            w.toggle.currentIndexChanged.disconnect(w.on_param_value_changed)
            w.load_model()
            w.param.valueChanged.connect(w.on_param_value_changed)
            w.analog.currentIndexChanged.connect(w.on_param_value_changed)
            w.toggle.currentIndexChanged.connect(w.on_param_value_changed)
            w.mode.currentIndexChanged.connect(w.on_param_value_changed) 
            
            #refresh some stuff
            mode = w.mode.currentIndex()
            w.min.setRange(0, 16383 if mode == MODE_NRPN else 127)
            w.min.setSingleStep(128 if mode == MODE_NRPN else 1)
            w.max.setRange(0, 16383 if mode == MODE_NRPN else 127)
            w.max.setSingleStep(128 if mode == MODE_NRPN else 1)
            
            en = not (mode == MODE_SHIFTER or mode == MODE_OFF or mode==MODE_PC or mode == MODE_PC_MINUS or mode == MODE_PC_PLUS)
            w.min.setEnabled(en)
            w.max.setEnabled(en)
            w.channel.setEnabled(not (mode == MODE_SHIFTER or mode == MODE_OFF))
            
            en = not (mode == MODE_PC_MINUS or mode == MODE_PC_PLUS or (mode == MODE_PC and w.analog.currentIndex() == 0))
            w.param.setEnabled(en)
            
            en = not (mode == MODE_SHIFTER or mode == MODE_OFF or mode == MODE_PC_MINUS or mode == MODE_PC_PLUS)
            w.analog.setEnabled(en)      
            w.toggle.setEnabled(not (w.analog.currentIndex() == 0 or mode == MODE_OFF or mode == MODE_PC_MINUS or mode == MODE_PC_PLUS))

    def load_file(self, fileName, automatic = False):
        try:
            file = open(fileName, 'rb')
            global config
            config2 = pickle.load(file)
                
            file_ver = config2['file_ver'] if 'file_ver' in config2 else 0
            
            self.label_file.setText(os.path.basename(fileName))
            
            if file_ver != PROTOCOL_VERSION:
                if not automatic:
                    QMessageBox.warning(self, _('Error'),
                                        _('Invalid version of kwt configuration file "{0}"\nVersion {1} should be {2} ')
                                        .format(fileName, file_ver, PROTOCOL_VERSION))
            else:
                config = config2       
                self.current_bank = 0
                self.current_inout_tab = 0
                self.refresh_tabs()
                self.refresh_in_outs()
                self.load_model()              
            file.close()
        except Exception as e:
            time.sleep(0.1)
            QMessageBox.warning(self, _('Error'), _('Error opening kwt configuration file "{0}"\n{1}').format(fileName, e))

    def save_file(self, fileName):
        try:
            if 1:
                file = open(fileName, 'wb')
                self.save_model()
                pickle.dump(config, file)
                file.close()
        except Exception as e:
            time.sleep(0.1)
            QMessageBox.warning(self, _('Error'), _('Error writing kwt configuration file "{0}"\n{1}').format(fileName, e))

    def on_save_file(self):
        # TODO: Check if it was saved!
        fileName, __ = QFileDialog.getSaveFileName(self, _("Save kwt configuration file"),  filter = _("kwt file (*.kwt)"))
        if not fileName:
            return
        try:
            self.save_file(fileName)
            self.label_file.setText(os.path.basename(fileName))
        finally:
            self.save_file(FILE_RECOVER)

    def processCommand(self, cmd):
        print("Received command")
        print(cmd)

        #TODO: make packets static once
        if cmd == sysex.make_sysex_packet(sysex.CONFIG_ACK, []):
            self.txt_log.append(_("ACK Received. Kilomux connected"))
            if not self.config_modeCB.isChecked():
                self.config_modeCB.setChecked(True)
            return
            
        if cmd == sysex.make_sysex_packet(sysex.EXIT_CONFIG_ACK, []):
            self.txt_log.append(_("Arduino is not in config mode anymore"))
            return

        if cmd == sysex.make_sysex_packet(sysex.DUMP_OK, []):
            self.txt_log.append(_("Dump OK"))
            self.config_modeCB.setChecked(False)
            return
        
        if cmd[0] >= MIDI_PROGRAM_CHANGE and cmd[0] <= MIDI_PROGRAM_CHANGE|0xF :
            type_chn, param = cmd
            value = 0
        else:
            type_chn, param, value = cmd
            
        cmd_type = type_chn & 0xf0
        chn = type_chn & 0xf
        
        # MIDI Monitor log
        if not self.config_modeCB.isChecked():
            if cmd_type == MIDI_CC:
                # NRPN Message parser
                if param == 101 and self.prev_param != 101:
                    self.prev_param = 101
                    self.nrpn_param_coarse = value
                    return
                elif param == 100 and self.prev_param == 101:
                    self.prev_param = 100
                    self.nrpn_param_complete = self.nrpn_param_coarse << 7 | value
                    return
                elif param == 6 and self.prev_param == 100:
                    self.prev_param = 6
                    self.nrpn_val_coarse = value
                    return
                elif param == 38 and self.prev_param == 6:
                    self.prev_param = 0
                    self.nrpn_val_complete = self.nrpn_val_coarse << 7 | value
                    self.midi_monitor.append(str(chn+1) + " NRPN " + str(self.nrpn_param_complete) + " " + str(self.nrpn_val_complete))
                    return
                else:    
                    prev_param = 0
                    self.midi_monitor.append(str(chn+1) + " CC " + str(param) + " " + str(value))
                    
            elif cmd_type == MIDI_NOTE_ON:
                self.midi_monitor.append(str(chn+1) + " Note On " + str(param) + " " + str(value))
            elif cmd_type == MIDI_NOTE_OFF:
                self.midi_monitor.append(str(chn+1) + " Note Off " + str(param) + " " + str(value))
                midi_send((MIDI_NOTE_ON | chn, param, value))
            elif cmd_type == MIDI_PROGRAM_CHANGE:
                self.midi_monitor.append(str(chn+1) + " Program Change " + str(param)) 
                return      # to prevent error unpacking only 2 bytes
            else:
                self.midi_monitor.append(_("MIDI message not supported"))
        
        if self.midi_thru:
            midi_send((cmd_type | chn, param, value))  # MIDI THRU
                    
        target = None
        if self.config_modeCB.isChecked():
            if chn == MONITOR_CHAN_US:
                target = self.input_us
            else:
                #if (type == MIDI_NOTE_ON or type == MIDI_CC) and param < len(self.inputs) and value > 0:
                if param < len(self.inputs):
                    if cmd_type == MIDI_NOTE_OFF:    #Force note-off to value = 0
                        value = 0
                    target = self.inputs[param]
        
        if target is not None:                
            #self.midi_monitor.append((_("CC") if cmd_type == MIDI_CC else _("Note")) + " " + str(param) + " " + str(value))

            target.show_value((_("CC") if cmd_type == MIDI_CC else _("Note")) + " " + str(value))
            last_value = self._last_in_values[param]
            #self.txt_log.append("Param " + str(param) + " Value " + str(value) + " Last value: " + str(self._last_in_values[param]))
            if abs(last_value - value) > THRESHOLD_SELECT:
                self._last_in_values[param] = value
                
                if target.enable_monitor.isChecked():
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
        """ 
            Widget simple select (from scratch)
            On a new selection, first clean possibly multiple old selection
        """
        widget.multiple_edition_mode = False 
        for i_widget in self.selected_list:
            i_widget.unselect()
        self.selected_list.clear()

        if self.prev_selected is not None:
            self.prev_selected.unselect()
        widget.select()
        self.prev_selected = widget

        self.selected_list.add( widget )

    def multiple_select_copy_values(self, origin, value="all"):
        # if not self.multiple_edition_mode:
        #     return
        if origin not in self.selected_list:
            return
        for i_widget in self.selected_list:
            if i_widget != origin:
                i_widget.copy_values_from(origin, value)

    def multiple_select_ctrl(self, widget):
        if isinstance(widget,InputConfigUS):
            return
        self.prev_selected = widget
        widget.multiple_edition_mode = True
        if widget in self.selected_list:
            widget.unselect()
            self.selected_list.remove( widget )
        else:
            widget.select()
            self.selected_list.add( widget )

    def multiple_select_shft(self, widget):
        if isinstance(widget,InputConfigUS):
            return
        widget.multiple_edition_mode = True
        if widget!=self.prev_selected:
            first = widget._index
            if first<self.prev_selected._index:
                last = self.prev_selected._index
            else:
                last = first
                first = self.prev_selected._index
            if isinstance(widget,InputConfigCC):
                widgets_list = self.inputs
            else:
                widgets_list = self.outputs
            for w in widgets_list:
                if w._index in range(first,last+1):
                    w.select()
                    self.selected_list.add( w )
        elif widget in self.selected_list:
            widget.unselect()
            self.selected_list.remove( widget )
        self.prev_selected = widget

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
                font = QFont(font_family, 10)

                font.setStyleStrategy(QFont.PreferAntialias)    #
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
    from ctypes import wintypes
    lpBuffer = wintypes.LPWSTR()
    AppUserModelID = ctypes.windll.shell32.GetCurrentProcessExplicitAppUserModelID
    AppUserModelID(ctypes.cast(ctypes.byref(lpBuffer), wintypes.LPWSTR))
    appid = lpBuffer.value
    ctypes.windll.kernel32.LocalFree(lpBuffer)
    if appid is not None:
        print(appid)

print("Creating form")

# Create and show the form
form = Form()
#form.resize(1024, 600)
print("Form created")
# print("fix combos")
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
