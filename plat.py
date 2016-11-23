
import platform

_LINUX = (platform.system() == 'Linux')
_WINDOWS = (platform.system == 'Windows')
_MACOSX = (platform.system() == 'Darwin')

print(platform.system())

