project_name := tvfeed

INSTALL_PROGRAM := install
INSTALL_DATA := install -m 644

prefix := /usr/local
datarootdir := $(prefix)/share
exec_prefix := $(prefix)
bindir := $(exec_prefix)/bin
docdir := $(datarootdir)/doc/$(project_name)

.PHONY: all clean install uninstall

all:
	python3 setup.py bdist

clean:
	find "$(project_name)" -type d -name '__pycache__' | xargs $(RM) -r
	$(RM) -r build/ dist/ "$(project_name).egg-info/"

install:
	python3 setup.py install --root="$(or $(DESTDIR),/)" --prefix="$(prefix)"
	mkdir -p "$(DESTDIR)$(bindir)/"
	$(INSTALL_PROGRAM) "$(project_name)-command" \
	    "$(DESTDIR)$(bindir)/$(project_name)"
	mkdir -p "$(DESTDIR)$(docdir)/"
	$(INSTALL_DATA) README.md "$(DESTDIR)$(docdir)/"

uninstall:
	./uninstall "$(DESTDIR)" "$(prefix)"
	$(RM) -r "$(DESTDIR)$(bindir)/$(project_name)" "$(DESTDIR)$(docdir)/"
