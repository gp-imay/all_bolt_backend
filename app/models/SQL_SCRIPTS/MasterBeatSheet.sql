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
        "Opening Image": "Sets up the tone and initial world of the story",
        "Theme Stated": "The message or lesson of the story is hinted at",
        "Set-Up": "Introduces main characters and their world before the change",
        "Catalyst": "The inciting incident that sets the story in motion",
        "Debate": "The protagonist wrestles with the call to action",
        "Break into Two": "The protagonist makes a choice and enters the new world",
        "B Story": "A secondary story or relationship that often carries the theme",
        "Fun and Games": "The promise of the premise is explored",
        "Midpoint": "A major turning point that raises the stakes",
        "Bad Guys Close In": "External and internal pressures intensify",
        "All Is Lost": "The protagonist hits rock bottom",
        "Dark Night of the Soul": "The protagonist''s lowest moment",
        "Break into Three": "The protagonist finds the solution",
        "Finale": "The protagonist proves they''ve changed and succeeds",
        "Final Image": "Shows how much the world has changed from the opening"
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
        "Ordinary World": "The hero''s normal life before the adventure",
        "Call to Adventure": "The initial challenge or problem appears",
        "Refusal of the Call": "The hero''s initial reluctance or fear",
        "Meeting the Mentor": "The hero finds guidance",
        "Crossing the Threshold": "The hero commits to the adventure",
        "Tests, Allies, and Enemies": "The hero faces early challenges",
        "Approach to the Inmost Cave": "Preparation for the major challenge",
        "Ordeal": "The hero faces a major crisis",
        "Reward": "The hero achieves their goal but faces consequences",
        "The Road Back": "The hero begins their return journey",
        "Resurrection": "The hero faces a final test",
        "Return with the Elixir": "The hero brings their learning home"
    }'::jsonb,
    NOW()
);