.PHONY: all macos keyman windows test clean

# Everything is generated from layout.toml by the layoutgen package.
SOURCES = layout.toml $(shell find src/layoutgen -type f -not -name '*.pyc')
LAYOUTGEN = uv run --quiet layoutgen
KMC = npx -y @keymanapp/kmc@18.0.255
ID = us_scientific
DLL = kbdussci

all: macos keyman windows

test:
	uv run --quiet pytest

# macOS: installable bundle, zipped for download
macos: build/$(ID).bundle.zip

build/$(ID).bundle: $(SOURCES) icon.icns
	$(LAYOUTGEN) bundle $@ --icon icon.icns
	touch $@

build/$(ID).bundle.zip: build/$(ID).bundle
	rm -f $@
	cd build && zip -q -r $(notdir $@) $(ID).bundle

# Keyman (Windows, macOS, Linux): compiled keyboard package
keyman: build/$(ID).kmp

build/keyman/$(ID).kmn: $(SOURCES)
	$(LAYOUTGEN) keyman build/keyman --license ../../LICENSE

build/keyman/$(ID).ico: icon.icns
	mkdir -p $(@D)
	sips -s format png $< --out $(@D)/icon.png > /dev/null
	magick $(@D)/icon.png -define icon:auto-resize=48,32,16 $@
	rm -f $(@D)/icon.png

build/keyman/$(ID).kmx: build/keyman/$(ID).kmn build/keyman/$(ID).ico
	$(KMC) build $< --out-file $@

build/$(ID).kmp: build/keyman/$(ID).kmx LICENSE
	$(KMC) build build/keyman/$(ID).kps --out-file $@

# Native Windows layout: source and scripts, zipped for building on Windows
windows: build/$(DLL)-src.zip

build/windows/$(DLL).c: $(SOURCES)
	$(LAYOUTGEN) windows build/windows

build/$(DLL)-src.zip: build/windows/$(DLL).c LICENSE
	cp LICENSE build/windows/LICENSE.txt
	rm -f $@
	cd build/windows && zip -q ../$(notdir $@) *

clean:
	rm -rf build
