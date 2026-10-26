let meta = #{
    name: "blend-search",
    description: "Blend the saved forests on 2024 without a new fit",
    when_to_use: "Search pairs of saved forests. /blend-search",
    phases: [
        #{ title: "Blend", detail: "score saved forests and keep a pair only above 26" },
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

phase("Blend");
let prompt = "Run one command and wait until it exits. Workspace: C:/Users/Jacob/Downloads/congressional app. ";
prompt += "py -3.14 scripts/blend_search.py. ";
prompt += "This scores saved forests on the 2024 rolled file. It does not fit and does not download. ";
prompt += "Do not edit scripts/, app/, or models/paper_forest.joblib. ";
prompt += "When it exits, read models/blend_search_note.txt. Return best as the integer in that note. Put the last printed line in note. ";
prompt += "A high score means resemblance to later fraud-type exclusions. Do not say the firm committed fraud.";
let scored = agent(prompt, #{
    label: "blend-saved",
    capability_mode: "execute",
    model: "grok-4.5",
    output_schema: schema,
    phase: "Blend",
});
if scored != () && scored.success && scored.output != () {
    complete(scored.output);
}
complete(#{ best: 26, note: "blend agent did not return" });
