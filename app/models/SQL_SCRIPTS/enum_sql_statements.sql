INSERT INTO "SELECT 'CREATE TYPE ' || n.nspname || '.' || t.typname || ' AS ENUM (' ||
       string_agg(quote_literal(e.enumlabel), ', ' ORDER BY e.enumsortorder) || ');'
FROM pg_type t
JOIN pg_enum e ON t.oid = e.enumtypid
JOIN pg_namespace n ON n.oid = t.typnamespace
GROUP BY n.nspname, t.typname
" ("?column?") VALUES
	 ('CREATE TYPE public.actenum AS ENUM (''act_1'', ''act_2a'', ''act_2b'', ''act_3'');'),
	 ('CREATE TYPE public.beatsheettype AS ENUM (''BLAKE_SNYDER'', ''HERO_JOURNEY'', ''STORY_CIRCLE'', ''PIXAR_STRUCTURE'', ''TV_BEAT_SHEET'', ''MINI_MOVIE'', ''INDIE_FILM'');'),
	 ('CREATE TYPE public.componenttype AS ENUM (''HEADING'', ''ACTION'', ''DIALOGUE'', ''TRANSITION'', ''CHARACTER'');'),
	 ('CREATE TYPE public.scenegenerationstatus AS ENUM (''NOT_STARTED'', ''IN_PROGRESS'', ''COMPLETED'', ''FAILED'');'),
	 ('CREATE TYPE public.scriptcreationmethod AS ENUM (''FROM_SCRATCH'', ''WITH_AI'', ''UPLOAD'');');
