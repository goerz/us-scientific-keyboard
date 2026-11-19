# Everything is generated from layout.toml by the layoutgen package.
SOURCES = layout.toml $(shell find src/layoutgen -type f -not -name '*.pyc')
LAYOUTGEN = uv run --quiet layoutgen
KMC = npx -y @keymanapp/kmc@18.0.255
ID = us_scientific
DLL = kbdussci

# JuliaMono (SIL Open Font License) for the diagrams and the cheat sheet,
# from https://github.com/cormullion/juliamono
JULIAMONO = v0.63.2
JULIAMONO_SHA256 = be6517295198ec5c92bdbaad42f4f6f8d83f921d80512b79f54fe036add95c0c
FONT = fonts/JuliaMono-Regular.ttf

.PHONY: help all macos keyman windows linux cheatsheet docs fonts test install uninstall install-keyman uninstall-keyman clean

.DEFAULT_GOAL := help

help:  ## Show this help
	@grep -E '^([a-zA-Z_-]+):.*## ' $(MAKEFILE_LIST) | awk -F ':.*## ' '{printf "%-17s %s\n", $$1, $$2}'

all: macos keyman windows linux cheatsheet  ## Build everything into build/

test: $(FONT)  ## Run the tests (generated layouts against layout.toml, README up to date)
	uv run --quiet pytest

fonts: $(FONT)  ## Download the JuliaMono font into fonts/

$(FONT):
	rm -rf fonts/download && mkdir -p fonts/download
	curl -sSfL -o fonts/download/JuliaMono-ttf.tar.gz \
	    https://github.com/cormullion/juliamono/releases/download/$(JULIAMONO)/JuliaMono-ttf.tar.gz
	echo "$(JULIAMONO_SHA256)  fonts/download/JuliaMono-ttf.tar.gz" | shasum -a 256 -c --quiet
	tar -xzf fonts/download/JuliaMono-ttf.tar.gz -C fonts JuliaMono-Regular.ttf LICENSE
	mv fonts/LICENSE fonts/JuliaMono-LICENSE
	rm -rf fonts/download

macos: build/$(ID).bundle.zip  ## Build the macOS bundle, zipped for download

build/$(ID).bundle: $(SOURCES) icon.icns
	$(LAYOUTGEN) bundle $@ --icon icon.icns
	touch $@

build/$(ID).bundle.zip: build/$(ID).bundle
	rm -f $@
	cd build && zip -q -r $(notdir $@) $(ID).bundle

keyman: build/$(ID).kmp  ## Build the Keyman package (Windows, macOS, Linux)

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

# Compiled on Windows (CI zips it with the DLLs as $(ID)-windows.zip)
windows: build/$(ID)-windows/$(DLL).c  ## Generate the native Windows layout (source and scripts) into a folder

build/$(ID)-windows/$(DLL).c: $(SOURCES) LICENSE
	rm -rf $(@D)
	$(LAYOUTGEN) windows $(@D)
	cp LICENSE $(@D)/LICENSE.txt

linux: build/$(ID)-linux.zip  ## Build the native Linux layout (XKB and Compose), zipped for download

build/$(ID)-linux/$(ID): $(SOURCES) LICENSE
	rm -rf $(@D)
	$(LAYOUTGEN) linux $(@D)
	cp LICENSE $(@D)/LICENSE.txt

build/$(ID)-linux.zip: build/$(ID)-linux/$(ID)
	rm -f $@
	cd build && zip -q -r $(notdir $@) $(ID)-linux

# Diagrams as PDF, assembled with LuaLaTeX
cheatsheet: build/us-scientific.pdf  ## Build the PDF cheat sheet

build/cheatsheet/cheatsheet.tex: $(SOURCES) $(FONT)
	rm -rf build/cheatsheet
	$(LAYOUTGEN) cheatsheet build/cheatsheet
	cd build/cheatsheet && for f in *.svg; do rsvg-convert -f pdf "$$f" -o "$${f%.svg}.pdf"; done

