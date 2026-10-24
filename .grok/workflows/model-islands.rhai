let meta = #{
    name: "model-islands",
    description: "Twenty agents refit the second forest until the 2024 top 1 percent count reaches 30 of 48",
    when_to_use: "Refit the 20/48 second forest. The harness loop stays separate. /model-islands",
    phases: [
        #{ title: "Oversee", detail: "one grok-4.7 overseer writes the next twenty settings" },
        #{ title: "Specify", detail: "twenty fit specs" },
        #{ title: "Check", detail: "one grok-4.7 checker reads every spec before a fit" },
        #{ title: "Fit", detail: "one second forest at a time" },
    ],
};

let overseer_schema = #{
    "type": "object",
    "required": ["wrote", "path", "count"],
    "properties": #{
        "wrote": #{ "type": "boolean" },
        "path": #{ "type": "string" },
        "count": #{ "type": "integer" },
    },
};

let spec_schema = #{
    "type": "object",
    "required": ["wrote", "path"],
    "properties": #{
        "wrote": #{ "type": "boolean" },
        "path": #{ "type": "string" },
    },
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

let jobs_spec = [
    #{ id: "281" },
    #{ id: "282" },
    #{ id: "283" },
    #{ id: "284" },
    #{ id: "285" },
    #{ id: "286" },
    #{ id: "287" },
    #{ id: "288" },
    #{ id: "289" },
    #{ id: "290" },
    #{ id: "291" },
    #{ id: "292" },
    #{ id: "293" },
    #{ id: "294" },
    #{ id: "295" },
    #{ id: "296" },
    #{ id: "297" },
    #{ id: "298" },
    #{ id: "299" },
    #{ id: "300" },
];

let base = "C:/Users/Jacob/Downloads/congressional app";

phase("Oversee");
let overseer_prompt = "You are the overseer for the second-forest search. Workspace: " + base + ". ";
overseer_prompt += "Use grok-4.7 judgment. Read models/model_island_db.json, models/model_island_note.txt, models/specs/22.json, and scripts/model_islands.py before you write. ";
overseer_prompt += "The best full-year count so far is 22 of 48, from models/candidates/22.joblib. Three rounds of one-knob edits around that fit tied 22 and did not pass it. ";
overseer_prompt += "Specs 61 through 280 already scored and none beat 22/48. Do not repeat specs 61 through 280. Do not rewrite those ids. ";
overseer_prompt += "Write models/specs/overseer_plan.json and nothing else. It must be a JSON array of exactly 20 objects, ids 281 through 300 in order. ";
overseer_prompt += "Each object has id, n_estimators, max_depth, min_samples_leaf, class_weight, clean_per_fraud, fit_years, and why. ";
overseer_prompt += "Bounds: n_estimators 20 to 200, max_depth 4 to 24 or null, min_samples_leaf 1 to 200, class_weight balanced or balanced_subsample or none, clean_per_fraud 1 to 30. ";
overseer_prompt += "fit_years must stay inside 2013 through 2022. Never include 2023 or 2024. ";
overseer_prompt += "Do not repeat a spec already listed in models/model_island_db.json. Leave the depth-20 leaf-1 balanced neighborhood that already tied at 22. ";
overseer_prompt += "Spec 274.json tied 22 with class_weight none, n_estimators 100, max_depth null, min_samples_leaf 1, clean_per_fraud 10, and fit_years 2016 through 2022. Specs 261 through 280 otherwise scored 19 to 21. ";
overseer_prompt += "Keep class_weight none and min_samples_leaf 1. Keep fit_years as 2016, 2017, 2018, 2019, 2020, 2021, and 2022. ";
overseer_prompt += "Vary only n_estimators across 80, 90, 100, 110, and 120, max_depth across null and 24, and clean_per_fraud across 8, 9, 10, and 11. Do not copy 274.json exactly. ";
overseer_prompt += "Do not edit app/, scripts/, models/optimized_model.joblib, or models/candidates/. ";
overseer_prompt += "A high score means resemblance to later fraud-type exclusions. Do not say the firm committed fraud.";
let overseer = agent(overseer_prompt, #{
    label: "overseer",
    capability_mode: "all",
    model: "grok-4.7",
    output_schema: overseer_schema,
    phase: "Oversee",
});
if overseer != () && overseer.success && overseer.output != () && overseer.output.wrote == true {
    log("overseer wrote " + overseer.output.path);
} else {
    log("overseer did not write a plan; writers use the saved 22/48 parent");
}

