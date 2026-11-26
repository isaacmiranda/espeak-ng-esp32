/* SPDX-License-Identifier: GPL-3.0-or-later */
/* Host harness for the async layer's state table (FSD 15.2).
 * stdin line: <STATE> <waiting> <capacity> <EVENT>;  stdout: <STATE> <waiting> <RESULT> <ACTIONS|->. */
#include <stdio.h>
#include <string.h>

#include "espk_fsm.h"

int main(void)
{
    char st[32], ev[32];
    int waiting, cap;
    while (scanf("%31s %d %d %31s", st, &waiting, &cap, ev) == 4) {
        espk_fsm_t f = {.state = espk_fsm_state_from_name(st), .waiting = waiting, .capacity = cap};
        espk_fsm_step_t r = espk_fsm_step(&f, espk_fsm_event_from_name(ev));
        char acts[160];
        espk_fsm_actions_str(r.actions, acts, sizeof acts);
        printf("%s %d %s %s\n", espk_fsm_state_name(f.state), f.waiting, espk_fsm_result_name(r.result), acts);
    }
    return 0;
}
