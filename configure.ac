#                                               -*- Autoconf -*-
# Process this file with autoconf to produce a configure script.

AC_PREREQ(2.59)
AC_INIT(pm_ctl, 1.0)
AM_INIT_AUTOMAKE

AC_PREFIX_DEFAULT(/usr)

AM_PATH_PYTHON(2.4,,:)
AC_PATH_PROGS(PYTHON, python)
AC_MSG_CHECKING(where is python installed)
if test "x${PYTHON}" = x; then
	PYTHON="/usr/bin/env python";
fi
AC_MSG_RESULT(using $PYTHON);

if test "$prefix" = "NONE"; then
	prefix="/usr"
fi
eval prefix="`eval echo ${prefix}`"

AC_PROG_LN_S
AC_CONFIG_FILES(Makefile pm_ctl.spec)
AC_OUTPUT

AC_MSG_RESULT([])
AC_MSG_RESULT([${PACKAGE} configuration:])
AC_MSG_RESULT([])
AC_MSG_RESULT([  Version  = ${VERSION}])
AC_MSG_RESULT([  Prefix   = ${prefix}])