phase("Specify");
let writers = [];
for job in jobs_spec {
    let prompt = "Write one JSON file and nothing else. Workspace: " + base + ". "
        + "Read models/specs/overseer_plan.json with the read_file tool. "
        + "Find the object whose id is " + job.id + ". "
        + "Write models/specs/" + job.id + ".json with only n_estimators, max_depth, min_samples_leaf, class_weight, clean_per_fraud, and fit_years from that object. "
        + "If the plan is missing, copy models/specs/22.json and change only min_samples_leaf to 1. "
        + "n_estimators is 20 to 200. max_depth is 4 to 24, or null. min_samples_leaf is 1 to 200. "
        + "class_weight is balanced, balanced_subsample, or none. clean_per_fraud is 1 to 30. "
        + "fit_years stays inside 2013 through 2022. Never include 2023 or 2024. "
        + "Do not edit app/, scripts/, or models/optimized_model.joblib.";
    writers.push(#{
        prompt: prompt,
        label: "spec-" + job.id,
        capability_mode: "read-write",
        model: "grok-4.5",
        output_schema: spec_schema,
        phase: "Specify",
    });
}
let written = parallel(writers);
let count = 0;
for item in written {
    if item != () && item.success && item.output != () && item.output.wrote == true {
        count += 1;
    }
}
log(count.to_string() + " of 20 specs written");

phase("Check");
let check_prompt = "You are the spec checker. Model grok-4.7. Workspace: " + base + ". ";
check_prompt += "Read every models/specs/281.json through models/specs/300.json with the read_file tool before you answer. ";
check_prompt += "Also read scripts/model_islands.py load_spec so the bounds match the fitter. ";
check_prompt += "A legal spec has n_estimators 20 to 200, max_depth 4 to 24 or null, min_samples_leaf 1 to 200, class_weight balanced or balanced_subsample or none, clean_per_fraud 1 to 30, and fit_years inside 2013 through 2022. ";
check_prompt += "Reject a year of 2023 or 2024 by rewriting that file. If a file is missing or illegal, rewrite only that JSON file so it matches the bounds. ";
check_prompt += "Do not edit scripts/, app/, models/optimized_model.joblib, or models/candidates/. ";
check_prompt += "Return checked as the number of files you read, fixed as the number you rewrote, and blocked as the number that were illegal before your rewrite.";
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
    log("checker did not return; fits still use the written specs");
}

phase("Fit");
let best = 22;
let index = 0;
for job in jobs_spec {
    index += 1;
    if best >= 30 {
        break;
    }
    let room = budget();
    if room.remaining < 1 {
        log("fit stopped with no agent budget left");
        break;
    }
    let fit_prompt = "Run this command and wait until it exits. Workspace: " + base + ". "
        + "py -3.14 scripts/model_islands.py fit models/specs/" + job.id + ".json. "
        + "Do not edit the script. Do not edit app/. Do not replace models/optimized_model.joblib. "
        + "Do not start a second fit. When it exits, read models/model_island_db.json. "
        + "Return best as the integer best_confirm_top1. Put the last printed line in note. "
        + "If the command fails, set best to 0.";
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
    log("after spec " + job.id + " best " + best.to_string() + "/48");
}

complete(#{
    best: best,
    stop: best >= 30,
});
