let meta = #{
    name: "lane-islands",
    description: "Watch the island scorer generation",
    when_to_use: "Check whether the island generation is moving toward 30 of 48. /lane-islands",
    phases: [
        #{ title: "Watch", detail: "read-only check of island_score.py" },
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
let prompt = "You watch the islands lane for " + base + ". You may write only models/islands_state.json. ";
prompt += "Read models/work_clock.json, models/island_db.json, and harness/islands/lesson.txt if it exists. ";
prompt += "List python processes whose command line contains island_score.py. ";
prompt += "Write models/islands_state.json with status and reason. status is leave when a generation is scoring. ";
prompt += "status is stalled when no generation is running and best_confirm_top1 is still below 30 and the clock is before 6:00 a.m. local on 2026-10-24. ";
prompt += "Do not start a generation. Do not edit a score_rows.py file. Do not edit app/. ";
prompt += "A high score means resemblance to later fraud-type exclusions. Do not say the firm committed fraud.";
let watched = agent(prompt, #{
    label: "islands-watch",
    capability_mode: "read-write",
    model: "grok-4.7",
    output_schema: schema,
    phase: "Watch",
});
if watched != () && watched.success && watched.output != () {
    complete(watched.output);
}
complete(#{ status: "stalled", reason: "watch did not return" });
