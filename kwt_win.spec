# -*- mode: python -*-

block_cipher = None


a = Analysis(['kilowhat.py'],
             pathex=['C:\\developing\\PROJECTS\\projects16\\kmgui'],
             binaries=None,
             datas=[('locales', 'locales'), ('style.css',''), ('ioconfig.txt',''), ('assets', 'assets')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='kilowhat',
          debug=False,
          strip=False,
          upx=True,
          console=False )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='kilowhat')
