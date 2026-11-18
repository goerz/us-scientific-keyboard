.PHONY: all macos keyman windows cheatsheet docs fonts test clean

# Everything is generated from layout.toml by the layoutgen package.
SOURCES = layout.toml $(shell find src/layoutgen -type f -not -name '*.pyc')
LAYOUTGEN = uv run --quiet layoutgen
KMC = npx -y @keymanapp/kmc@18.0.255
ID = us_scientific
DLL = kbdussci

all: macos keyman windows cheatsheet

test: $(FONT)
	uv run --quiet pytest

# JuliaMono (SIL Open Font License) for the diagrams and the cheat sheet,
# from https://github.com/cormullion/juliamono
JULIAMONO = v0.63.2
JULIAMONO_SHA256 = be6517295198ec5c92bdbaad42f4f6f8d83f921d80512b79f54fe036add95c0c
FONT = fonts/JuliaMono-Regular.ttf

fonts: $(FONT)

$(FONT):
	rm -rf fonts/download && mkdir -p fonts/download
	curl -sSfL -o fonts/download/JuliaMono-ttf.tar.gz \
	    https://github.com/cormullion/juliamono/releases/download/$(JULIAMONO)/JuliaMono-ttf.tar.gz
	echo "$(JULIAMONO_SHA256)  fonts/download/JuliaMono-ttf.tar.gz" | shasum -a 256 -c --quiet
	tar -xzf fonts/download/JuliaMono-ttf.tar.gz -C fonts JuliaMono-Regular.ttf LICENSE
	mv fonts/LICENSE fonts/JuliaMono-LICENSE
	rm -rf fonts/download

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

# Cheat sheet: diagrams as PDF, assembled with LuaLaTeX
cheatsheet: build/us-scientific.pdf

build/cheatsheet/cheatsheet.tex: $(SOURCES) $(FONT)
	rm -rf build/cheatsheet
	$(LAYOUTGEN) cheatsheet build/cheatsheet
	cd build/cheatsheet && for f in *.svg; do rsvg-convert -f pdf "$$f" -o "$${f%.svg}.pdf"; done

build/us-scientific.pdf: build/cheatsheet/cheatsheet.tex
	cd build/cheatsheet && lualatex -interaction=nonstopmode -halt-on-error cheatsheet.tex > /dev/null
	cp build/cheatsheet/cheatsheet.pdf $@

# README tables and diagrams (committed, so that GitHub shows them)
docs: $(SOURCES) $(FONT)
	$(LAYOUTGEN) docs

clean:
	rm -rf build
