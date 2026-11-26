// SPDX-License-Identifier: GPL-3.0-or-later
// FR-ENG-04 (issue espeak-ng#1611): the engine classifies wide characters with the libc's isw*
// functions (its own towlower2 already goes through ucd-tools). On the ESP32 the libc (newlib, C locale) knows no letter beyond ASCII, so
// accented text is spelled out. The linker sends those calls here (-Wl,--wrap=...), to the
// functions of the upstream's own ucd-tools, which agree with the desktop libc on Latin, Greek
// and Cyrillic (tests/host/test_ucd_agreement.py). The engine's sources are not touched.
#include <wctype.h>

#include "sdkconfig.h"

#ifdef CONFIG_ESPK_UCD_WRAP

#include "ucd/ucd.h"

int __wrap_iswalpha(wint_t c) { return ucd_isalpha(c); }
int __wrap_iswalnum(wint_t c) { return ucd_isalnum(c); }
int __wrap_iswupper(wint_t c) { return ucd_isupper(c); }
int __wrap_iswlower(wint_t c) { return ucd_islower(c); }
int __wrap_iswpunct(wint_t c) { return ucd_ispunct(c); }
int __wrap_iswspace(wint_t c) { return ucd_isspace(c); }
int __wrap_iswdigit(wint_t c) { return ucd_isdigit(c); }

#endif
