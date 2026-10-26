let meta = #{
    name: "score-overseer",
    description: "Check the scoring loops and change a stuck one",
    when_to_use: "Keep scoring moving without asking. /score-overseer",
    phases: [
        #{ title: "Decide", detail: "read scores and running fits" },
        #{ title: "Change", detail: "edit a stuck loop or start the next fit" },
    ],
};

let decision_schema = #{
    "type": "object",
    "required": ["action", "best", "reason"],
    "properties": #{
        "action": #{ "type": "string" },
        "best": #{ "type": "integer" },
        "reason": #{ "type": "string" },
    },
};

let change_schema = #{
    "type": "object",
    "required": ["changed", "best", "note"],
    "properties": #{
        "changed": #{ "type": "boolean" },
        "best": #{ "type": "integer" },
        "note": #{ "type": "string" },
    },
};

let base = "C:/Users/Jacob/Downloads/congressional app";

phase("Decide");
let look = "You are the scoring overseer for " + base + ". Read, do not edit yet. ";
look += "Read models/model_island_db.json, models/model_island_note.txt, models/feature_island_note.txt, models/column_pack_note.txt, models/zero_rank_note.txt, and models/overseer_state.json if it exists. ";
look += "List python processes whose command line contains model_islands.py, feature_islands.py, column_pack.py, combine_forest.py, or zero_rank.py. ";
look += "Return action as one of: leave, restart, switch, edit. ";
look += "The working stop is 6:00 a.m. local on 2026-10-24 in models/work_clock.json. An empty queue before that clock is a stall, not a leave. ";
look += "leave means a fit is running and its files or CPU are moving, or the last change was under 10 minutes ago. ";
look += "A spec number with no file was never assigned. Do not search for it and do not call it a failed fit. ";
look += "restart means a fit exited with an error and that spec has no confirm line. ";
look += "switch means the forest-setting search is idle and the last 20 scores did not beat best_confirm_top1. The next work is a column pack or a 357 combine, not another near-357 tree spec. ";
look += "edit means the same error happened twice, a script rejected a legal spec, or a loop is stuck on a missing file it could build from columns already on disk. ";
look += "Return best as best_confirm_top1, or 25 if that key is missing. Put the reason in reason. ";
look += "A high score means resemblance to later fraud-type exclusions. Do not say the firm committed fraud.";
let decision = agent(look, #{
    label: "decide",
    capability_mode: "read-only",
    model: "grok-4.7",
    output_schema: decision_schema,
    phase: "Decide",
});

phase("Change");
let seen = 26;
if decision != () && decision.success && decision.output != () && decision.output.best != () {
    seen = decision.output.best;
}
if decision != () && decision.success && decision.output != () && decision.output.action == "leave" {
    log("overseer left the running fits alone");
    complete(#{ changed: false, best: seen, note: "leave" });
}
if decision == () || !decision.success || decision.output == () {
    log("decide did not return; change step will check the fits");
}

let action = "check";
let reason = "decide did not return";
if decision != () && decision.success && decision.output != () {
    action = decision.output.action;
    reason = decision.output.reason;
}
let fix = "You are the scoring overseer for " + base + ". You may edit loops. The decision is action=" + action + " reason=" + reason + ". ";
fix += "If action is check, list the scoring python processes first. Leave them if one is using CPU or writing a file. If none is running, start the next unscored spec in models/specs from 610 upward with scripts/model_islands.py. ";
fix += "Do that one change, then start at most one fit. ";
fix += "You may edit scripts/column_pack.py, scripts/combine_forest.py, scripts/zero_rank.py, scripts/feature_islands.py, scripts/model_islands.py, scripts/overnight_queue.py, and files in .grok/workflows/. ";
fix += "You may write models/column_packs, models/zero_rules, and models/specs. ";
fix += "Do not edit app/. Do not replace models/paper_forest.joblib. Do not put 2023 or 2024 in fit_years. ";
fix += "Do not download a CMS file while feature_islands.py is running. Do not kill a fit whose CPU is moving or whose output file is growing. ";
fix += "Do not start a second fit of a spec that is already running. Do not lower a validator unless a test covers the new bound. ";
fix += "If you edit a script, run the matching unittest file when one exists. ";
fix += "Write models/overseer_state.json with last_action, best, and a one-line note. ";
fix += "Return changed true if you edited a script or started a fit. Return best as the database best_confirm_top1. Put what you did in note. ";
fix += "A high score means resemblance to later fraud-type exclusions. Do not say the firm committed fraud.";
let changed = agent(fix, #{
    label: "change",
    capability_mode: "execute",
    model: "grok-4.7",
    output_schema: change_schema,
    phase: "Change",
});
if changed != () && changed.success && changed.output != () {
    complete(changed.output);
}
complete(#{ changed: false, best: 25, note: "change agent did not return" });
