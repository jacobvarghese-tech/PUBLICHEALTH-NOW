let meta = #{
    name: "score-islands",
    description: "Twenty agents rewrite island scorers until the 2024 top 1 percent count reaches 30 of 48",
    when_to_use: "Keep the island search running toward 30/48. /score-islands",
    phases: [
        #{ title: "Oversee", detail: "one grok-4.7 overseer writes the lesson before the writers" },
        #{ title: "Propose", detail: "fifteen island writers" },
        #{ title: "Review", detail: "five critics" },
        #{ title: "Score", detail: "local generation score" },
    ],
};

fn trimmed(s) {
    if type_of(s) == "string" {
        s.trim();
        s
    } else {
        ""
    }
}

let file_schema = #{
    "type": "object",
    "required": ["wrote", "path"],
    "properties": #{
        "wrote": #{ "type": "boolean" },
        "path": #{ "type": "string" },
        "note": #{ "type": "string" },
    },
};

let overseer_schema = #{
    "type": "object",
    "required": ["wrote", "path"],
    "properties": #{
        "wrote": #{ "type": "boolean" },
        "path": #{ "type": "string" },
    },
};

let review_schema = #{
    "type": "object",
    "required": ["island", "verdict", "reason"],
    "properties": #{
        "island": #{ "type": "string" },
        "verdict": #{ "type": "string" },
        "reason": #{ "type": "string" },
    },
};

let lesson_schema = #{
    "type": "object",
    "required": ["wrote", "stalls"],
    "properties": #{
        "wrote": #{ "type": "boolean" },
        "stalls": #{ "type": "integer" },
        "best": #{ "type": "integer" },
        "note": #{ "type": "string" },
    },
};

let roles = [
    "Zero-tie. Start from harness/islands/01/score_rows.py. Change only the way a paper_score of 0 is raised, using secondary_score, zero_cutoff, and vote_step already on the row.",
    "Blend. On a paper_score of 0, combine secondary_score and tree_score into one promotion. Leave a positive paper_score unchanged.",
    "Within-zero rank. On a paper_score of 0, order rows by secondary_score. Promote only a thin top of that group.",
    "Specialty. On a paper_score of 0, compare secondary_score with other rows of the same Specialty. Promote only a high within-specialty rank.",
    "Services per beneficiary. On a paper_score of 0, use Service count and Beneficiary count to order the zero group.",
    "Charge-to-payment. On a paper_score of 0, rank Charge-to-payment ratio within Specialty.",
    "Top-code share. On a paper_score of 0, rank Top-code share within Specialty.",
    "Missing growth. Use a separate zero-group rule when Growth is missing.",
    "Log services. On a paper_score of 0, use the log of Service count as the tie break.",
    "Beneficiary rank. On a paper_score of 0, rank Beneficiary count.",
    "Charge minus payment. On a paper_score of 0, use Average charge minus Average payment.",
    "Growth times top-code. On a paper_score of 0, promote a high Top-code share together with a high Growth.",
    "Tree tie. On a paper_score of 0, use tree_score as the only tie break.",
    "Miss note. Read harness/islands/lesson.txt if it exists. Propose one threshold on a billing field that the missed 2023 rows share. No identifier.",
    "Merge. Read two island files that the lesson names, or islands 01 and 02 if the lesson names none. Combine them into one score_rows.",
];

let base = "C:/Users/Jacob/Downloads/congressional app";
let generation = 0;
let best = 22;
let stalls = 0;

