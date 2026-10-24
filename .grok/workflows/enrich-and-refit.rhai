let meta = #{
    name: "enrich-and-refit",
    description: "A grok-4.7 overseer runs feature enrichment, then a long second-forest search, to beat 22 of 48",
    when_to_use: "Feature columns first, then another model loop. /enrich-and-refit",
    phases: [
        #{ title: "Feature plan", detail: "one grok-4.7 overseer writes the next feature order" },
        #{ title: "Feature check", detail: "one grok-4.7 checker reads the feature plan" },
        #{ title: "Enrich", detail: "one feature fit at a time, 2024 graded against 22 of 48" },
        #{ title: "Model plan", detail: "the overseer writes the next forty forest settings" },
        #{ title: "Model check", detail: "one grok-4.7 checker reads every new forest spec" },
        #{ title: "Refit", detail: "one second forest at a time" },
    ],
};

let plan_schema = #{
    "type": "object",
    "required": ["wrote", "path", "count"],
    "properties": #{
        "wrote": #{ "type": "boolean" },
        "path": #{ "type": "string" },
        "count": #{ "type": "integer" },
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

let feature_jobs = [
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

let model_jobs = [
    #{ id: "241" },
    #{ id: "242" },
    #{ id: "243" },
    #{ id: "244" },
    #{ id: "245" },
    #{ id: "246" },
    #{ id: "247" },
    #{ id: "248" },
    #{ id: "249" },
    #{ id: "250" },
    #{ id: "251" },
    #{ id: "252" },
    #{ id: "253" },
    #{ id: "254" },
    #{ id: "255" },
    #{ id: "256" },
    #{ id: "257" },
    #{ id: "258" },
    #{ id: "259" },
    #{ id: "260" },
    #{ id: "261" },
    #{ id: "262" },
    #{ id: "263" },
    #{ id: "264" },
    #{ id: "265" },
    #{ id: "266" },
    #{ id: "267" },
    #{ id: "268" },
    #{ id: "269" },
    #{ id: "270" },
    #{ id: "271" },
    #{ id: "272" },
    #{ id: "273" },
    #{ id: "274" },
    #{ id: "275" },
    #{ id: "276" },
    #{ id: "277" },
    #{ id: "278" },
    #{ id: "279" },
    #{ id: "280" },
];

let base = "C:/Users/Jacob/Downloads/congressional app";

phase("Feature plan");
let feature_prompt = "You are the grok-4.7 overseer for feature enrichment. Workspace: " + base + ". ";
feature_prompt += "Read models/feature_island_db.json, models/feature_island_lesson.txt, models/feature_specs/01.json through models/feature_specs/12.json, and the FORMULA_NAMES tuple in scripts/feature_islands.py before you write. ";
feature_prompt += "Specs 01 and 02 already scored. Their 2023 top 1 percent count is 93 of 93. The script now also scores 2024 on every legal spec. A candidate is saved only when that 2024 top 1 percent count is higher than 22 of 48. ";
feature_prompt += "Write models/feature_specs/overseer_plan.json and nothing else. It is a JSON array of exactly 10 objects, ids 03 through 12 in order, two digits. ";
feature_prompt += "Each object has id, name, and why. name must be one of the names already in models/feature_specs/03.json through 12.json. Do not invent a formula. Do not edit those spec files. ";
feature_prompt += "why is one sentence on why that column might move a 2024 fraud row that the frozen 22 of 48 forest left out of the top 1 percent. ";
feature_prompt += "Do not edit app/, scripts/, models/specs/, models/candidates/, models/optimized_model.joblib, or models/paper_forest.joblib. ";
feature_prompt += "A high score means resemblance to later fraud-type exclusions. Do not say the firm committed fraud.";
let feature_plan = agent(feature_prompt, #{
    label: "feature-overseer",
    capability_mode: "all",
    model: "grok-4.7",
    output_schema: plan_schema,
    phase: "Feature plan",
});
if feature_plan != () && feature_plan.success && feature_plan.output != () && feature_plan.output.wrote == true {
    log("feature overseer wrote " + feature_plan.output.path);
} else {
    log("feature overseer did not write a plan; fits use the saved specs 03 through 12");
}

