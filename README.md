# Kilowhat

Software de configuración por SysEx de Yaeltex. / SysEx configuration tool by Yaeltex
 
* [Último release] (https://github.com/Yaeltex/kilowhat/releases/)
* [Wiki](http://wiki.yaeltex.com/index.php?title=Kilowhat)

(english below)
**Kilowhat** es una herramienta open source desarrollada por Yaeltex, pensada para ser usada con sus productos, para poder configurar interfaces MIDI hechas con el Kilomux Shield para Arduino.
Funciona mediante el uso del protocolo SysEx, y permite al usuario configurar las entradas y las salidas disponibles en esos dispositivos, para que puedan enviar y recibir mensajes MIDI personalizados.

* Configuración general:
  * Elige la placa Arduino que estás usando y aprovecha al máximo su memoria.
  * Elige la cantidad de entradas y salidas que usas en tu aplicación del Kilomux.
  * Configura hasta 8 bancos diferentes (dependiendo de la placa Arduino y la memoria disponible).
  * Guarda tus configuraciones y compartelas con la comunidad, o carga configuraciones que hayan compartido otros usuarios.

* Entradas:
  * Configura las entradas para que envíen distintos tipos de mensajes MIDI, como Notas, CC, NRPN, Program change (estático, +1 o -1) o Shifters (para alternar entre los bancos).
  * Configura tu entrada como analógica o digital.
  * Configura tus entradas digitales cómo momentánes o toggle.
  * Configura los valores mínimo y máximo para los mensajes MIDI que envía cada control, y si quieres incluso puedes invertirlos.
  * Configura el canal MIDI que envía cada control en forma individual.
  * Monitorea los mensajes MIDI provenientes de tu dispositivo.

* Control por sensor de ultrasonido:
  * Configura los mensajes MIDI que envía este control como Nota, CC o NRPN. 
  * Configura el canal MIDI.
  * Configura los valores mínimo y máximo para el mensaje MIDI.
  * Configura la distancia mínima y máxima de sensado.

* Salidas:
  * Configura el parámetro para que se corresponda con el de un botón asociado, o en forma independiente, para que responda a la Nota que tu elijas.
  * Prueba las salidas del Kilomux desde la aplicación.
  * Configura si quieres que la salida sea intermitente o permanente.
  * Elige si usas tus salidas en forma directa o matricial (con ésta última puedes usar hasta 64 LEDs con tu Kilomux).

* Instalación
Te proporcionamos los ejecutables para que puedas usar el Kilowhat en el sistema operativo que prefieras (ver al final de éste documento) de forma sencilla. 

* Sistemas operativos soportados
El Kilowhat está probado y funciona en:
  ** Mac OS X El Capitan 10.11.6
  ** Windows 10
  ** Ubuntu 16.04 LTS

Puede funcionar en otros, si lo pruebas y funciona, por favor avisa a franco@yaeltex.com!

---

First production release with cool features :)

**Kilowhat** is an open source tool developed by Yaeltex, to be used with our products, and meant for configuring MIDI interfaces made with the Kilomux shield.
It works with the SysEx protocol and it allows the user to configure all the inputs and outputs available in the device, to send and receive custom MIDI messages.

* General configuration:
  * Select Arduino board and get the most of each.
  * Choose the number of inputs and outputs that suit your application.
  * Configure up to 8 banks (depending on the device and memory available).
  * Save and your configurations and share them with the community, or load configurations made by other users.

* Inputs:
  * Configure MIDI messages as Note, CC, NRPN, Program change (static, +1 or -1) or Shifter (to switch banks).
  * Configure as analog or digital.
  * Configure digital inputs as either momentary or latching (Toggle).
  * Configure MIN/MAX values for MIDI output, and even invert if desired.
  * Configure MIDI channel individually.
  * Monitor MIDI input from device.

* Ultrasonic sensor input:
  * Configure MIDI message as Note, CC, or NRPN.
  * Configure MIDI channel.
  * Configure MIN/MAX value for MIDI output.
  * Configure min and max sensing distance.

* Outputs:
  * Configure parameter to match button's and light up at the correct time.
  * Test outputs by sending MIDI notes.
  * Configure blink or permanent mode.
  * Change between Normal or Matrix mode in order to have up to 64 outputs.

* Installation
We provide the executable files so that you can use Kilowhat in the operating system you normally use (detailed below). Just download and run!

* Tested OS
Kilowhat has been tested and works in these OS:
  ** Mac OS X El Capitan 10.11.6
  ** Windows 10
  ** Ubuntu 16.04 LTS
  
  
## Dependencias paso a paso para cada plataforma

*Fecha*: 11/2016

###Nota general:
Python: versión 3.4.x debido a que PySide via pip install a la fecha soporta versiones < 3.5 (en linux esta disponible para py3.5 pero vía apt-get, no vía pip)

RtMidi: 0.5b o 1.0 dependiendo de la plataforma

Se dejan documentadas tachadas y/o en gris claro opciones que se probaron y no funcionan.
Al final se listan las versiones específicas usadas de cada programa.

## Mac OS
Testeada en ‘el capitán’ v10.11
Python version: 3.4.5

* Instalar Xcode tools (vía Mac App Store)

* Asegurarse de instalar también las Command Line Tools (ver Xcode -> Preferences -> Downloads)

  $ xcode-select --install

* Instalar brew

  *   $ ruby -e "  $(curl -fsSL
https://raw.githubusercontent.com/Homebrew/install/master/install)"

  $ brew install wget

* WARNING: Intentar instalar python vía brew instala py3.5 y pip install PySide no es compatible (hasta py3.4)


* Instalar Python 3.4
Opciones con problemas:
* Via archivo .dmg 3.4.0 y superiores dentro de 3.4.x
* Compilando (problemas con openssl) 3.4.0 y superiores dentro de 3.4.x


* Instalar mac ports https://guide.macports.org/

  $ wget https://distfiles.macports.org/MacPorts/MacPorts-2.3.4-10.11-ElCapitan.pkg

  $ sudo port install python34

  $ sudo port install py34-readline

  $ sudo port install py34-pip

  $ sudo port select --set pip pip34

* virtualenv

  $ sudo pip install virtualenv

* Probar con el terminal si reconoce el comando "virtualenv"

* Si no funciona porque no encuentra el comando virtualenv, hacer

  $ sudo pip install virtualenv

  $ sudo /usr/bin/easy_install virtualenv

  $ virtualenv -p python3.4 yaeltex-py3.4.5

  $ source yaeltex-py3.4.5/bin/activate

* RtMidi

  $ brew install rtmidi # lib en c

* (@yaeltex-py3.4.5) rtmidi bindings para py versión python-rtmidi-0.5b1

* la 1.0.0 problema con threads

  $ wget https://pypi.python.org/packages/6f/39/f7f52c432d4dd95d27703608af11818d99db0b2163cec88958efcf7c10cf/python-rtmidi-0.5b1.zip#md5=dba5808d78c843254455efb147fe87b2

  $ unzip python-rtmidi-0.5b1.zip

  $ cd python-rtmidi-0.5b1

  $ python setup.py install

* cmake

  $ brew install cmake

* Lo siguiente instala qt5 y no sirve

  $ brew install qt

* No funciona tampoco compilar desde los fuentes, tira un error de linker

* Instalar con MacPorts

  $ sudo port install qt4-mac

* Pyside (demora, compila los bindings para qt, el -v verbose para ver paso a paso)

* Lo siguiente no funciona, no encuentra qmake

  $ pip install PySide -v # version 1.2.4

* Descargar los fuentes de PySide

  $ wget https://pypi.python.org/packages/source/P/PySide/PySide-1.2.4.tar.gz

* Extraer

  $ tar -xvzf PySide-1.2.4.tar.gz

* Moverse al directorio extraído

  $ cd PySide-1.2.4

* Generar el wheel, indicando el directorio de qmake

  $ python setup.py bdist_wheel --qmake="/opt/local/libexec/qt4/bin/qmake"

* Instalar el wheel

  $ sudo pip install dist/PySide-1.2.4-cp34-cp34m-macosx_10_11_x86_64.whl -v

* Patchear pyside: cpython, shiboken, qtcore, qtgui fix

  $ export ENV_PATH=~/Virtualenvs/yaeltex-env-py3.4/lib/python3.4/site-packages/PySide/

  $ sudo install_name_tool -change @rpath/libpyside.cpython-34m.1.2.dylib   $ENV_PATH/libpyside.cpython-34m.1.2.dylib   $ENV_PATH/QtCore.so 


* pyside, libshiboken and qtcore fix

  $ sudo install_name_tool -change @rpath/libshiboken.cpython-34m.1.2.dylib    $ENV_PATH/libshiboken.cpython-34m.1.2.dylib   $ENV_PATH/QtCore.so 


  $ sudo install_name_tool -change @rpath/libshiboken.cpython-34m.1.2.dylib    $ENV_PATH/libshiboken.cpython-34m.1.2.dylib   $ENV_PATH/libpyside.cpython-34m.1.2.dylib 


  $ sudo install_name_tool -change @rpath/libpyside.cpython-34m.1.2.dylib   $ENV_PATH/libpyside.cpython-34m.1.2.dylib   $ENV_PATH/QtGui.so  


  $ sudo install_name_tool -change @rpath/libshiboken.cpython-34m.1.2.dylib    $ENV_PATH/libshiboken.cpython-34m.1.2.dylib   $ENV_PATH/QtGui.so


* py2app (bundle build)

* Instalar py2app con bug fix working with a newer version of ModuleGraph

  $ pip install -U git+https://github.com/metachris/py2app.git@master


* Construir bundle

  $ python setup_mac.py py2app


###Detalle de versiones (pip y brew list)
(yaeltex-py3.4.5)  $ brew list --versions

autoconf 2.69

cmake 3.6.2

pkg-config 0.29.1_2

pyenv 1.0.2_1

qt 4.8.7_2

readline 7.0

rtmidi 2.1.1


(yaeltex-py3.4.5)  $ pip list
altgraph (0.12)
macholib (1.7)
modulegraph (0.12.1)
pip (9.0.1)
py2app (0.10)
PySide (1.2.4)
python-rtmidi (0.5b1)
setuptools (28.8.0)
wheel (0.30.0a0)


## Windows
Testeada en Windows 10


### Instalar Python 3.4
Bajar https://www.python.org/ftp/python/3.4.0/python-3.4.0.amd64.msi e instalar (en la configuración marcar que se agregue al PATH)

### VirtualEnv
* Abrir una consola (cmd)

  $ pip install penv


* Crear virtualenv

  $ python -m venv yaeltex-env-py3.4


* activar

  $ yaeltex-env-py3.4\Scripts\activate.bat


### cython

  $ pip install Cython

### setuptools

  $ pip install -U setuptools

### rtmidi 

* python rtmidi version 1.0.0rc1

*Lo siguiente no funciona, tampoco la versión 0.5b

  $ pip install python_rtmidi 

*Hay que compilar la librería

  $ wget https://pypi.python.org/packages/70/00/4245aedfa5d352cdb086b3a7f329e0446bd13995d2ef69fe3c2a46ca6cee/python-rtmidi-1.0.0rc1.zip#md5=f490ee1a6f8b8e83da3632fe42a203c3

  $ unzip python-rtmidi-1.0.0rc1.zip

Compilar rtmidi con Visual Studio 2015 Community Edition no funciona. Hay que instalar el Visual C++ 2010 Express de la siguiente forma:
* Bajar e instalar http://download.microsoft.com/download/1/D/9/1D9A6C0E-FC89-43EE-9658-B9F0E3A76983/vc_web.exe
* Desinstalar todo los paquetes “Microsoft Visual C++ 2010 Redistributable”
* Instalar el SDK 7.1, pero en windows 10 el instalador web se confunde con las dependencias de .net y  framework 4, entonces hay que bajar el .iso (https://download.microsoft.com/download/F/1/0/F10113F5-B750-4969-A255-274341AC6BCE/GRMSDKX_EN_DVD.iso, chequear que sea GRMSDKX_EN_DVD.iso , la X es de 64 bits) montarlo e instalar desde ahi. NO usar el setup.exe que esta en el raiz, sino Setup\SDKSetup.exe
* Ir al inicio y abrir una consola “Windows SDK 7.1 Command Prompt” (C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Microsoft Windows SDK v7.1\Windows SDK 7.1 Command Prompt) Que ejecuta: C:\Windows\System32\cmd.exe /E:ON /V:ON /T:0E /K "C:\Program Files\Microsoft SDKs\Windows\v7.1\Bin\SetEnv.cmd"
Nota: Sobre este problema en la web hay mucho escrito, pero para más referencia sobre como instalar dependencias con python 3.4 en Windows10, esto creo que es lo mejorcito:
https://blog.ionelmc.ro/2014/12/21/compiling-python-extensions-on-windows/
y
http://haypo-notes.readthedocs.io/python.html#build-a-python-wheel-package-on-windows


* Desde una consola “Windows SDK 7.1 Command Prompt” hacer:

* activar

  $ yaeltex-env-py3.4\Scripts\activate.bat

  $ cd python-rtmidi-1.0.0rc1.zip

(@Yaeltex-env-py3.4)  $ python setup.py install

### PySide y Qt

* Pyside (demora, compila los bindings para qt, el -v verbose para ver paso a paso)

* Bajar e instalar qt 4.8 : https://download.qt.io/archive/qt/4.8/4.8.4/qt-win-opensource-4.8.4-vs2010.exe

* Agregar a la variable de entorno PATH, la ruta C:\Qt\4.8.4\bin

* Probar instalar PySide con pip

  $ pip install -U PySide

* Si no funciona, bajar PySide como wheel precompilado http://www.lfd.uci.edu/~gohlke/pythonlibs/#pyside

  $ wget http://www.lfd.uci.edu/~gohlke/pythonlibs/dp2ng7en/PySide-1.2.2-cp34-none-win_amd64.whl

(@Yaeltex-env-py3.4)  $ pip install PySide-1.2.2-cp34-none-win_amd64.whl


### PyInstaller

  $ pip install PyInstaller

* Si no funca porque pywin32 no se instala correctamente vía pip en windows 10, upgradear pip con la siguiente linea

  $ python -m pip install --upgrade pip

* Luego repetir pip install

  $ pip install PyInstaller

* Si nada de lo anterior funciona, probar entonces instalar este último vía wheel

  $ wget https://pypi.python.org/packages/8f/da/36439654abd8f39bcad0664c68674a41b838ca902da440defde17abbeade/pypiwin32-219-cp34-none-win_amd64.whl#md5=110e2769da6659c270b8e6e4595155eb

  $ pip install pypiwin32-219-cp34-none-win_amd64.whl

(@Yaeltex-env-py3.4)  $ pip install PyInstaller

### Bundle en Windows

(@Yaeltex-env-py3.4)$ python -m PyInstaller kwt_win.spec


### Detalle de versiones (pip list)

Cython (0.24.1)

future (0.16.0)

pefile (2016.3.28)

pip (1.5.4)

PyInstaller (3.2)

pypiwin32 (219)

PySide (1.2.2)

python-rtmidi (1.0.0rc1)

setuptools (28.8.0)

Shiboken (1.2.2)

wheel (0.29.0)

# Linux
Testeado en Ubuntu 16.04.1 y 14.04
3 opciones (con y sin virtualenv). Recomiendo la opción B

## A. Modo virtual-env compilación completa Python 3.4.0

* Python 3.4.0 (versión original)
Nota: hay que bajar y compilar la versión 3.4.0 porque en los repositorios esta la 3.5 que por lo menos en este momento no es compatible con PySide compilado vía pip “only these python versions are supported: [(2, 6), (2, 7), (3, 2), (3, 3), (3, 4)]”

  $ wget https://www.python.org/ftp/python/3.4.0/Python-3.4.0.tgz

  $ tar -xf Python-3.4.0.tgz

  $ cd Python-3.4.0

  $ sudo apt-get install build-essential

* Activar zlib y ssl

  $ sudo apt-get install zlib1g-dev libssl-dev

  $ vi /Modules/Setup

Descomentar las líneas:

zlib zlibmodule.c -I  $(prefix)/include -L  $(exec_prefix)/lib -lz

SSL=/usr/local/ssl
_ssl _ssl.c \
   -DUSE_SSL -I  $(SSL)/include -I  $(SSL)/include/openssl \
   -L  $(SSL)/lib -lssl -lcrypto

* Enable shared para poder compilar pyside al instalar vía pip

  $ ./configure --enable-shared

  $ make -j3

  $ sudo make install

  $ export LD_LIBRARY_PATH=/usr/local/lib 

* Para que lo anterior sea permanente, editar .bashrc y agregar la línea

  $ vi ~/.bashrc
   Agregar al final: export LD_LIBRARY_PATH=  $LD_LIBRARY_PATH:/usr/local/lib

* Virtualenv:

  $ sudo apt install virtualenv

  $ virtualenv -p python3.4 yaeltex-env

  $ source yaeltex-env/bin/activate

* (@yaeltex-env) rtmidi:

  $ sudo apt install librtmidi-dev # y dependencias

  $ wget https://pypi.python.org/packages/70/00/4245aedfa5d352cdb086b3a7f329e0446bd13995d2ef69fe3c2a46ca6cee/python-rtmidi-1.0.0rc1.zip#md5=f490ee1a6f8b8e83da3632fe42a203c3

  $ unzip python-rtmidi-1.0.0rc1.zip

  $ cd python-rtmidi-1.0.0rc1

  $ python setup.py install

* (@yaeltex-env) pyside

  $ sudo apt install cmake

  $ sudo apt-get install qt4-qmake qt-sdk

  $ sudo apt-get install libxml++2.6-dev libxslt1-dev

  $ pip install sphinx

  $ pip install pyside

## B. Módo mixto virtualenv + apt-get (python 3.5) (recomendado):

  $ sudo apt install virtualenv

  $ virtualenv -p python3.5 yaeltex-env

  $ source yaeltex-env/bin/activate

* (@yaeltex-env) rtmidi:

  $ sudo apt install librtmidi-dev

  $ wget https://pypi.python.org/packages/6f/39/f7f52c432d4dd95d27703608af11818d99db0b2163cec88958efcf7c10cf/python-rtmidi-0.5b1.zip#md5=dba5808d78c843254455efb147fe87b2

  $ unzip python-rtmidi-0.5b1.zip

  $ cd python-rtmidi-0.5b1/

  $ sudo python setup.py install

* (@yaeltex-env) pyside

  $ sudo apt-get install python3-pyside.qtgui python3-pyside.qtcore

  $ ln -s /usr/lib/python3/dist-packages/PySide/ yaeltex-env/lib/python3.5/site-packages/



## C. Modo rápido (python3.5 SIN virtualenv):
        * Funciona en ubuntu 16.04, pero en 14.04 por ejemplo no

* Sin virtual-env y python3.5 (dependencias en el sistema)

  $ sudo apt-get install python3-pyside.qtgui python3-pyside.qtcore

  $ sudo pip3 install python_rtmidi # o bajando zip y compilando


* Ejecutar

  $ python kilowhat.py #o python3 si no se esta en el virtualenv


* PyInstaller

  $ pip3 install pyinstaller


* Armar bundle para distribución:

  $ python -m PyInstaller kwt_linux.spec


### Detalle de versiones (pip list)

Python3.4 o 3.5

pip (8.1.2)

pkg-resources (0.0.0)

python-rtmidi (1.0.0rc1)

setuptools (28.4.0)

wheel (0.30.0a0)
