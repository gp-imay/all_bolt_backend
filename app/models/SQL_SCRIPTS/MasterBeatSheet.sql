-- seed_master_beatsheets.sql

-- Blake Snyder Beat Sheet
INSERT INTO master_beat_sheets (
    id,
    name,
    beat_sheet_type,
    description,
    number_of_beats,
    template,
    created_at
) VALUES (
    gen_random_uuid(),
    'Blake Snyder''s Beat Sheet',
    'BLAKE_SNYDER',
    'The classic Save the Cat! beat sheet structure for screenwriting',
    15,
    '{
  "beats": [
    {"name": "Opening Image", "description": "Sets up the tone and initial world of the story", "position": 1, "number_of_scenes": 4},
    {"name": "Theme Stated", "description": "The message or lesson of the story is hinted at", "position": 2, "number_of_scenes": 4},
    {"name": "Set-Up", "description": "Introduces main characters and their world before the change", "position": 3, "number_of_scenes": 4},
    {"name": "Catalyst", "description": "The inciting incident that sets the story in motion", "position": 4, "number_of_scenes": 4},
    {"name": "Debate", "description": "The protagonist wrestles with the call to action", "position": 5, "number_of_scenes": 4},
    {"name": "Break into Two", "description": "The protagonist makes a choice and enters the new world", "position": 6, "number_of_scenes": 4},
    {"name": "B Story", "description": "A secondary story or relationship that often carries the theme", "position": 7, "number_of_scenes": 4},
    {"name": "Fun and Games", "description": "The promise of the premise is explored", "position": 8, "number_of_scenes": 4},
    {"name": "Midpoint", "description": "A major turning point that raises the stakes", "position": 9, "number_of_scenes": 4},
    {"name": "Bad Guys Close In", "description": "External and internal pressures intensify", "position": 10, "number_of_scenes": 4},
    {"name": "All Is Lost", "description": "The protagonist hits rock bottom", "position": 11, "number_of_scenes": 4},
    {"name": "Dark Night of the Soul", "description": "The protagonist''s lowest moment", "position": 12, "number_of_scenes": 4},
    {"name": "Break into Three", "description": "The protagonist finds the solution", "position": 13, "number_of_scenes": 4},
    {"name": "Finale", "description": "The protagonist proves they''ve changed and succeeds", "position": 14, "number_of_scenes": 4},
    {"name": "Final Image", "description": "Shows how much the world has changed from the opening", "position": 15, "number_of_scenes": 4}
  ]
}'::jsonb,
    NOW()
);

-- Hero's Journey
INSERT INTO master_beat_sheets (
    id,
    name,
    beat_sheet_type,
    description,
    number_of_beats,
    template,
    created_at
) VALUES (
    gen_random_uuid(),
    'The Hero''s Journey',
    'HERO_JOURNEY',
    'Campbell/Vogler''s mythic structure for storytelling',
    12,
    '{
  "beats": [
    {"name": "Ordinary World", "description": "The hero''s normal life before the adventure", "position": 1, "number_of_scenes": 4},
    {"name": "Call to Adventure", "description": "The initial challenge or problem appears", "position": 2, "number_of_scenes": 4},
    {"name": "Refusal of the Call", "description": "The hero''s initial reluctance or fear", "position": 3, "number_of_scenes": 4},
    {"name": "Meeting the Mentor", "description": "The hero finds guidance", "position": 4, "number_of_scenes": 4},
    {"name": "Crossing the Threshold", "description": "The hero commits to the adventure", "position": 5, "number_of_scenes": 4},
    {"name": "Tests, Allies, and Enemies", "description": "The hero faces early challenges", "position": 6, "number_of_scenes": 4},
    {"name": "Approach to the Inmost Cave", "description": "Preparation for the major challenge", "position": 7, "number_of_scenes": 4},
    {"name": "Ordeal", "description": "The hero faces a major crisis", "position": 8, "number_of_scenes": 4},
    {"name": "Reward", "description": "The hero achieves their goal but faces consequences", "position": 9, "number_of_scenes": 4},
    {"name": "The Road Back", "description": "The hero begins their return journey", "position": 10, "number_of_scenes": 4},
    {"name": "Resurrection", "description": "The hero faces a final test", "position": 11, "number_of_scenes": 4},
    {"name": "Return with the Elixir", "description": "The hero brings their learning home", "position": 12, "number_of_scenes": 4}
  ]
}'::jsonb,
    NOW()
);