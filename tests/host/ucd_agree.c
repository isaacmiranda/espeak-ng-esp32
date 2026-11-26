/*
 * SPDX-License-Identifier: GPL-3.0-or-later
 *
 * The functions the component redirects (FSD FR-ENG-04) against the desktop libc: prints
 * one line "<function> U+XXXX" for every code point in the covered ranges where the
 * upstream's ucd-tools and the desktop libc (glibc, locale C.UTF-8, the one the engine
 * selects) disagree.
 */
#include <locale.h>
#include <stdio.h>
#include <wctype.h>
#include <ucd/ucd.h>
int main(void)
{
    setlocale(LC_CTYPE, "C.UTF-8");
    struct { const char *n; int (*a)(wint_t); int (*b)(codepoint_t); } t[] = {
        {"alpha", iswalpha, ucd_isalpha}, {"alnum", iswalnum, ucd_isalnum}, {"upper", iswupper, ucd_isupper},
        {"lower", iswlower, ucd_islower}, {"punct", iswpunct, ucd_ispunct}, {"space", iswspace, ucd_isspace},
        {"digit", iswdigit, ucd_isdigit}};
    wint_t rs[][2] = {{0, 0x52F}, {0x1E00, 0x1EFF}};
    for (int i = 0; i < 7; i++) for (int r = 0; r < 2; r++) for (wint_t c = rs[r][0]; c <= rs[r][1]; c++)
        if (!!t[i].a(c) != !!t[i].b(c)) printf("%s U+%04X\n", t[i].n, c);
    return 0;
}