phase("Oversee");
while best < 30 && generation < 8 {
    let room = budget();
    if room.remaining < 21 {
        log("stopping this run with budget remaining " + room.remaining.to_string());
        break;
    }
    generation += 1;
    log("generation " + generation.to_string() + " best " + best.to_string() + "/48");
    let overseer_prompt = "You are the grok-4.7 overseer for harness generation " + generation.to_string() + ". Workspace: " + base + ". ";
    overseer_prompt += "Read models/island_note.txt, models/island_db.json, and harness/islands/01/seed_score_rows.py before you write. ";
    overseer_prompt += "The saved seed scores 22 of 48 on the full 2024 year. Earlier generations tied because every promoted zero got the same 0.01 step. ";
    overseer_prompt += "Write harness/islands/lesson.txt and nothing else. Tell each island to leave a positive paper_score unchanged, promote a paper_score of 0 only, and give each promoted zero its own rank from secondary_score. ";
    overseer_prompt += "Name one billing field each island 02 through 14 should use. Do not import, open a file, or read NPI, name, city, state, ZIP, or year. ";
    overseer_prompt += "Do not edit app/, scripts/, or models/*.joblib. A high score means resemblance to later fraud-type exclusions. Do not say the firm committed fraud.";
    let overseer = agent(overseer_prompt, #{
        label: "harness-overseer-" + generation.to_string(),
        capability_mode: "all",
        model: "grok-4.7",
        output_schema: overseer_schema,
        phase: "Oversee",
    });
    if overseer != () && overseer.success && overseer.output != () && overseer.output.wrote == true {
        log("overseer wrote " + overseer.output.path);
    } else {
        log("overseer did not write a lesson; writers use the seed");
    }
    phase("Propose");
    let jobs = [];
    let n = 0;
    for role in roles {
        n += 1;
        let folder = if n < 10 { "0" + n.to_string() } else { n.to_string() };
        let prompt = "You are island " + folder + " in generation " + generation.to_string()
            + " of a ranking search. Workspace: " + base + ". "
            + "Read harness/islands/" + folder + "/kept_score_rows.py if it exists, otherwise read harness/islands/01/seed_score_rows.py. "
            + "Also read harness/islands/lesson.txt and models/island_note.txt if they exist. "
            + "Read models/island_note.txt. Use the read_file tool before you write. "
            + "Your only write is harness/islands/" + folder + "/score_rows.py. "
            + "Define exactly one function score_rows(rows) that returns one finite float per row, same order. "
            + "Each row has the eight billing fields plus paper_score, secondary_score, tree_score, zero_cutoff, and vote_step. "
            + "A paper_score above 0 must stay unchanged. Promote a paper_score of 0 only. "
            + "A promoted zero must get its own rank from secondary_score, not one shared 0.01 step. "
            + "The saved seed is 22 of 48. A flat vote_step cannot enter the top 1 percent one row at a time. "
            + "Do not import a module. Do not open a file. Do not read NPI, name, city, state, ZIP, or year. "
            + "Do not edit app/, scripts/, models/*.joblib, or data/. "
            + "A high score means resemblance to later fraud-type exclusions. Do not say the firm committed fraud. "
            + "Role: " + role;
        let model_id = "grok-4.5";
        if n == 15 { model_id = "grok-4.7"; }
        jobs.push(#{
            prompt: prompt,
            label: "island-" + folder,
            capability_mode: "read-write",
            model: model_id,
            output_schema: file_schema,
            phase: "Propose",
        });
    }
    let proposed = parallel(jobs);
    let wrote = 0;
    for item in proposed {
        if item != () && item.success && item.output != () && item.output.wrote == true {
            wrote += 1;
        }
    }
    log(wrote.to_string() + " of 15 islands wrote a file");

    phase("Review");
    let reviews = [];
    let critic_names = ["contract", "leakage", "short-list", "diversity", "lesson"];
    let c = 0;
    for critic_name in critic_names {
        c += 1;
        let critic_id = (15 + c).to_string();
        let review_prompt = "You are critic " + critic_id + " (" + critic_name + "). Workspace: " + base + ". "
            + "Read every harness/islands/NN/score_rows.py from 01 through 15 with the read_file tool. "
            + "Island 01 is the seed and is not rejected. "
            + "For each island 02 through 15, write harness/islands/reviews/" + critic_id + "-NN.json "
            + "as {\"island\":\"NN\",\"verdict\":\"pass\" or \"reject\",\"reason\":\"one sentence\"}. "
            + "Contract: reject an import, a file open, or a read of NPI, name, city, state, ZIP, or year. "
            + "Leakage: reject a fit, a 2024 row, or demo NPIs 1124725817 and 1639879034. "
            + "Short-list: reject a function that lifts every row or ties every score. "
            + "Diversity: name one island that is not the leader and still uses a different field. "
            + "Lesson: write harness/islands/lesson.txt from the files you read and from models/island_db.json if it exists. "
            + "Do not edit scripts/ or app/. Do not say the firm committed fraud.";
        let critic_model = "grok-4.7";
        if c == 4 { critic_model = "grok-4.5"; }
        reviews.push(#{
            prompt: review_prompt,
            label: "critic-" + critic_id,
            capability_mode: "read-write",
            model: critic_model,
            output_schema: review_schema,
            phase: "Review",
        });
    }
    let reviewed = parallel(reviews);
    let passed = 0;
    for item in reviewed {
        if item != () && item.success {
            passed += 1;
        }
    }
    log(passed.to_string() + " of 5 critics returned");

    phase("Score");
    let score_prompt = "Run this command in the workspace and wait until it exits: "
        + "py -3.14 scripts/island_score.py generation. "
        + "The workspace is " + base + ". "
        + "Do not edit the script. Do not fit a model. Do not edit app/. "
        + "When it exits, read models/island_note.txt and models/island_db.json. "
        + "Return best as the integer before /48 in best_confirm_top1, and stalls from the database. "
        + "If the command fails, set best to 0 and put the last error line in note.";
    let scored = agent(score_prompt, #{
        label: "score-generation-" + generation.to_string(),
        capability_mode: "execute",
        model: "grok-4.5",
        output_schema: lesson_schema,
        phase: "Score",
    });
    if scored != () && scored.success && scored.output != () && scored.output.best != () {
        best = scored.output.best;
        if scored.output.stalls != () {
            stalls = scored.output.stalls;
        }
    }
    log("after generation " + generation.to_string() + " best " + best.to_string() + "/48");
    phase("Oversee");
}

complete(#{
    best: best,
    generations: generation,
    stalls: stalls,
    stop: best >= 30,
});
