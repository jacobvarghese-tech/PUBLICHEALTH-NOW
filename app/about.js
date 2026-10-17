fetch("data/rankings.json")
  .then((response) => response.json())
  .then((data) => {
    const gate = data.gate;
    const target = document.querySelector("#gate-count");
    if (!target) return;
    const lines = [
      `Joined fraud-type NPIs in the prepared file: ${gate.uniquePositives}.`,
      `Physician-file matches across the watched groups: ${gate.physicianMatches}.`,
      `DMEPOS referring-provider catheter matches, 2021–2024: ${gate.catheterMatches}.`,
      `Archived exclusion NPIs not in the current file: ${gate.archivedRecovered}. These were not joined to billing rows.`,
      `Named labs resolved to an NPI and not already a joined positive: ${gate.namedLabsResolved}.`,
    ];
    target.textContent = lines.join(" ");
  })
  .catch(() => {
    const target = document.querySelector("#gate-count");
    if (target) target.textContent = "Open this page from the app folder so the count file can load.";
  });
