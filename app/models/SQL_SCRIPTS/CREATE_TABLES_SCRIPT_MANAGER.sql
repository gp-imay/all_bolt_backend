-- public.alembic_version definition

-- Drop table

-- DROP TABLE public.alembic_version;

-- CREATE TABLE public.alembic_version (
-- 	version_num varchar(32) NOT NULL,
-- 	CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
-- );


-- public.master_beat_sheets definition

-- Drop table

-- DROP TABLE public.master_beat_sheets;

CREATE TABLE public.master_beat_sheets (
	"name" varchar(255) NOT NULL,
	beat_sheet_type public."beatsheettype" NOT NULL,
	description text NOT NULL,
	number_of_beats int4 NOT NULL,
	"template" json NOT NULL,
	created_at timestamptz DEFAULT now() NULL,
	updated_at timestamptz NULL,
	id uuid NOT NULL,
	CONSTRAINT master_beat_sheets_beat_sheet_type_key UNIQUE (beat_sheet_type),
	CONSTRAINT master_beat_sheets_pkey PRIMARY KEY (id)
);
CREATE INDEX ix_master_beat_sheets_id ON public.master_beat_sheets USING btree (id);


-- public."new" definition

-- Drop table

-- DROP TABLE public."new";

CREATE TABLE public."new" (
	"new" varchar NULL,
	id uuid NOT NULL,
	CONSTRAINT new_pkey PRIMARY KEY (id)
);
CREATE INDEX ix_new_id ON public.new USING btree (id);


-- public.users definition

-- Drop table

-- DROP TABLE public.users;

CREATE TABLE public.users (
	email varchar NOT NULL,
	phone varchar NULL,
	full_name varchar NOT NULL,
	email_verified bool NULL,
	phone_verified bool NULL,
	is_active bool NULL,
	is_anonymous bool NULL,
	auth_role varchar NULL,
	auth_provider varchar NULL,
	created_at timestamptz DEFAULT now() NULL,
	updated_at timestamptz NULL,
	last_sign_in timestamptz NULL,
	app_metadata json NULL,
	user_metadata json NULL,
	id uuid NOT NULL,
	supabase_uid varchar NOT NULL,
	is_super_user bool NULL,
	CONSTRAINT users_pkey PRIMARY KEY (id)
);
CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_id ON public.users USING btree (id);


-- public.scripts definition

-- Drop table

-- DROP TABLE public.scripts;

CREATE TABLE public.scripts (
	title varchar(255) NOT NULL,
	subtitle varchar(255) NULL,
	genre varchar(100) NOT NULL,
	story text NOT NULL,
	is_file_uploaded bool NOT NULL,
	file_url varchar(512) NULL,
	created_at timestamptz DEFAULT now() NULL,
	updated_at timestamptz NULL,
	user_id uuid NOT NULL,
	id uuid NOT NULL,
	script_progress int4 NULL,
	creation_method public."scriptcreationmethod" NOT NULL,
	CONSTRAINT scripts_pkey PRIMARY KEY (id),
	CONSTRAINT scripts_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE INDEX ix_scripts_id ON public.scripts USING btree (id);
CREATE INDEX ix_scripts_title ON public.scripts USING btree (title);


-- public.beats definition

-- Drop table

-- DROP TABLE public.beats;

CREATE TABLE public.beats (
	script_id uuid NOT NULL,
	master_beat_sheet_id uuid NOT NULL,
	"position" int4 NOT NULL,
	beat_title varchar(1000) NOT NULL,
	beat_description text NOT NULL,
	created_at timestamptz DEFAULT now() NULL,
	updated_at timestamptz NULL,
	beat_act public."actenum" NOT NULL,
	complete_json jsonb NULL,
	id uuid NOT NULL,
	deleted_at timestamptz NULL,
	is_deleted bool NULL,
	CONSTRAINT beats_pkey PRIMARY KEY (id),
	CONSTRAINT unique_beat_title_per_script UNIQUE (script_id, beat_title),
	CONSTRAINT unique_position_per_script UNIQUE (script_id, "position"),
	CONSTRAINT beats_master_beat_sheet_id_fkey FOREIGN KEY (master_beat_sheet_id) REFERENCES public.master_beat_sheets(id),
	CONSTRAINT beats_script_id_fkey FOREIGN KEY (script_id) REFERENCES public.scripts(id) ON DELETE CASCADE
);
CREATE INDEX ix_beats_id ON public.beats USING btree (id);


-- public.scene_description_beats definition

-- Drop table

-- DROP TABLE public.scene_description_beats;

CREATE TABLE public.scene_description_beats (
	beat_id uuid NOT NULL,
	"position" int4 NOT NULL,
	scene_heading varchar(1000) NOT NULL,
	scene_description text NOT NULL,
	created_at timestamptz DEFAULT now() NULL,
	updated_at timestamptz NULL,
	id uuid NOT NULL,
	deleted_at timestamptz NULL,
	is_deleted bool NULL,
	CONSTRAINT scene_description_beats_pkey PRIMARY KEY (id),
	CONSTRAINT scene_description_beats_beat_id_fkey FOREIGN KEY (beat_id) REFERENCES public.beats(id) ON DELETE CASCADE
);
CREATE INDEX ix_scene_description_beats_id ON public.scene_description_beats USING btree (id);


-- public.scene_segments definition

-- Drop table

-- DROP TABLE public.scene_segments;

CREATE TABLE public.scene_segments (
	script_id uuid NOT NULL,
	beat_id uuid NULL,
	scene_description_id uuid NULL,
	segment_number float8 NOT NULL,
	created_at timestamptz DEFAULT now() NULL,
	updated_at timestamptz NULL,
	id uuid NOT NULL,
	deleted_at timestamptz NULL,
	is_deleted bool NULL,
	CONSTRAINT scene_segments_pkey PRIMARY KEY (id),
	CONSTRAINT scene_segments_beat_id_fkey FOREIGN KEY (beat_id) REFERENCES public.beats(id) ON DELETE SET NULL,
	CONSTRAINT scene_segments_scene_description_id_fkey FOREIGN KEY (scene_description_id) REFERENCES public.scene_description_beats(id) ON DELETE SET NULL,
	CONSTRAINT scene_segments_script_id_fkey FOREIGN KEY (script_id) REFERENCES public.scripts(id) ON DELETE CASCADE
);
CREATE INDEX ix_scene_segments_id ON public.scene_segments USING btree (id);

-- public.scene_segment_components definition

-- Drop table

-- DROP TABLE public.scene_segment_components;

CREATE TABLE public.scene_segment_components (
	scene_segment_id uuid NOT NULL,
	component_type public."componenttype" NOT NULL,
	"position" float8 NOT NULL,
	"content" text NOT NULL,
	character_name varchar(255) NULL,
	parenthetical text NULL,
	created_at timestamptz DEFAULT now() NULL,
	updated_at timestamptz NULL,
	id uuid NOT NULL,
	deleted_at timestamptz NULL,
	is_deleted bool NULL,
	CONSTRAINT scene_segment_components_pkey PRIMARY KEY (id),
	CONSTRAINT scene_segment_components_scene_segment_id_fkey FOREIGN KEY (scene_segment_id) REFERENCES public.scene_segments(id) ON DELETE CASCADE
);
CREATE INDEX ix_scene_segment_components_id ON public.scene_segment_components USING btree (id);