let meta = #{
    name: "combine-forest",
    description: "Refit the 25/48 forest with line-level columns already on disk",
    when_to_use: "Add built feature columns to spec 357. /combine-forest",
    phases: [
        #{ title: "Combine", detail: "357 tree settings, columns already on disk" },
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

let jobs = ["05", "06", "07", "08", "09", "10", "11", "12"];
let base = "C:/Users/Jacob/Downloads/congressional app";
let best = 25;

phase("Combine");
for job in jobs {
    if best >= 30 {
        break;
    }
    let room = budget();
    if room.remaining < 1 {
        log("combine fits stopped with no agent budget left");
        break;
    }
    let prompt = "Run this command and wait until it exits. Workspace: " + base + ". ";
    prompt += "py -3.14 scripts/combine_forest.py fit models/column_packs/" + job + ".json. ";
    prompt += "The script rejects a spec whose tree settings differ from models/specs/357.json. Do not edit the spec to force it through. ";
    prompt += "Do not download a CMS file. Do not edit scripts/, app/, or models/paper_forest.joblib. ";
    prompt += "When it exits, read models/column_pack_note.txt. Return best as 25 unless the note prints a higher confirm_top1. Put the last printed line in note. ";
    prompt += "A high score means resemblance to later fraud-type exclusions. Do not say the firm committed fraud.";
    let fitted = agent(prompt, #{
        label: "combine-" + job,
        capability_mode: "execute",
        model: "grok-4.5",
        output_schema: fit_schema,
        phase: "Combine",
    });
    if fitted != () && fitted.success && fitted.output != () && fitted.output.best != () && fitted.output.best > best {
        best = fitted.output.best;
    }
    log("after combine " + job + " best " + best.to_string());
}

complete(#{ best: best, stop: best >= 30 });
