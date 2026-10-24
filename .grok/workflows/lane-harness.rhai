let meta = #{
    name: "lane-harness",
    description: "Watch rank evolve, harness rank, and the meta harness",
    when_to_use: "Check the three harness lanes. /lane-harness",
    phases: [
        #{ title: "Watch", detail: "read-only check of the harness scripts" },
    ],
};

let schema = #{
    "type": "object",
    "required": ["status", "reason"],
    "properties": #{
        "status": #{ "type": "string" },
        "reason": #{ "type": "string" },
    },
};

let base = "C:/Users/Jacob/Downloads/congressional app";

phase("Watch");
let prompt = "You watch the harness lanes for " + base + ". You may write only models/harness_state.json. ";
prompt += "Read models/work_clock.json, models/rank_evolve_note.txt, models/harness_rank_note.txt, and models/meta_harness_note.txt. ";
prompt += "List python processes whose command line contains rank_evolve.py, harness_rank.py, or meta_harness.py. ";
prompt += "Write models/harness_state.json with status and reason. status is leave when one of those scripts is running. ";
prompt += "status is stalled when none is running and the clock is before 6:00 a.m. local on 2026-10-24. Name which script is idle in reason. ";
prompt += "Do not start a script. Do not edit app/. Do not write an API key into a file. ";
prompt += "A high score means resemblance to later fraud-type exclusions. Do not say the firm committed fraud.";
let watched = agent(prompt, #{
    label: "harness-watch",
    capability_mode: "read-write",
    model: "grok-4.7",
    output_schema: schema,
    phase: "Watch",
});
if watched != () && watched.success && watched.output != () {
    complete(watched.output);
}
complete(#{ status: "stalled", reason: "watch did not return" });
