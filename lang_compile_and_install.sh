# 1. poedit ( $ sudo apt-get install potool poedit )
# 2. update from source
# 3. edit translations
# 4. compile .mo -> $ msgfmt translation_es.po -o translation_es.mo
# 5. install -> $ cp translation_es.mo locales/es/LC_MESSAGES/kmgui.mo
echo ".mo generation"
msgfmt translation_es.po -o translation_es.mo

echo "install"
cp translation_es.mo locales/es/LC_MESSAGES/kmgui.mo

