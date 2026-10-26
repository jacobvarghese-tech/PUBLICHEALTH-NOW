let meta = #{
    name: "code-concentration",
    description: "Score providers by how concentrated their procedure codes are",
    when_to_use: "Use the line stores already on disk. /code-concentration",
    phases: [
        #{ title: "Score", detail: "one year at a time, no download" },
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

let years = ["2019", "2018", "2017"];
let best = 0;

phase("Score");
for year in years {
    let prompt = "Run one command and wait until it exits. Workspace: C:/Users/Jacob/Downloads/congressional app. ";
    prompt += "py -3.14 scripts/code_concentration.py " + year + ". ";
    prompt += "This reads a sqlite line store already on disk. If the store is missing, the command fails. Do not download. ";
    prompt += "Do not edit scripts/, app/, or models/paper_forest.joblib. ";
    prompt += "When it exits, read models/code_concentration_note.txt. Return best as the integer before the slash. Put the last printed line in note. If it fails, return best 0 and the error in note. ";
    prompt += "A high score means resemblance to later fraud-type exclusions. Do not say the firm committed fraud.";
    let scored = agent(prompt, #{
        label: "codes-" + year,
        capability_mode: "execute",
        model: "grok-4.5",
        output_schema: schema,
        phase: "Score",
    });
    if scored != () && scored.success && scored.output != () && scored.output.best != () && scored.output.best > best {
        best = scored.output.best;
    }
    log("after year " + year + " best " + best.to_string());
}
complete(#{ best: best });
