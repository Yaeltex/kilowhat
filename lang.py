###################################################################################
# Original code by Martin Sebastian Wain for YAELTEX - 2016
# Revisions by Hernan Ordiales and Franco Grassano - 2016/2017
###################################################################################


#print("LANG")

# Placeholder for internationalization
#def _(x):
#	return x

from os import listdir
import os
from os.path import isfile, join, split, splitext, abspath

path = ('locales')
for root, __, files in os.walk(path):
	for f in files:
		pp=join(root, f)
		if isfile(join(root, f)):
			#fn, ext = splitext(f)
			#if ext == '.mo':
			if f == 'kwt.mo':
				lang = root.split(os.sep)[1]
				print("Found lang: " + lang)


import gettext
from PySide.QtCore import QLocale

#import platform
#if platform.system() == "Darwin":
#TODO: Do some shit to make fonts work...

print("Lang handler")

try:
	#QLocale.setDefault(QLocale("es"))
	#current_locale, encoding = locale.getdefaultlocale()

	es = gettext.translation('kwt', localedir='./locales/', languages=['es'])
	#es = gettext.translation('kwt', localedir='locales/', languages=[current_locale])
	es.install()
except Exception as le:
	print("Couldn't load language file, using default", le)
	try:
		__builtins__["_"] = lambda x: x
	except:
		try:
			__builtins__._ = lambda x: x
		except:
			pass


print("Lang handler OK")