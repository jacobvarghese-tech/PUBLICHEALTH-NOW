let meta = #{
    name: "lane-forest",
    description: "Watch the forest-fit lane and write a state file",
    when_to_use: "Check whether the one forest fit is moving. /lane-forest",
    phases: [
        #{ title: "Watch", detail: "read-only check of the forest fit" },
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
let prompt = "You watch the forest lane for " + base + ". You may write only models/forest_state.json. ";
prompt += "Read models/work_clock.json, models/loop_ledger.json, and models/model_island_db.json. ";
prompt += "List python processes whose command line contains model_islands.py or overnight_queue.py. ";
prompt += "Write models/forest_state.json with status and reason. status is leave when a fit is using CPU or writing a file. ";
prompt += "status is stalled when no fit is running, the last progress is older than 20 minutes, or the queue would exit before 6:00 a.m. local on 2026-10-24. ";
prompt += "Do not start a fit. Do not edit a script. Do not edit app/. ";
prompt += "A high score means resemblance to later fraud-type exclusions. Do not say the firm committed fraud.";
let watched = agent(prompt, #{
    label: "forest-watch",
    capability_mode: "read-write",
    model: "grok-4.7",
    output_schema: schema,
    phase: "Watch",
});
if watched != () && watched.success && watched.output != () {
    complete(watched.output);
}
complete(#{ status: "stalled", reason: "watch did not return" });
