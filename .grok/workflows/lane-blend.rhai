let meta = #{
    name: "lane-blend",
    description: "Watch the blend and grow loop",
    when_to_use: "Check whether grow_loop is waiting or dead. /lane-blend",
    phases: [
        #{ title: "Watch", detail: "read-only check of the blend loop" },
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
let prompt = "You watch the blend lane for " + base + ". You may write only models/blend_state.json. ";
prompt += "Read models/work_clock.json and models/grow_tried.json if it exists. ";
prompt += "List python processes whose command line contains grow_loop.py or blend_search.py. ";
prompt += "Write models/blend_state.json with status and reason. status is leave when grow_loop.py is running, including when its last line is WAIT for a new saved forest. That wait is a heartbeat. ";
prompt += "status is stalled when neither script is running and the clock is still before 6:00 a.m. local on 2026-10-24. ";
prompt += "Do not start a script. Do not edit app/. Do not open models/paper_forest.joblib for writing. ";
prompt += "A high score means resemblance to later fraud-type exclusions. Do not say the firm committed fraud.";
let watched = agent(prompt, #{
    label: "blend-watch",
    capability_mode: "read-write",
    model: "grok-4.7",
    output_schema: schema,
    phase: "Watch",
});
if watched != () && watched.success && watched.output != () {
    complete(watched.output);
}
complete(#{ status: "stalled", reason: "watch did not return" });
