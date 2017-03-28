# -*- mode: python -*-

block_cipher = None


a = Analysis(['kilowhat.py'],
             pathex=['/home/nitram/Desktop/kmgui_linux'],
             binaries=None,
             datas=[('assets','assets'),('templates', 'templates'),('locales', 'locales'),('ioconfig.txt',''),('style-linux.css','')],
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
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='kilowhat')
