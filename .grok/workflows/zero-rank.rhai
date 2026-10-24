let meta = #{
    name: "zero-rank",
    description: "Rank the zero-score rows with line-level columns already on disk",
    when_to_use: "Separate the page-forest zeros without another tree setting. /zero-rank",
    phases: [
        #{ title: "Rank", detail: "one rule at a time, 2023 selection year" },
    ],
};

let fit_schema = #{
    "type": "object",
    "required": ["captured", "note"],
    "properties": #{
        "captured": #{ "type": "integer" },
        "note": #{ "type": "string" },
    },
};

let jobs = ["01", "02", "03", "04", "05", "06", "07", "08"];
let base = "C:/Users/Jacob/Downloads/congressional app";
let best = 0;

phase("Rank");
for job in jobs {
    let room = budget();
    if room.remaining < 1 {
        log("zero rank stopped with no agent budget left");
        break;
    }
    let prompt = "Run this command and wait until it exits. Workspace: " + base + ". ";
    prompt += "py -3.14 scripts/zero_rank.py fit models/zero_rules/" + job + ".json. ";
    prompt += "This scores 2023 because 2024 column files are not on disk. Do not download a CMS file. Do not edit scripts/, app/, or models/paper_forest.joblib. ";
    prompt += "When it exits, read models/zero_rank_note.txt. Return captured as the fraud count printed for the 2023 zero group. Put the last printed line in note. If the command fails, set captured to 0 and put the error in note. ";
    prompt += "A high score means resemblance to later fraud-type exclusions. Do not say the firm committed fraud.";
    let fitted = agent(prompt, #{
        label: "zero-" + job,
        capability_mode: "execute",
        model: "grok-4.5",
        output_schema: fit_schema,
        phase: "Rank",
    });
    if fitted != () && fitted.success && fitted.output != () && fitted.output.captured != () && fitted.output.captured > best {
        best = fitted.output.captured;
    }
    log("after zero rule " + job + " captured " + best.to_string());
}

complete(#{ captured: best });
