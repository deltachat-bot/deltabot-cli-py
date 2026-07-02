#!/bin/sh

cp icon.png manifest.toml _build/html/
cd _build/html/

PACKAGE_NAME="../../deltabot-cli-docs"
rm "$PACKAGE_NAME.xdc" 2> /dev/null
zip -9 --recurse-paths "$PACKAGE_NAME.xdc" --exclude "node_modules/*" package.json LICENSE README.md webxdc.js webxdc.d.ts "*~" "./*.sh" "./*.xdc" -- *

echo "success, archive contents:"
unzip -l "$PACKAGE_NAME.xdc"

# check package size
MAXSIZE=655360
size=$(wc -c < "$PACKAGE_NAME.xdc")
if [ "$size" -ge $MAXSIZE ]; then
    echo "WARNING: package size exceeded the limit ($size > $MAXSIZE)"
fi
