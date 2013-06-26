MAINTAINERCLEANFILES = Makefile.in

pmctl_START   = $(PACKAGE_NAME)_start
pmctl_STOP    = $(PACKAGE_NAME)_stop
pmctl_MOVE    = $(PACKAGE_NAME)_move
pmctl_STATUS  = $(PACKAGE_NAME)_status
pmctl_SCRIPTS = $(pmctl_START).py $(pmctl_STOP).py $(pmctl_MOVE).py $(pmctl_STATUS).py

pmctldir      = $(prefix)/share/pacemaker/$(PACKAGE_NAME)
pmctllinkdir  = /usr/sbin

SPEC          = $(PACKAGE_NAME).spec
TARFILE       = $(PACKAGE_NAME)-$(VERSION).tar.gz
EXTRA_DIST    = $(pmctl_SCRIPTS) $(SPEC) autogen.sh

RPM_ROOT      = $(shell pwd)
RPMBUILDOPTS  = --define "_sourcedir $(RPM_ROOT)" --define "_specdir $(RPM_ROOT)"

install-data-hook:
	@$(NORMAL_INSTALL)
	test -z $(pmctldir) || $(mkdir_p) $(DESTDIR)$(pmctldir)
	$(INSTALL_SCRIPT) $(pmctl_SCRIPTS) $(DESTDIR)$(pmctldir)
	test -z $(pmctllinkdir) || $(mkdir_p) $(DESTDIR)$(pmctllinkdir)
	ln -sf $(pmctldir)/$(pmctl_START).py  $(DESTDIR)$(pmctllinkdir)/$(pmctl_START)
	ln -sf $(pmctldir)/$(pmctl_STOP).py   $(DESTDIR)$(pmctllinkdir)/$(pmctl_STOP)
	ln -sf $(pmctldir)/$(pmctl_MOVE).py   $(DESTDIR)$(pmctllinkdir)/$(pmctl_MOVE)
	ln -sf $(pmctldir)/$(pmctl_STATUS).py $(DESTDIR)$(pmctllinkdir)/$(pmctl_STATUS)


uninstall-local:
	rm -rf $(pmctllinkdir)/$(pmctl_START)
	rm -rf $(pmctllinkdir)/$(pmctl_STOP)
	rm -rf $(pmctllinkdir)/$(pmctl_MOVE)
	rm -rf $(pmctllinkdir)/$(pmctl_STATUS)

$(TARFILE):
	$(MAKE) dist

srpm: clean
	rm -f $(TARFILE)
	$(MAKE) $(SPEC) $(TARFILE)
	rpmbuild $(RPMBUILDOPTS) --nodeps -bs --rmsource $(SPEC)

rpm: clean
	rm -f $(TARFILE)
	$(MAKE) $(SPEC) $(TARFILE)
	rpmbuild $(RPMBUILDOPTS) -ba --rmsource $(SPEC)

