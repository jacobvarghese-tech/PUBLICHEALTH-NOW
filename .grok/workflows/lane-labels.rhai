let meta = #{
    name: "lane-labels",
    description: "Watch label islands and the rus loop",
    when_to_use: "Check the label and rus lanes. /lane-labels",
    phases: [
        #{ title: "Watch", detail: "read-only check of label and rus fits" },
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
let prompt = "You watch the label lanes for " + base + ". You may write only models/labels_state.json. ";
prompt += "Read models/work_clock.json, models/label_island_note.txt, and models/rus_loop/note.txt. ";
prompt += "List python processes whose command line contains label_islands.py or rus_loop.py. ";
prompt += "Write models/labels_state.json with status and reason. status is leave when one of those scripts is running. ";
prompt += "status is stalled when the rus loop has stopped at round 10 while the count is still at or below 26, or when label islands has stopped with unfitted specs that use a date rule and a code list already in the files, and the clock is before 6:00 a.m. local on 2026-10-24. ";
prompt += "Rejected specs stay rejected. Do not start a fit. Do not edit app/. ";
prompt += "A high score means resemblance to later fraud-type exclusions. Do not say the firm committed fraud.";
let watched = agent(prompt, #{
    label: "labels-watch",
    capability_mode: "read-write",
    model: "grok-4.7",
    output_schema: schema,
    phase: "Watch",
});
if watched != () && watched.success && watched.output != () {
    complete(watched.output);
}
complete(#{ status: "stalled", reason: "watch did not return" });
