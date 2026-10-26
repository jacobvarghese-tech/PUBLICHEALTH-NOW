let meta = #{
    name: "usability-islands",
    description: "Refit the second forest around the 23/48 pattern until the 2024 top 1 percent count reaches 26 of 48",
    when_to_use: "Keep the no-weight leaf-1 clean-ratio-10 pattern and raise the 2024 top 1 percent count. /usability-islands",
    phases: [
        #{ title: "Oversee", detail: "one grok-4.7 overseer writes the next twenty settings" },
        #{ title: "Specify", detail: "twenty fit specs" },
        #{ title: "Check", detail: "one grok-4.7 checker reads every new spec before a fit" },
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
    #{ id: "301" },
    #{ id: "302" },
    #{ id: "303" },
    #{ id: "304" },
    #{ id: "305" },
    #{ id: "306" },
    #{ id: "307" },
    #{ id: "308" },
    #{ id: "309" },
    #{ id: "310" },
    #{ id: "311" },
    #{ id: "312" },
    #{ id: "313" },
    #{ id: "314" },
    #{ id: "315" },
    #{ id: "316" },
    #{ id: "317" },
    #{ id: "318" },
    #{ id: "319" },
    #{ id: "320" },
];

let base = "C:/Users/Jacob/Downloads/congressional app";

phase("Oversee");
let overseer_prompt = "You are the overseer for the second-forest usability search. Workspace: " + base + ". ";
overseer_prompt += "Use grok-4.7 judgment. Read models/model_island_db.json, models/model_island_note.txt, models/specs/247.json, and scripts/model_islands.py before you write. ";
overseer_prompt += "The saved best is 23 of 48, from models/specs/247.json: n_estimators 50, max_depth null, min_samples_leaf 1, class_weight none, clean_per_fraud 10, fit_years 2016 through 2022. ";
overseer_prompt += "Ten fits held 23 of 48. They share class_weight none, min_samples_leaf 1, and clean_per_fraud 10. Tree counts that held were 20, 30, 50, 90, and 100. Unlimited depth held. Depth 21 also held on two specs. ";
overseer_prompt += "Year lists that held were 2016-2022, 2018-2022, 2016-2017 plus 2019-2022, and 2019-2022. ";
overseer_prompt += "Moving clean_per_fraud off 10, raising the leaf above 1, or using class_weight balanced dropped the count. Do not leave that pattern. ";
overseer_prompt += "Specs 61 through 300 already scored. Do not repeat those ids. Do not rewrite any file except models/specs/overseer_plan.json. ";
overseer_prompt += "Write models/specs/overseer_plan.json and nothing else. It must be a JSON array of exactly 20 objects, ids 301 through 320 in order. ";
overseer_prompt += "Each object has id, n_estimators, max_depth, min_samples_leaf, class_weight, clean_per_fraud, fit_years, and why. ";
overseer_prompt += "Every object must set class_weight to none, min_samples_leaf to 1, and clean_per_fraud to 10. ";
overseer_prompt += "Vary n_estimators across 20, 30, 40, 50, 60, and 70. Set max_depth to null on at least 14 objects. The other objects may use 16, 18, or 21. ";
overseer_prompt += "fit_years must stay inside 2013 through 2022 and must include 2020, 2021, and 2022. Never include 2023 or 2024. ";
overseer_prompt += "Do not copy 247.json exactly. Do not edit app/, scripts/, models/optimized_model.joblib, or models/candidates/. ";
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
    log("overseer did not write a plan; writers use the 23/48 parent");
}

phase("Specify");
let writers = [];
for job in jobs_spec {
    let prompt = "Write one JSON file and nothing else. Workspace: " + base + ". "
        + "Read models/specs/overseer_plan.json with the read_file tool. "
        + "Find the object whose id is " + job.id + ". "
        + "Write models/specs/" + job.id + ".json with only n_estimators, max_depth, min_samples_leaf, class_weight, clean_per_fraud, and fit_years from that object. "
        + "If the plan is missing, copy models/specs/247.json and change only n_estimators to 40. "
        + "Force class_weight to none, min_samples_leaf to 1, and clean_per_fraud to 10. "
        + "n_estimators is 20 to 200. max_depth is 4 to 24, or null. "
        + "fit_years stays inside 2013 through 2022 and includes 2020, 2021, and 2022. Never include 2023 or 2024. "
        + "Do not edit any other spec. Do not edit app/, scripts/, or models/optimized_model.joblib.";
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
check_prompt += "Read every models/specs/301.json through models/specs/320.json with the read_file tool before you answer. ";
check_prompt += "Also read scripts/model_islands.py load_spec so the bounds match the fitter. ";
check_prompt += "A legal spec has n_estimators 20 to 200, max_depth 4 to 24 or null, min_samples_leaf 1, class_weight none, clean_per_fraud 10, and fit_years inside 2013 through 2022 including 2020, 2021, and 2022. ";
check_prompt += "If one of those twenty files is missing or illegal, rewrite only that file so it matches the pattern. ";
check_prompt += "Do not rewrite models/specs/247.json or any spec numbered 300 or below. ";
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
let best = 23;
let index = 0;
for job in jobs_spec {
    index += 1;
    if best >= 26 {
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
        + "Do not edit any spec file. Do not start a second fit. When it exits, read models/model_island_db.json. "
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
    stop: best >= 26,
});
