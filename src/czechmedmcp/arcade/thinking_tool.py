"""Arcade wrapper for the sequential thinking tool."""

import json
from typing import Annotated

from czechmedmcp.arcade import arcade_app
from czechmedmcp.thinking.sequential import _sequential_thinking
from czechmedmcp.thinking_tracker import mark_thinking_used


@arcade_app.tool
async def think(
    thought: Annotated[
        str,
        "Current thinking step for analysis",
    ],
    thoughtNumber: Annotated[
        int,
        "Current thought number, starting at 1",
    ],
    totalThoughts: Annotated[
        int,
        "Estimated total thoughts needed for complete analysis",
    ],
    nextThoughtNeeded: Annotated[
        bool,
        "Whether more thinking steps are needed after this one",
    ] = True,
) -> str:
    """REQUIRED FIRST STEP: Perform structured sequential thinking for ANY biomedical research task.

    You MUST use this tool BEFORE any search or fetch operations when:
    - Researching ANY biomedical topic (genes, diseases, variants, trials)
    - Planning to use multiple CzechMedMCP tools
    - Answering questions that require analysis or synthesis
    - Comparing information from different sources
    - Making recommendations or drawing conclusions

    Sequential thinking ensures you:
    1. Fully understand the research question
    2. Plan an optimal search strategy
    3. Identify all relevant data sources
    4. Structure your analysis properly
    5. Deliver comprehensive, well-reasoned results

    ## Usage Pattern:
    1. Start with thoughtNumber=1 to initiate analysis
    2. Progress through numbered thoughts sequentially
    3. Adjust totalThoughts estimate as understanding develops
    4. Set nextThoughtNeeded=False only when analysis is complete
    """
    # Clamp ge=1 constraints
    thoughtNumber = max(1, thoughtNumber)
    totalThoughts = max(1, totalThoughts)

    # Mark that thinking has been used
    mark_thinking_used()

    result = await _sequential_thinking(
        thought=thought,
        thoughtNumber=thoughtNumber,
        totalThoughts=totalThoughts,
        nextThoughtNeeded=nextThoughtNeeded,
    )

    return json.dumps(
        {
            "domain": "thinking",
            "result": result,
            "thoughtNumber": thoughtNumber,
            "nextThoughtNeeded": nextThoughtNeeded,
        },
        ensure_ascii=False,
    )
