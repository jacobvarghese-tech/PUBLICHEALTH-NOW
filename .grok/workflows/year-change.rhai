let meta = #{
    name: "year-change",
    description: "Score 2024 rows by their change from prior rolled years",
    when_to_use: "Look for providers who moved against their own history. /year-change",
    phases: [
        #{ title: "Change", detail: "one prior year at a time, no download" },
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

let years = ["2023", "2022", "2021", "2020"];
let best = 0;

phase("Change");
for year in years {
    let prompt = "Run one command and wait until it exits. Workspace: C:/Users/Jacob/Downloads/congressional app. ";
    prompt += "py -3.14 scripts/year_change.py " + year + ". ";
    prompt += "This reads rolled files already on disk. It does not fit a forest and does not download. ";
    prompt += "Do not edit scripts/, app/, or models/paper_forest.joblib. ";
    prompt += "When it exits, read models/year_change_note.txt. Return best as the integer before /48. Put the last printed line in note. ";
    prompt += "A high score means resemblance to later fraud-type exclusions. Do not say the firm committed fraud.";
    let scored = agent(prompt, #{
        label: "change-" + year,
        capability_mode: "execute",
        model: "grok-4.5",
        output_schema: schema,
        phase: "Change",
    });
    if scored != () && scored.success && scored.output != () && scored.output.best != () && scored.output.best > best {
        best = scored.output.best;
    }
    log("after prior " + year + " best " + best.to_string());
}
complete(#{ best: best });