build/us-scientific.pdf: build/cheatsheet/cheatsheet.tex
	cd build/cheatsheet && lualatex -interaction=nonstopmode -halt-on-error cheatsheet.tex > /dev/null
	cp build/cheatsheet/cheatsheet.pdf $@

# Committed, so that GitHub shows them
docs: $(SOURCES) $(FONT)  ## Regenerate the README tables and docs/*.svg diagrams
	$(LAYOUTGEN) docs

# Install, as appropriate for the operating system: for the current user, or
# with SYSTEM=1 for all users (macOS; asks for the sudo password only for the
# copy, and removes the current user's copy)
UNAME := $(shell uname -s)
USER_LAYOUTS = $(HOME)/Library/Keyboard Layouts
ifdef SYSTEM
MACOS_LAYOUTS ?= /Library/Keyboard Layouts
SUDO = sudo
else
MACOS_LAYOUTS ?= $(USER_LAYOUTS)
SUDO =
endif

install:  ## Install the layout for this OS (SYSTEM=1 on macOS: for all users)
uninstall:  ## Remove the installed layout (SYSTEM=1 on macOS: for all users)

install-keyman: build/$(ID).kmp  ## Install the Keyman package instead (Linux, with Keyman for Linux)
	@command -v km-package-install > /dev/null || \
	    { echo "Install Keyman for Linux first: https://keyman.com/linux/"; exit 1; }
	km-package-install -f build/$(ID).kmp

uninstall-keyman:  ## Remove the Keyman package (Linux)
	km-package-uninstall $(ID)

ifeq ($(UNAME),Darwin)
install: build/$(ID).bundle
	$(SUDO) rm -rf "$(MACOS_LAYOUTS)/$(ID).bundle"
	$(SUDO) mkdir -p "$(MACOS_LAYOUTS)"
	$(SUDO) cp -R build/$(ID).bundle "$(MACOS_LAYOUTS)/"
	@if [ "$(MACOS_LAYOUTS)" != "$(USER_LAYOUTS)" ] && [ -e "$(USER_LAYOUTS)/$(ID).bundle" ]; then \
	    rm -rf "$(USER_LAYOUTS)/$(ID).bundle"; \
	    echo "Removed the copy in $(USER_LAYOUTS)."; \
	fi
	@echo "Installed $(ID).bundle in $(MACOS_LAYOUTS)."
	@swift tools/macos-activate.swift "$(MACOS_LAYOUTS)/$(ID).bundle" 2>&1 | grep -v '^Keyboard Layouts:' || true
	@echo "If an earlier version was installed, log out and back in for macOS to load this one."
	@for dir in "$(HOME)/Library/Keyboard Layouts" "/Library/Keyboard Layouts"; do \
	    if [ -e "$$dir/USScientific.bundle" ]; then \
	        echo "The predecessor is still installed; to remove it, run:"; \
	        echo "    $$( [ "$$dir" = "/Library/Keyboard Layouts" ] && echo 'sudo ' )rm -rf \"$$dir/USScientific.bundle\""; \
	    fi; \
	done

uninstall:
	$(SUDO) rm -rf "$(MACOS_LAYOUTS)/$(ID).bundle"
	@echo "Removed $(ID).bundle from $(MACOS_LAYOUTS); log out and back in to finish."
else ifeq ($(UNAME),Linux)
install: build/$(ID)-linux/$(ID)
	python3 build/$(ID)-linux/install.py

uninstall: build/$(ID)-linux/$(ID)
	python3 build/$(ID)-linux/install.py --uninstall
else
install uninstall:
	@echo "On Windows, either install Keyman (https://keyman.com/windows/) and"
	@echo "double-click build/$(ID).kmp (from 'make keyman'), or build and install the"
	@echo "native layout from build/$(DLL)-src.zip (from 'make windows') as described"
	@echo "in its README.txt."
endif

clean:  ## Remove build/
	rm -rf build
