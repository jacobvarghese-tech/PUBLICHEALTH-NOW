let meta = #{
    name: "lane-columns",
    description: "Watch column packs, the 357 combine, and feature sample",
    when_to_use: "Check whether the column lane is moving. /lane-columns",
    phases: [
        #{ title: "Watch", detail: "read-only check of column fits" },
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
let prompt = "You watch the columns lane for " + base + ". You may write only models/columns_state.json. ";
prompt += "Read models/work_clock.json, models/column_pack_note.txt, and models/loop_ledger.json. ";
prompt += "List python processes whose command line contains column_pack.py, combine_forest.py, or feature_islands.py. ";
prompt += "Write models/columns_state.json with status and reason. status is leave when a column fit is using CPU or writing a file, or when it is waiting because a forest fit is using the CPU. ";
prompt += "status is stalled when the column list is finished before 6:00 a.m. local on 2026-10-24 and no forest fit is blocking it. ";
prompt += "Do not start a fit. Do not download a CMS file. Do not edit app/. ";
prompt += "A high score means resemblance to later fraud-type exclusions. Do not say the firm committed fraud.";
let watched = agent(prompt, #{
    label: "columns-watch",
    capability_mode: "read-write",
    model: "grok-4.7",
    output_schema: schema,
    phase: "Watch",
});
if watched != () && watched.success && watched.output != () {
    complete(watched.output);
}
complete(#{ status: "stalled", reason: "watch did not return" });
