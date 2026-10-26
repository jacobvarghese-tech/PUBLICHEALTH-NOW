let meta = #{
    name: "column-packs",
    description: "Refit forests on line-level columns already on disk",
    when_to_use: "Join the built feature columns and score them together. /column-packs",
    phases: [
        #{ title: "Pack", detail: "one pack at a time, no CMS download" },
    ],
};

let fit_schema = #{
    "type": "object",
    "required": ["best", "note"],
    "properties": #{
        "best": #{ "type": "integer" },
        "note": #{ "type": "string" },
    },
};

let jobs = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"];
let base = "C:/Users/Jacob/Downloads/congressional app";
let best = 25;

phase("Pack");
for job in jobs {
    if best >= 30 {
        break;
    }
    let room = budget();
    if room.remaining < 1 {
        log("column packs stopped with no agent budget left");
        break;
    }
    let prompt = "Run this command and wait until it exits. Workspace: " + base + ". ";
    prompt += "py -3.14 scripts/column_pack.py fit models/column_packs/" + job + ".json. ";
    prompt += "This fit reads data/feature_columns only. Do not download a CMS file. Do not edit scripts/, app/, or models/paper_forest.joblib. ";
    prompt += "If the command says confirm skipped, that is a finished result. ";
    prompt += "When it exits, read models/column_pack_db.json. Return best as best_confirm_top1 if that key exists, otherwise 25. Put the last printed line in note. ";
    prompt += "A high score means resemblance to later fraud-type exclusions. Do not say the firm committed fraud.";
    let fitted = agent(prompt, #{
        label: "pack-" + job,
        capability_mode: "execute",
        model: "grok-4.5",
        output_schema: fit_schema,
        phase: "Pack",
    });
    if fitted != () && fitted.success && fitted.output != () && fitted.output.best != () && fitted.output.best > best {
        best = fitted.output.best;
    }
    log("after pack " + job + " best " + best.to_string());
}

complete(#{ best: best, stop: best >= 30 });