phase("Feature check");
let feature_check_prompt = "You are the feature-plan checker. Model grok-4.7. Workspace: " + base + ". ";
feature_check_prompt += "Read models/feature_specs/overseer_plan.json if it exists, and read models/feature_specs/03.json through 12.json. ";
feature_check_prompt += "A legal plan has exactly 10 objects, ids 03 through 12, and each name matches that spec file. ";
feature_check_prompt += "If the plan is missing or a name disagrees, rewrite only models/feature_specs/overseer_plan.json so each id copies the name from that spec file. ";
feature_check_prompt += "Do not edit scripts/, app/, models/specs/, or models/feature_specs/01.json through 12.json. ";
feature_check_prompt += "Return checked as the number of spec files you read, fixed as 1 if you rewrote the plan and 0 otherwise, and blocked as the number of illegal names before your rewrite.";
let feature_checked = agent(feature_check_prompt, #{
    label: "feature-checker",
    capability_mode: "read-write",
    model: "grok-4.7",
    output_schema: check_schema,
    phase: "Feature check",
});
if feature_checked != () && feature_checked.success && feature_checked.output != () {
    log("feature checker read " + feature_checked.output.checked.to_string());
} else {
    log("feature checker did not return; fits still use the saved specs");
}

phase("Enrich");
let feature_best = 22;
let feature_index = 0;
for job in feature_jobs {
    feature_index += 1;
    if feature_best >= 30 {
        break;
    }
    let room = budget();
    if room.remaining < 1 {
        log("feature fits stopped with no agent budget left");
        break;
    }
    let enrich_prompt = "Run this command and wait until it exits. Workspace: " + base + ". ";
    enrich_prompt += "py -3.14 scripts/feature_islands.py fit models/feature_specs/" + job.id + ".json. ";
    enrich_prompt += "The fit downloads one CMS year at a time, about 3 GB, builds data/feature_columns, refits the frozen 60-tree forest, and scores 2024. Wait for the process to exit. Do not start a second fit. Do not edit the script. ";
    enrich_prompt += "Do not edit app/, models/specs/, models/candidates/, models/optimized_model.joblib, or models/paper_forest.joblib. ";
    enrich_prompt += "When it exits, read models/feature_island_db.json. Return best as the integer best_confirm_top1 if that key exists, otherwise 22. Put the last printed confirm_top1 line in note. If the command fails, set best to 0.";
    let enriched = agent(enrich_prompt, #{
        label: "enrich-" + job.id,
        capability_mode: "execute",
        model: "grok-4.5",
        output_schema: fit_schema,
        phase: "Enrich",
    });
    if enriched != () && enriched.success && enriched.output != () && enriched.output.best != () {
        if enriched.output.best > feature_best {
            feature_best = enriched.output.best;
        }
    }
    log("after feature " + job.id + " best " + feature_best.to_string() + "/48");
}

phase("Model plan");
let model_prompt = "You are the grok-4.7 overseer for the long second-forest search. Workspace: " + base + ". ";
model_prompt += "Read models/model_island_db.json, models/model_island_note.txt, models/specs/22.json, and scripts/model_islands.py before you write. ";
model_prompt += "The best full-year count so far is 22 of 48, from models/candidates/22.joblib. Specs 01 through 236 are already scored. None beat 22 of 48. Do not repeat a spec already listed in models/model_island_db.json. ";
model_prompt += "Also read models/feature_island_db.json. If a feature candidate saved a higher best_confirm_top1, say that number in why, and still write forest settings only. This loop does not add a column. ";
model_prompt += "Write models/specs/overseer_plan.json and nothing else. It must be a JSON array of exactly 40 objects, ids 241 through 280 in order. ";
model_prompt += "Each object has id, n_estimators, max_depth, min_samples_leaf, class_weight, clean_per_fraud, fit_years, and why. ";
model_prompt += "Bounds: n_estimators 20 to 200, max_depth 4 to 24 or null, min_samples_leaf 1 to 200, class_weight balanced or balanced_subsample or none, clean_per_fraud 1 to 30. ";
model_prompt += "fit_years must stay inside 2013 through 2022. Never include 2023 or 2024. ";
model_prompt += "Leave the depth-20 leaf-1 neighborhood that already tied at 22. Spread year sets, mix ratios, and tree counts. ";
model_prompt += "Do not edit app/, scripts/, models/feature_specs/, models/optimized_model.joblib, or models/candidates/. ";
model_prompt += "A high score means resemblance to later fraud-type exclusions. Do not say the firm committed fraud.";
let model_plan = agent(model_prompt, #{
    label: "model-overseer",
    capability_mode: "all",
    model: "grok-4.7",
    output_schema: plan_schema,
    phase: "Model plan",
});
if model_plan != () && model_plan.success && model_plan.output != () && model_plan.output.wrote == true {
    log("model overseer wrote " + model_plan.output.path);
} else {
    log("model overseer did not write a plan; writers copy the saved 22 of 48 parent");
}

