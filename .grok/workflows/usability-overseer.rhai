let meta = #{
    name: "usability-overseer",
    description: "A standing grok-4.7 overseer reviews scored second-forest fits and writes the next 23/48-pattern batch",
    when_to_use: "After a usability-islands batch, have the overseer write the next twenty specs. /usability-overseer",
    phases: [
        #{ title: "Review", detail: "one grok-4.7 overseer reads the scores" },
        #{ title: "Plan", detail: "the same overseer writes the next twenty settings" },
    ],
};

let review_schema = #{
    "type": "object",
    "required": ["best", "held", "dropped", "next_start"],
    "properties": #{
        "best": #{ "type": "integer" },
        "held": #{ "type": "integer" },
        "dropped": #{ "type": "integer" },
        "next_start": #{ "type": "integer" },
    },
};

let plan_schema = #{
    "type": "object",
    "required": ["wrote", "path", "count", "first_id", "last_id"],
    "properties": #{
        "wrote": #{ "type": "boolean" },
        "path": #{ "type": "string" },
        "count": #{ "type": "integer" },
        "first_id": #{ "type": "integer" },
        "last_id": #{ "type": "integer" },
    },
};

let base = "C:/Users/Jacob/Downloads/congressional app";

phase("Review");
let review_prompt = "You are the standing overseer for the second-forest usability search. Workspace: " + base + ". ";
review_prompt += "Use grok-4.7 judgment. Read models/model_island_note.txt and models/model_island_db.json with the read_file tool before you answer. ";
review_prompt += "Read models/specs/247.json. The pattern that held 23 of 48 is class_weight none, min_samples_leaf 1, clean_per_fraud 10, and fit years inside 2016 through 2022 that include 2020, 2021, and 2022. ";
review_prompt += "Count how many recorded specs have confirm_top1 of 23 or higher. Count how many of specs 301 and above scored below 23. ";
review_prompt += "Set best to the integer best_confirm_top1. Set held to the count at or above 23. Set dropped to the count of specs 301 and above that scored below 23. ";
review_prompt += "Set next_start to 321 if no spec numbered 301 or higher exists in the database. Otherwise set next_start to one past the highest spec number already recorded. ";
review_prompt += "Do not edit any file. Do not start a fit. ";
review_prompt += "A high score means resemblance to later fraud-type exclusions. Do not say the firm committed fraud.";
let review = agent(review_prompt, #{
    label: "overseer-review",
    capability_mode: "read-only",
    model: "grok-4.7",
    output_schema: review_schema,
    phase: "Review",
});
if review == () || !review.success || review.output == () {
    log("overseer review did not return");
    complete(#{ wrote: false, best: 23 });
}
log("overseer best " + review.output.best.to_string() + " held " + review.output.held.to_string() + " next " + review.output.next_start.to_string());

phase("Plan");
let plan_prompt = "You are the standing overseer. Workspace: " + base + ". ";
plan_prompt += "Your review found best " + review.output.best.to_string() + " of 48, held " + review.output.held.to_string() + ", dropped " + review.output.dropped.to_string() + ", next_start " + review.output.next_start.to_string() + ". ";
plan_prompt += "Read models/model_island_note.txt, models/specs/247.json, and the newest 20 entries of models/model_island_db.json before you write. ";
plan_prompt += "Write models/specs/overseer_plan.json and nothing else. It must be a JSON array of exactly 20 objects. ";
plan_prompt += "Ids start at " + review.output.next_start.to_string() + " and increase by 1. Do not reuse an id already listed in models/model_island_db.json. ";
plan_prompt += "Each object has id, n_estimators, max_depth, min_samples_leaf, class_weight, clean_per_fraud, fit_years, and why. ";
plan_prompt += "Every object must set class_weight to none, min_samples_leaf to 1, and clean_per_fraud to 10. ";
plan_prompt += "Keep max_depth null on at least 14 objects. The other objects may use 16, 18, or 21. ";
plan_prompt += "If the review best is still 23, vary n_estimators across 20, 30, 40, 50, 60, and 70, and vary year lists that still include 2020, 2021, and 2022. ";
plan_prompt += "If the review best is 24 or higher, read the winning spec and vary only one knob away from it. Keep the other knobs fixed. ";
plan_prompt += "fit_years must stay inside 2013 through 2022. Never include 2023 or 2024. ";
plan_prompt += "Do not edit app/, scripts/, models/optimized_model.joblib, models/candidates/, or any models/specs file other than overseer_plan.json. ";
plan_prompt += "The working stop is 6:00 a.m. local on 2026-10-24 in models/work_clock.json. An empty forest-spec list before that clock is a stall. Write the next twenty specs so the director can start the next fit. ";
plan_prompt += "Do not start a fit. The director starts the fit. A high score means resemblance to later fraud-type exclusions. Do not say the firm committed fraud.";
let planned = agent(plan_prompt, #{
    label: "overseer-plan",
    capability_mode: "read-write",
    model: "grok-4.7",
    output_schema: plan_schema,
    phase: "Plan",
    resume_from: review.agent_id,
});
if planned != () && planned.success && planned.output != () && planned.output.wrote == true {
    log("overseer wrote " + planned.output.path + " ids " + planned.output.first_id.to_string() + " through " + planned.output.last_id.to_string());
    complete(#{
        wrote: true,
        path: planned.output.path,
        first_id: planned.output.first_id,
        last_id: planned.output.last_id,
        best: review.output.best,
    });
}
log("overseer did not write a plan");
complete(#{ wrote: false, best: review.output.best });
