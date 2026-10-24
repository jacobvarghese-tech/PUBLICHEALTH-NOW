let meta = #{
    name: "lane-far",
    description: "Watch zero rank, payment gap, year change, and code concentration",
    when_to_use: "Check the far-off column lanes. /lane-far",
    phases: [
        #{ title: "Watch", detail: "read-only check of the far-off scorers" },
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
let prompt = "You watch the far-off lanes for " + base + ". You may write only models/far_state.json. ";
prompt += "Read models/work_clock.json, models/zero_rank_note.txt, models/payment_gap_note.txt, models/year_change_note.txt, and models/code_concentration_note.txt if it exists. ";
prompt += "List python processes whose command line contains zero_rank.py, payment_gap.py, year_change.py, or code_concentration.py. ";
prompt += "Write models/far_state.json with status and reason. status is leave when one of those scripts is writing a file or printing a year line. ";
prompt += "status is stalled when a year list or a rule list has ended before 6:00 a.m. local on 2026-10-24. Name the finished script in reason so the director can refill it. ";
prompt += "Do not start a script. Do not edit app/. ";
prompt += "A high score means resemblance to later fraud-type exclusions. Do not say the firm committed fraud.";
let watched = agent(prompt, #{
    label: "far-watch",
    capability_mode: "read-write",
    model: "grok-4.7",
    output_schema: schema,
    phase: "Watch",
});
if watched != () && watched.success && watched.output != () {
    complete(watched.output);
}
complete(#{ status: "stalled", reason: "watch did not return" });
