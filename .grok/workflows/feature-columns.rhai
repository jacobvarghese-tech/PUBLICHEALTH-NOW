let meta = #{
    name: "feature-columns",
    description: "Finish the twelve feature columns and score each one on the full 2024 year",
    when_to_use: "Finish the unused line-level columns. /feature-columns",
    phases: [
        #{ title: "Release", detail: "clear the 2016 size stop after the live file check" },
        #{ title: "Check", detail: "one checker reads the twelve saved specs" },
        #{ title: "Fit", detail: "one feature column at a time, 2024 scored against 23 of 48" },
    ],
};

let check_schema = #{
    "type": "object",
    "required": ["checked", "fixed", "blocked"],
    "properties": #{
        "checked": #{ "type": "integer" },
        "fixed": #{ "type": "integer" },
        "blocked": #{ "type": "integer" },
    },
};

let fit_schema = #{
    "type": "object",
    "required": ["best", "note"],
    "properties": #{
        "best": #{ "type": "integer" },
        "note": #{ "type": "string" },
    },
};

let jobs = [
    #{ id: "01" },
    #{ id: "02" },
    #{ id: "03" },
    #{ id: "04" },
    #{ id: "05" },
    #{ id: "06" },
    #{ id: "07" },
    #{ id: "08" },
    #{ id: "09" },
    #{ id: "10" },
    #{ id: "11" },
    #{ id: "12" },
];

let base = "C:/Users/Jacob/Downloads/congressional app";

phase("Release");
let release_prompt = "Run one command and wait until it exits. Workspace: " + base + ". ";
release_prompt += "py -3.14 scripts/feature_islands.py release-stop. ";
release_prompt += "That command clears the recorded 2016 size stop in models/feature_island_db.json. ";
release_prompt += "The live 2016 file still reports Content-Range bytes 0-0/3051491999, which matches data/paper_rolled/2016.resources.txt. The earlier download of 3077063327 bytes was longer than that file. ";
release_prompt += "Do not edit opened_bytes. Do not invent a URL. Do not download a CMS year. Do not edit app/, scripts/, or models/paper_forest.joblib. ";
release_prompt += "When it exits, read models/feature_island_db.json. Return checked as 1, fixed as 1 if the latest stop has cleared true, and blocked as 0. If the command fails, set blocked to 1 and fixed to 0.";
let released = agent(release_prompt, #{
    label: "release-stop",
    capability_mode: "execute",
    model: "grok-4.5",
    output_schema: check_schema,
    phase: "Release",
});
if released != () && released.success && released.output != () && released.output.fixed == 1 {
    log("2016 size stop cleared");
} else {
    log("release did not confirm a clear; fits still run and will exit if the stop remains");
}

phase("Check");
let check_prompt = "You are the feature-spec checker. Workspace: " + base + ". ";
check_prompt += "Read models/feature_specs/01.json through models/feature_specs/12.json with the read_file tool. ";
check_prompt += "Read the FORMULA_NAMES tuple in scripts/feature_islands.py. ";
check_prompt += "A legal spec has name, source_columns, formula, join_keys, and grain. ";
check_prompt += "name, or every name in names, must be one of the FORMULA_NAMES. ";
check_prompt += "join_keys must be provider_type, npi, and nppes_provider_gender. grain must be provider-year. ";
check_prompt += "formula must not start with the word rejected. ";
check_prompt += "Do not rewrite a legal spec. If a spec is missing a required key, add only that key from the matching formula already in scripts/feature_islands.py. ";
check_prompt += "Do not edit scripts/, app/, models/paper_forest.joblib, models/candidates/, or models/optimized_model.joblib. ";
check_prompt += "Return checked as the number of spec files you read, fixed as the number you rewrote, and blocked as the number that were illegal before your rewrite.";
let checked = agent(check_prompt, #{
    label: "spec-checker",
    capability_mode: "read-write",
    model: "grok-4.7",
    output_schema: check_schema,
    phase: "Check",
});
if checked != () && checked.success && checked.output != () {
    log("checker read " + checked.output.checked.to_string() + " and rewrote " + checked.output.fixed.to_string());
} else {
    log("checker did not return; fits still use the saved specs");
}

phase("Fit");
let best = 23;
let index = 0;
for job in jobs {
    index += 1;
    if best >= 30 {
        break;
    }
    let room = budget();
    if room.remaining < 1 {
        log("feature fits stopped with no agent budget left");
        break;
    }
    let fit_prompt = "Run this command and wait until it exits. Workspace: " + base + ". ";
    fit_prompt += "py -3.14 scripts/feature_islands.py fit models/feature_specs/" + job.id + ".json. ";
    fit_prompt += "The fit downloads one CMS year at a time, about 3 GB, builds data/feature_columns, refits the frozen 60-tree forest from models/specs/22.json, and scores the full 2024 year. ";
    fit_prompt += "Wait for the process to exit. A year can take a long time. Do not start a second fit. Do not kill the process because it looks quiet. ";
    fit_prompt += "Do not edit the script. Do not edit app/, models/specs/, models/paper_forest.joblib, or models/optimized_model.joblib. ";
    fit_prompt += "A candidate file is written only when the 2024 top 1 percent count is higher than 23 of 48. ";
    fit_prompt += "When it exits, read models/feature_island_db.json. Return best as the integer best_confirm_top1 if that key exists, otherwise 23. ";
    fit_prompt += "Put the last printed confirm_top1 line in note. If the command fails, set best to 0 and put the error in note. ";
    fit_prompt += "A high score means resemblance to later fraud-type exclusions. Do not say the firm committed fraud.";
    let fitted = agent(fit_prompt, #{
        label: "fit-" + job.id,
        capability_mode: "execute",
        model: "grok-4.5",
        output_schema: fit_schema,
        phase: "Fit",
    });
    if fitted != () && fitted.success && fitted.output != () && fitted.output.best != () {
        if fitted.output.best > best {
            best = fitted.output.best;
        }
    }
    log("after feature " + job.id + " best " + best.to_string() + "/48");
}

complete(#{
    best: best,
    stop: best >= 30,
    scored: index,
});