phase("Model check");
let model_check_prompt = "You are the spec checker. Model grok-4.7. Workspace: " + base + ". ";
model_check_prompt += "Read models/specs/overseer_plan.json. For each object whose id is 241 through 280, write models/specs/ID.json with only n_estimators, max_depth, min_samples_leaf, class_weight, clean_per_fraud, and fit_years. ";
model_check_prompt += "Read scripts/model_islands.py load_spec so the bounds match the fitter. ";
model_check_prompt += "A legal spec has n_estimators 20 to 200, max_depth 4 to 24 or null, min_samples_leaf 1 to 200, class_weight balanced or balanced_subsample or none, clean_per_fraud 1 to 30, and fit_years inside 2013 through 2022. ";
model_check_prompt += "Reject a year of 2023 or 2024 by rewriting that file. If a plan object is missing or illegal, write a legal file copied from models/specs/22.json with min_samples_leaf set to 2. ";
model_check_prompt += "Do not edit scripts/, app/, models/feature_specs/, models/optimized_model.joblib, or models/candidates/. ";
model_check_prompt += "Return checked as the number of spec files you wrote or read, fixed as the number you rewrote, and blocked as the number that were illegal before your rewrite.";
let model_checked = agent(model_check_prompt, #{
    label: "model-checker",
    capability_mode: "read-write",
    model: "grok-4.7",
    output_schema: check_schema,
    phase: "Model check",
});
if model_checked != () && model_checked.success && model_checked.output != () {
    log("model checker wrote " + model_checked.output.checked.to_string());
} else {
    log("model checker did not return; fits still use whatever specs exist");
}

phase("Refit");
let model_best = 22;
if feature_best > model_best {
    model_best = feature_best;
}
for job in model_jobs {
    if model_best >= 30 {
        break;
    }
    let room = budget();
    if room.remaining < 1 {
        log("model fits stopped with no agent budget left");
        break;
    }
    let fit_prompt = "Run this command and wait until it exits. Workspace: " + base + ". ";
    fit_prompt += "py -3.14 scripts/model_islands.py fit models/specs/" + job.id + ".json. ";
    fit_prompt += "Wait for the process to exit. Do not edit the script. Do not start a second fit. ";
    fit_prompt += "Do not edit app/, models/feature_specs/, models/feature_candidates/, or models/optimized_model.joblib. ";
    fit_prompt += "When it exits, read models/model_island_db.json. Return best as the integer best_confirm_top1. Put the last printed line in note. If the command fails, set best to 0.";
    let fitted = agent(fit_prompt, #{
        label: "fit-" + job.id,
        capability_mode: "execute",
        model: "grok-4.5",
        output_schema: fit_schema,
        phase: "Refit",
    });
    if fitted != () && fitted.success && fitted.output != () && fitted.output.best != () {
        if fitted.output.best > model_best {
            model_best = fitted.output.best;
        }
    }
    log("after spec " + job.id + " best " + model_best.to_string() + "/48");
}

complete(#{
    feature_best: feature_best,
    best: model_best,
    stop: model_best >= 30,
});
