let meta = #{
    name: "feature-sample",
    description: "Fit the 357 pattern with different column samples",
    when_to_use: "Try column samples the earlier forests never changed. /feature-sample",
    phases: [
        #{ title: "Fit", detail: "specs 610-625, one at a time" },
    ],
};

let schema = #{
    "type": "object",
    "required": ["best", "note"],
    "properties": #{
        "best": #{ "type": "integer" },
        "note": #{ "type": "string" },
    },
};

let jobs = ["610","611","612","613","614","615","616","617","618","619","620","621","622","623","624","625"];
let best = 26;

phase("Fit");
for job in jobs {
    if best >= 30 {
        break;
    }
    let room = budget();
    if room.remaining < 1 {
        log("feature sample stopped with no agent budget left");
        break;
    }
    let prompt = "Run one command and wait until it exits. Workspace: C:/Users/Jacob/Downloads/congressional app. ";
    prompt += "py -3.14 scripts/model_islands.py fit models/specs/" + job + ".json. ";
    prompt += "Do not start a second fit. Do not edit scripts/, app/, or models/paper_forest.joblib. ";
    prompt += "2023 and 2024 must not enter the fit. If the command fails, record the error and return best 26. ";
    prompt += "When it exits, read models/model_island_note.txt. Return best as the confirm_top1 integer if it is higher than 26, otherwise 26. Put the last confirm line in note. ";
    prompt += "A high score means resemblance to later fraud-type exclusions. Do not say the firm committed fraud.";
    let fitted = agent(prompt, #{
        label: "sample-" + job,
        capability_mode: "execute",
        model: "grok-4.5",
        output_schema: schema,
        phase: "Fit",
    });
    if fitted != () && fitted.success && fitted.output != () && fitted.output.best != () && fitted.output.best > best {
        best = fitted.output.best;
    }
    log("after sample " + job + " best " + best.to_string());
}
complete(#{ best: best });
