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
    {
      "name": "Opening Image",
      "position": 1,
      "description": "Sets up the tone and initial world of the story",
      "number_of_scenes": 1,
      "page_count": 2,
      "word_count_minimum": 200,
      "word_count_maximum": 500
    },
    {
      "name": "Theme Stated",
      "position": 2,
      "description": "The message or lesson of the story is hinted at",
      "number_of_scenes": 2,
      "page_count": 4,
      "word_count_minimum": 600,
      "word_count_maximum": 800
    },
    {
      "name": "Set-Up",
      "position": 3,
      "description": "Introduces main characters and their world before the change",
      "number_of_scenes": 4,
      "page_count": 10,
      "word_count_minimum": 2000,
      "word_count_maximum": 3000
    },
    {
      "name": "Catalyst",
      "position": 4,
      "description": "The inciting incident that sets the story in motion",
      "number_of_scenes": 3,
      "page_count": 4,
      "word_count_minimum": 600,
      "word_count_maximum": 800
    },
    {
      "name": "Debate",
      "position": 5,
      "description": "The protagonist wrestles with the call to action",
      "number_of_scenes": 4,
      "page_count": 6,
      "word_count_minimum": 1000,
      "word_count_maximum": 1600
    },
    {
      "name": "Break into Two",
      "position": 6,
      "description": "The protagonist makes a choice and enters the new world",
      "number_of_scenes": 2,
      "page_count": 4,
      "word_count_minimum": 600,
      "word_count_maximum": 800
    },
    {
      "name": "B Story",
      "position": 7,
      "description": "A secondary story or relationship that often carries the theme",
      "number_of_scenes": 4,
      "page_count": 4,
      "word_count_minimum": 600,
      "word_count_maximum": 800
    },
    {
      "name": "Fun and Games",
      "position": 8,
      "description": "The promise of the premise is explored",
      "number_of_scenes": 12,
      "page_count": 20,
      "word_count_minimum": 4000,
      "word_count_maximum": 6000
    },
    {
      "name": "Midpoint",
      "position": 9,
      "description": "A major turning point that raises the stakes",
      "number_of_scenes": 2,
      "page_count": 4,
      "word_count_minimum": 700,
      "word_count_maximum": 1000
    },
    {
      "name": "Bad Guys Close In",
      "position": 10,
      "description": "External and internal pressures intensify",
      "number_of_scenes": 5,
      "page_count": 12,
      "word_count_minimum": 2000,
      "word_count_maximum": 3000
    },
    {
      "name": "All Is Lost",
      "position": 11,
      "description": "The protagonist hits rock bottom",
      "number_of_scenes": 2,
      "page_count": 4,
      "word_count_minimum": 600,
      "word_count_maximum": 800
    },
    {
      "name": "Dark Night of the Soul",
      "position": 12,
      "description": "The protagonist\'s lowest moment",
      "number_of_scenes": 3,
      "page_count": 4,
      "word_count_minimum": 500,
      "word_count_maximum": 700
    },
    {
      "name": "Break into Three",
      "position": 13,
      "description": "The protagonist finds the solution",
      "number_of_scenes": 2,
      "page_count": 4,
      "word_count_minimum": 600,
      "word_count_maximum": 800
    },
    {
      "name": "Finale",
      "position": 14,
      "description": "The protagonist proves they\'ve changed and succeeds",
      "number_of_scenes": 8,
      "page_count": 16,
      "word_count_minimum": 3000,
      "word_count_maximum": 6000
    },
    {
      "name": "Final Image",
      "position": 15,
      "description": "Shows how much the world has changed from the opening",
      "number_of_scenes": 1,
      "page_count": 2,
      "word_count_minimum": 200,
      "word_count_maximum": 500
    }
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