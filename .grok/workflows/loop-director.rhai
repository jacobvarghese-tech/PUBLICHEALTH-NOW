let meta = #{
    name: "loop-director",
    description: "The only overseer that may end a lane, start a lane, or rewrite a loop",
    when_to_use: "Keep every scoring lane moving until 6:00 a.m. local. /loop-director",
    phases: [
        #{ title: "Read", detail: "one grok-4.7 read of the clock, the ledger, and the live fits" },
        #{ title: "Act", detail: "one repair or one start, then the ledger is rewritten" },
    ],
};

let read_schema = #{
    "type": "object",
    "required": ["past_clock", "best", "stalled_lane", "empty_lane", "reason"],
    "properties": #{
        "past_clock": #{ "type": "boolean" },
        "best": #{ "type": "integer" },
        "stalled_lane": #{ "type": "string" },
        "empty_lane": #{ "type": "string" },
        "reason": #{ "type": "string" },
    },
};

let act_schema = #{
    "type": "object",
    "required": ["changed", "best", "note"],
    "properties": #{
        "changed": #{ "type": "boolean" },
        "best": #{ "type": "integer" },
        "note": #{ "type": "string" },
    },
};

let base = "C:/Users/Jacob/Downloads/congressional app";

phase("Read");
let look = "You are the loop director for " + base + ". Read, do not edit yet. ";
look += "Read models/work_clock.json, models/loop_ledger.json, models/model_island_db.json, and models/overseer_state.json. ";
look += "List python processes whose command line contains overnight_queue.py, model_islands.py, column_pack.py, combine_forest.py, zero_rank.py, payment_gap.py, year_change.py, code_concentration.py, grow_loop.py, blend_search.py, island_score.py, rank_evolve.py, harness_rank.py, meta_harness.py, label_islands.py, or rus_loop.py. ";
look += "The working stop is 6:00 a.m. local on 2026-10-24. Set past_clock true only when that clock has passed. ";
look += "Set best to best_confirm_top1 from models/model_island_db.json, or 26 if that key is missing. ";
look += "A lane is stalled when its last progress is older than 20 minutes and no child is writing a file, or when its process exited without a confirm line, or when its status is idle while its command can still run. A printed WAIT line from grow_loop.py is a heartbeat, not a stall. ";
look += "Set stalled_lane to the stalled lane name, or to none. Set empty_lane to a lane whose list is finished and whose clock has not passed, or to none. ";
look += "Put the evidence in reason. ";
look += "A high score means resemblance to later fraud-type exclusions. Do not say the firm committed fraud.";
let decision = agent(look, #{
    label: "read",
    capability_mode: "read-only",
    model: "grok-4.7",
    output_schema: read_schema,
    phase: "Read",
});

phase("Act");
let past_text = "false";
let best = 26;
let stalled = "none";
let empty = "none";
let reason = "read did not return";
if decision != () && decision.success && decision.output != () {
    if decision.output.past_clock == true {
        past_text = "true";
    }
    if decision.output.best != () {
        best = decision.output.best;
    }
    if decision.output.stalled_lane != () {
        stalled = decision.output.stalled_lane;
    }
    if decision.output.empty_lane != () {
        empty = decision.output.empty_lane;
    }
    if decision.output.reason != () {
        reason = decision.output.reason;
    }
}

let fix = "You are the loop director for " + base + ". You are the only agent that may end a lane, start a lane, or rewrite a loop. ";
fix += "The read says past_clock=" + past_text + " best=" + best.to_string() + " stalled_lane=" + stalled + " empty_lane=" + empty + " reason=" + reason + ". ";
fix += "If past_clock is true, write status done on every lane in models/loop_ledger.json and do not start anything. Do not kill a fit whose output file is still growing. ";
fix += "If past_clock is false and stalled_lane is not none, do one repair for that lane: restart the exited command, or edit the script that rejected a legal spec, or write the next spec and start it. One repair only. ";
fix += "If past_clock is false and stalled_lane is none and empty_lane is not none, refill that lane with the next unused unit and start it. An empty queue is not a reason to leave the lane idle. ";
fix += "If every lane is moving, write last_action leave in models/overseer_state.json and do not start a second copy of a moving fit. ";
fix += "You may edit scripts/overnight_queue.py, scripts/grow_loop.py, scripts/model_islands.py, scripts/column_pack.py, scripts/combine_forest.py, scripts/zero_rank.py, scripts/feature_islands.py, scripts/island_score.py, scripts/rank_evolve.py, scripts/harness_rank.py, scripts/meta_harness.py, scripts/label_islands.py, scripts/rus_loop.py, scripts/blend_search.py, scripts/payment_gap.py, scripts/year_change.py, scripts/code_concentration.py, and files in .grok/workflows/. ";
fix += "You may write models/specs, models/column_packs, models/zero_rules, models/label_specs, models/loop_ledger.json, and models/overseer_state.json. ";
fix += "Do not edit app/. Do not replace models/paper_forest.joblib. Do not put 2023 or 2024 in fit_years. ";
fix += "Do not lower a validator unless a test covers the new bound. Do not kill a process whose CPU is moving or whose output file is growing. ";
fix += "Do not start a second fit of a spec that is already running. Two model_islands.py fits do not run together. ";
fix += "Lanes that do not fit may run beside one forest fit. Those lanes are blend, islands, rank-evolve, harness-rank, meta-harness, zero-rank, payment-gap, year-change, and code-concentration. ";
fix += "If you edit a script, run the matching unittest file when one exists. ";
fix += "Write models/overseer_state.json with last_action, best, and a one-line note. Update models/loop_ledger.json so no lane is idle with an empty queue before the clock. ";
fix += "Return changed true if you edited a script, refilled a lane, or started a command. Return best as the database best_confirm_top1. Put what you did in note. ";
fix += "A high score means resemblance to later fraud-type exclusions. Do not say the firm committed fraud.";
let changed = agent(fix, #{
    label: "act",
    capability_mode: "execute",
    model: "grok-4.7",
    output_schema: act_schema,
    phase: "Act",
});
if changed != () && changed.success && changed.output != () {
    complete(changed.output);
}
complete(#{ changed: false, best: best, note: "act agent did not return" });
