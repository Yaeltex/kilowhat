###################################################################################
# Original code by Martin Sebastian Wain for YAELTEX - 2016
# Revisions by Hernan Ordiales and Franco Grassano - 2016/2017
###################################################################################

import platform

_LINUX = (platform.system() == 'Linux')
_WINDOWS = (platform.system == 'Windows')
_MACOSX = (platform.system() == 'Darwin')

print(platform.system())

