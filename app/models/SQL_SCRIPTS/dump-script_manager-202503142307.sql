PGDMP  !                    }            script_manager    16.4 (Postgres.app)    16.4 (Postgres.app) G    �           0    0    ENCODING    ENCODING        SET client_encoding = 'UTF8';
                      false            �           0    0 
   STDSTRINGS 
   STDSTRINGS     (   SET standard_conforming_strings = 'on';
                      false            �           0    0 
   SEARCHPATH 
   SEARCHPATH     8   SELECT pg_catalog.set_config('search_path', '', false);
                      false            �           1262    16730    script_manager    DATABASE     z   CREATE DATABASE script_manager WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'en_US.UTF-8';
    DROP DATABASE script_manager;
                postgres    false                        2615    2200    public    SCHEMA        CREATE SCHEMA public;
    DROP SCHEMA public;
                pg_database_owner    false            �           0    0    SCHEMA public    COMMENT     6   COMMENT ON SCHEMA public IS 'standard public schema';
                   pg_database_owner    false    4            d           1247    16830    actenum    TYPE     ]   CREATE TYPE public.actenum AS ENUM (
    'act_1',
    'act_2a',
    'act_2b',
    'act_3'
);
    DROP TYPE public.actenum;
       public          postgres    false    4            ^           1247    16770    beatsheettype    TYPE     �   CREATE TYPE public.beatsheettype AS ENUM (
    'BLAKE_SNYDER',
    'HERO_JOURNEY',
    'STORY_CIRCLE',
    'PIXAR_STRUCTURE',
    'TV_BEAT_SHEET',
    'MINI_MOVIE',
    'INDIE_FILM'
);
     DROP TYPE public.beatsheettype;
       public          postgres    false    4            v           1247    17062    componenttype    TYPE     }   CREATE TYPE public.componenttype AS ENUM (
    'HEADING',
    'ACTION',
    'DIALOGUE',
    'TRANSITION',
    'CHARACTER'
);
     DROP TYPE public.componenttype;
       public          postgres    false    4            j           1247    16865    scenegenerationstatus    TYPE     z   CREATE TYPE public.scenegenerationstatus AS ENUM (
    'NOT_STARTED',
    'IN_PROGRESS',
    'COMPLETED',
    'FAILED'
);
 (   DROP TYPE public.scenegenerationstatus;
       public          postgres    false    4            [           1247    16762    scriptcreationmethod    TYPE     e   CREATE TYPE public.scriptcreationmethod AS ENUM (
    'FROM_SCRATCH',
    'WITH_AI',
    'UPLOAD'
);
 '   DROP TYPE public.scriptcreationmethod;
       public          postgres    false    4            �            1259    16731    alembic_version    TABLE     X   CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);
 #   DROP TABLE public.alembic_version;
       public         heap    postgres    false    4            �            1259    16839    beats    TABLE     �  CREATE TABLE public.beats (
    script_id uuid NOT NULL,
    master_beat_sheet_id uuid NOT NULL,
    "position" integer NOT NULL,
    beat_title character varying(1000) NOT NULL,
    beat_description text NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    beat_act public.actenum NOT NULL,
    complete_json jsonb,
    id uuid NOT NULL,
    deleted_at timestamp with time zone,
    is_deleted boolean
);
    DROP TABLE public.beats;
       public         heap    postgres    false    4    868            �            1259    16785    master_beat_sheets    TABLE     _  CREATE TABLE public.master_beat_sheets (
    name character varying(255) NOT NULL,
    beat_sheet_type public.beatsheettype NOT NULL,
    description text NOT NULL,
    number_of_beats integer NOT NULL,
    template json NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    id uuid NOT NULL
);
 &   DROP TABLE public.master_beat_sheets;
       public         heap    postgres    false    4    862            �            1259    17107    new    TABLE     M   CREATE TABLE public.new (
    new character varying,
    id uuid NOT NULL
);
    DROP TABLE public.new;
       public         heap    postgres    false    4            �            1259    17046    scene_description_beats    TABLE     |  CREATE TABLE public.scene_description_beats (
    beat_id uuid NOT NULL,
    "position" integer NOT NULL,
    scene_heading character varying(1000) NOT NULL,
    scene_description text NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    id uuid NOT NULL,
    deleted_at timestamp with time zone,
    is_deleted boolean
);
 +   DROP TABLE public.scene_description_beats;
       public         heap    postgres    false    4            �            1259    16889    scene_generation_tracker    TABLE     ~  CREATE TABLE public.scene_generation_tracker (
    script_id uuid NOT NULL,
    beat_id uuid,
    act public.actenum,
    status public.scenegenerationstatus NOT NULL,
    started_at timestamp with time zone DEFAULT now(),
    completed_at timestamp with time zone,
    attempt_count integer,
    id uuid NOT NULL,
    deleted_at timestamp with time zone,
    is_deleted boolean
);
 ,   DROP TABLE public.scene_generation_tracker;
       public         heap    postgres    false    874    868    4            �            1259    17093    scene_segment_components    TABLE     �  CREATE TABLE public.scene_segment_components (
    scene_segment_id uuid NOT NULL,
    component_type public.componenttype NOT NULL,
    "position" double precision NOT NULL,
    content text NOT NULL,
    character_name character varying(255),
    parenthetical text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    id uuid NOT NULL,
    deleted_at timestamp with time zone,
    is_deleted boolean
);
 ,   DROP TABLE public.scene_segment_components;
       public         heap    postgres    false    4    886            �            1259    17071    scene_segments    TABLE     Z  CREATE TABLE public.scene_segments (
    script_id uuid NOT NULL,
    beat_id uuid,
    scene_description_id uuid,
    segment_number double precision NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    id uuid NOT NULL,
    deleted_at timestamp with time zone,
    is_deleted boolean
);
 "   DROP TABLE public.scene_segments;
       public         heap    postgres    false    4            �            1259    16919    scenes    TABLE     �  CREATE TABLE public.scenes (
    beat_id uuid NOT NULL,
    "position" double precision NOT NULL,
    scene_heading character varying(1000) NOT NULL,
    scene_description text NOT NULL,
    dialogue_blocks jsonb,
    estimated_duration double precision,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    id uuid NOT NULL,
    deleted_at timestamp with time zone,
    is_deleted boolean
);
    DROP TABLE public.scenes;
       public         heap    postgres    false    4            �            1259    16746    scripts    TABLE     �  CREATE TABLE public.scripts (
    title character varying(255) NOT NULL,
    subtitle character varying(255),
    genre character varying(100) NOT NULL,
    story text NOT NULL,
    is_file_uploaded boolean NOT NULL,
    file_url character varying(512),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    user_id uuid NOT NULL,
    id uuid NOT NULL,
    script_progress integer,
    creation_method public.scriptcreationmethod NOT NULL
);
    DROP TABLE public.scripts;
       public         heap    postgres    false    4    859            �            1259    16736    users    TABLE     R  CREATE TABLE public.users (
    email character varying NOT NULL,
    phone character varying,
    full_name character varying NOT NULL,
    email_verified boolean,
    phone_verified boolean,
    is_active boolean,
    is_anonymous boolean,
    auth_role character varying,
    auth_provider character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    last_sign_in timestamp with time zone,
    app_metadata json,
    user_metadata json,
    id uuid NOT NULL,
    supabase_uid character varying NOT NULL,
    is_super_user boolean
);
    DROP TABLE public.users;
       public         heap    postgres    false    4            �          0    16731    alembic_version 
   TABLE DATA                 public          postgres    false    215   �\       �          0    16839    beats 
   TABLE DATA                 public          postgres    false    219   �\       �          0    16785    master_beat_sheets 
   TABLE DATA                 public          postgres    false    218   �s       �          0    17107    new 
   TABLE DATA                 public          postgres    false    225   <y       �          0    17046    scene_description_beats 
   TABLE DATA                 public          postgres    false    222   Vy       �          0    16889    scene_generation_tracker 
   TABLE DATA                 public          postgres    false    220   �       �          0    17093    scene_segment_components 
   TABLE DATA                 public          postgres    false    224   ��       �          0    17071    scene_segments 
   TABLE DATA                 public          postgres    false    223   ��       �          0    16919    scenes 
   TABLE DATA                 public          postgres    false    221   ��       �          0    16746    scripts 
   TABLE DATA                 public          postgres    false    217   ��       �          0    16736    users 
   TABLE DATA                 public          postgres    false    216   H�       �           2606    16735 #   alembic_version alembic_version_pkc 
   CONSTRAINT     j   ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);
 M   ALTER TABLE ONLY public.alembic_version DROP CONSTRAINT alembic_version_pkc;
       public            postgres    false    215            �           2606    16846    beats beats_pkey 
   CONSTRAINT     N   ALTER TABLE ONLY public.beats
    ADD CONSTRAINT beats_pkey PRIMARY KEY (id);
 :   ALTER TABLE ONLY public.beats DROP CONSTRAINT beats_pkey;
       public            postgres    false    219            �           2606    16794 9   master_beat_sheets master_beat_sheets_beat_sheet_type_key 
   CONSTRAINT        ALTER TABLE ONLY public.master_beat_sheets
    ADD CONSTRAINT master_beat_sheets_beat_sheet_type_key UNIQUE (beat_sheet_type);
 c   ALTER TABLE ONLY public.master_beat_sheets DROP CONSTRAINT master_beat_sheets_beat_sheet_type_key;
       public            postgres    false    218            �           2606    16792 *   master_beat_sheets master_beat_sheets_pkey 
   CONSTRAINT     h   ALTER TABLE ONLY public.master_beat_sheets
    ADD CONSTRAINT master_beat_sheets_pkey PRIMARY KEY (id);
 T   ALTER TABLE ONLY public.master_beat_sheets DROP CONSTRAINT master_beat_sheets_pkey;
       public            postgres    false    218            �           2606    17113    new new_pkey 
   CONSTRAINT     J   ALTER TABLE ONLY public.new
    ADD CONSTRAINT new_pkey PRIMARY KEY (id);
 6   ALTER TABLE ONLY public.new DROP CONSTRAINT new_pkey;
       public            postgres    false    225            �           2606    17053 4   scene_description_beats scene_description_beats_pkey 
   CONSTRAINT     r   ALTER TABLE ONLY public.scene_description_beats
    ADD CONSTRAINT scene_description_beats_pkey PRIMARY KEY (id);
 ^   ALTER TABLE ONLY public.scene_description_beats DROP CONSTRAINT scene_description_beats_pkey;
       public            postgres    false    222            �           2606    16894 6   scene_generation_tracker scene_generation_tracker_pkey 
   CONSTRAINT     t   ALTER TABLE ONLY public.scene_generation_tracker
    ADD CONSTRAINT scene_generation_tracker_pkey PRIMARY KEY (id);
 `   ALTER TABLE ONLY public.scene_generation_tracker DROP CONSTRAINT scene_generation_tracker_pkey;
       public            postgres    false    220            �           2606    17100 6   scene_segment_components scene_segment_components_pkey 
   CONSTRAINT     t   ALTER TABLE ONLY public.scene_segment_components
    ADD CONSTRAINT scene_segment_components_pkey PRIMARY KEY (id);
 `   ALTER TABLE ONLY public.scene_segment_components DROP CONSTRAINT scene_segment_components_pkey;
       public            postgres    false    224            �           2606    17076 "   scene_segments scene_segments_pkey 
   CONSTRAINT     `   ALTER TABLE ONLY public.scene_segments
    ADD CONSTRAINT scene_segments_pkey PRIMARY KEY (id);
 L   ALTER TABLE ONLY public.scene_segments DROP CONSTRAINT scene_segments_pkey;
       public            postgres    false    223            �           2606    16926    scenes scenes_pkey 
   CONSTRAINT     P   ALTER TABLE ONLY public.scenes
    ADD CONSTRAINT scenes_pkey PRIMARY KEY (id);
 <   ALTER TABLE ONLY public.scenes DROP CONSTRAINT scenes_pkey;
       public            postgres    false    221            �           2606    16753    scripts scripts_pkey 
   CONSTRAINT     R   ALTER TABLE ONLY public.scripts
    ADD CONSTRAINT scripts_pkey PRIMARY KEY (id);
 >   ALTER TABLE ONLY public.scripts DROP CONSTRAINT scripts_pkey;
       public            postgres    false    217            �           2606    17045 "   beats unique_beat_title_per_script 
   CONSTRAINT     n   ALTER TABLE ONLY public.beats
    ADD CONSTRAINT unique_beat_title_per_script UNIQUE (script_id, beat_title);
 L   ALTER TABLE ONLY public.beats DROP CONSTRAINT unique_beat_title_per_script;
       public            postgres    false    219    219            �           2606    16928    scenes unique_position_per_beat 
   CONSTRAINT     u   ALTER TABLE ONLY public.scenes
    ADD CONSTRAINT unique_position_per_beat UNIQUE (beat_id, "position", is_deleted);
 I   ALTER TABLE ONLY public.scenes DROP CONSTRAINT unique_position_per_beat;
       public            postgres    false    221    221    221            �           2606    16850     beats unique_position_per_script 
   CONSTRAINT     l   ALTER TABLE ONLY public.beats
    ADD CONSTRAINT unique_position_per_script UNIQUE (script_id, "position");
 J   ALTER TABLE ONLY public.beats DROP CONSTRAINT unique_position_per_script;
       public            postgres    false    219    219            �           2606    16743    users users_pkey 
   CONSTRAINT     N   ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);
 :   ALTER TABLE ONLY public.users DROP CONSTRAINT users_pkey;
       public            postgres    false    216            �           1259    16861    ix_beats_id    INDEX     ;   CREATE INDEX ix_beats_id ON public.beats USING btree (id);
    DROP INDEX public.ix_beats_id;
       public            postgres    false    219            �           1259    16795    ix_master_beat_sheets_id    INDEX     U   CREATE INDEX ix_master_beat_sheets_id ON public.master_beat_sheets USING btree (id);
 ,   DROP INDEX public.ix_master_beat_sheets_id;
       public            postgres    false    218            �           1259    17114 	   ix_new_id    INDEX     7   CREATE INDEX ix_new_id ON public.new USING btree (id);
    DROP INDEX public.ix_new_id;
       public            postgres    false    225            �           1259    17059    ix_scene_description_beats_id    INDEX     _   CREATE INDEX ix_scene_description_beats_id ON public.scene_description_beats USING btree (id);
 1   DROP INDEX public.ix_scene_description_beats_id;
       public            postgres    false    222            �           1259    16905    ix_scene_generation_tracker_id    INDEX     a   CREATE INDEX ix_scene_generation_tracker_id ON public.scene_generation_tracker USING btree (id);
 2   DROP INDEX public.ix_scene_generation_tracker_id;
       public            postgres    false    220            �           1259    17106    ix_scene_segment_components_id    INDEX     a   CREATE INDEX ix_scene_segment_components_id ON public.scene_segment_components USING btree (id);
 2   DROP INDEX public.ix_scene_segment_components_id;
       public            postgres    false    224            �           1259    17092    ix_scene_segments_id    INDEX     M   CREATE INDEX ix_scene_segments_id ON public.scene_segments USING btree (id);
 (   DROP INDEX public.ix_scene_segments_id;
       public            postgres    false    223            �           1259    16934    ix_scenes_id    INDEX     =   CREATE INDEX ix_scenes_id ON public.scenes USING btree (id);
     DROP INDEX public.ix_scenes_id;
       public            postgres    false    221            �           1259    16759    ix_scripts_id    INDEX     ?   CREATE INDEX ix_scripts_id ON public.scripts USING btree (id);
 !   DROP INDEX public.ix_scripts_id;
       public            postgres    false    217            �           1259    16760    ix_scripts_title    INDEX     E   CREATE INDEX ix_scripts_title ON public.scripts USING btree (title);
 $   DROP INDEX public.ix_scripts_title;
       public            postgres    false    217            �           1259    16744    ix_users_email    INDEX     H   CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);
 "   DROP INDEX public.ix_users_email;
       public            postgres    false    216            �           1259    16745    ix_users_id    INDEX     ;   CREATE INDEX ix_users_id ON public.users USING btree (id);
    DROP INDEX public.ix_users_id;
       public            postgres    false    216            �           2606    16851 %   beats beats_master_beat_sheet_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.beats
    ADD CONSTRAINT beats_master_beat_sheet_id_fkey FOREIGN KEY (master_beat_sheet_id) REFERENCES public.master_beat_sheets(id);
 O   ALTER TABLE ONLY public.beats DROP CONSTRAINT beats_master_beat_sheet_id_fkey;
       public          postgres    false    218    219    3542            �           2606    16856    beats beats_script_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.beats
    ADD CONSTRAINT beats_script_id_fkey FOREIGN KEY (script_id) REFERENCES public.scripts(id) ON DELETE CASCADE;
 D   ALTER TABLE ONLY public.beats DROP CONSTRAINT beats_script_id_fkey;
       public          postgres    false    217    219    3537            �           2606    17054 <   scene_description_beats scene_description_beats_beat_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.scene_description_beats
    ADD CONSTRAINT scene_description_beats_beat_id_fkey FOREIGN KEY (beat_id) REFERENCES public.beats(id) ON DELETE CASCADE;
 f   ALTER TABLE ONLY public.scene_description_beats DROP CONSTRAINT scene_description_beats_beat_id_fkey;
       public          postgres    false    3544    219    222            �           2606    16900 >   scene_generation_tracker scene_generation_tracker_beat_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.scene_generation_tracker
    ADD CONSTRAINT scene_generation_tracker_beat_id_fkey FOREIGN KEY (beat_id) REFERENCES public.beats(id);
 h   ALTER TABLE ONLY public.scene_generation_tracker DROP CONSTRAINT scene_generation_tracker_beat_id_fkey;
       public          postgres    false    219    220    3544            �           2606    16895 @   scene_generation_tracker scene_generation_tracker_script_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.scene_generation_tracker
    ADD CONSTRAINT scene_generation_tracker_script_id_fkey FOREIGN KEY (script_id) REFERENCES public.scripts(id);
 j   ALTER TABLE ONLY public.scene_generation_tracker DROP CONSTRAINT scene_generation_tracker_script_id_fkey;
       public          postgres    false    220    3537    217            �           2606    17101 G   scene_segment_components scene_segment_components_scene_segment_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.scene_segment_components
    ADD CONSTRAINT scene_segment_components_scene_segment_id_fkey FOREIGN KEY (scene_segment_id) REFERENCES public.scene_segments(id) ON DELETE CASCADE;
 q   ALTER TABLE ONLY public.scene_segment_components DROP CONSTRAINT scene_segment_components_scene_segment_id_fkey;
       public          postgres    false    224    223    3563            �           2606    17082 *   scene_segments scene_segments_beat_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.scene_segments
    ADD CONSTRAINT scene_segments_beat_id_fkey FOREIGN KEY (beat_id) REFERENCES public.beats(id) ON DELETE SET NULL;
 T   ALTER TABLE ONLY public.scene_segments DROP CONSTRAINT scene_segments_beat_id_fkey;
       public          postgres    false    3544    223    219            �           2606    17087 7   scene_segments scene_segments_scene_description_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.scene_segments
    ADD CONSTRAINT scene_segments_scene_description_id_fkey FOREIGN KEY (scene_description_id) REFERENCES public.scene_description_beats(id) ON DELETE SET NULL;
 a   ALTER TABLE ONLY public.scene_segments DROP CONSTRAINT scene_segments_scene_description_id_fkey;
       public          postgres    false    222    3560    223            �           2606    17077 ,   scene_segments scene_segments_script_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.scene_segments
    ADD CONSTRAINT scene_segments_script_id_fkey FOREIGN KEY (script_id) REFERENCES public.scripts(id) ON DELETE CASCADE;
 V   ALTER TABLE ONLY public.scene_segments DROP CONSTRAINT scene_segments_script_id_fkey;
       public          postgres    false    3537    223    217            �           2606    16929    scenes scenes_beat_id_fkey    FK CONSTRAINT     �   ALTER TABLE ONLY public.scenes
    ADD CONSTRAINT scenes_beat_id_fkey FOREIGN KEY (beat_id) REFERENCES public.beats(id) ON DELETE CASCADE;
 D   ALTER TABLE ONLY public.scenes DROP CONSTRAINT scenes_beat_id_fkey;
       public          postgres    false    219    3544    221            �           2606    16754    scripts scripts_user_id_fkey    FK CONSTRAINT     {   ALTER TABLE ONLY public.scripts
    ADD CONSTRAINT scripts_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);
 F   ALTER TABLE ONLY public.scripts DROP CONSTRAINT scripts_user_id_fkey;
       public          postgres    false    217    216    3533            �   F   x���v
Q���W((M��L�K�I�M�L�/K-*���Ss�	uV�PO4H2LKK1063�T״��� ��      �      x��\َ�v}�W\t��4j�C�����5���8Uu�<Vtl�A �C���d�}�Hv�h�����+�0��bk�a����o�>��z�ͫo����:�L��;��^|����2w��pr�%�~Z�B&�+"�v37��I/�ERDy�������p���/� d�*p]����W+e]����Һ��P���j֪�kݯ�Ǻ�����f�Z>��hu&��Ⱥ���խ��Lvt���m��[�)���Z�+녬���W�W:�롐����v(ե�n��%�m3�c�ne�UE��W�J��~Y�MK�]i<dӖ�b�xÚ���l������j�7���42�U{I/��n lW��e{O�_]�����z6����/p&��C_���|�?yj=�CO֓^W�%r�"���!���ZV��~陞Wr�v���/��[�>T�jqXz��.k���M=}�g��X�KU/�,�uO�ka�34 �
O��^��,�Tݺ�;��R�[~�j)��1�1Ϻ���U7��0�}�&h�/�����QGj�G�|�۬Tt�](�;nJ�8�T�t+��Cڗ[��;M\���8o�6�#�t9U�����VD"� _�΢��b���0Ô���y3?��cX�cXab��e�V۽]tO�ߺ��֙�za�ۦWYOd�XX�P��]�,gk�F���z�j�a�2W�����,]���	n�-�k�h���j�*Y1	������	�n�5w����~R�l���<ԼM;�yF��3cٟ�^�ۮ��U+���u=�:=�U�Ό�J7_6�R-���V��5&'{�\�
�����Fg��fv����U�Z���h\`9�0�\ՠ.5�-J�&�>���@��]��.�u��U�S��;g��;cڟ��{�����8���n�F��@3@D���*������S���PwzwF��U�]ZW�f(s��C?���j��[k�j�����׸z���J#����I���t�ǚ�@����x��c:����g�1u}��\����%ֲ��X�N�pWޤa��O������n���J�ji}���1�	,�ej�u(�����^iլW&?�jI�^�MO��OȆ���6Q�FjS�&���?Hڹ�2�.u��6^���d��EO�Y�[�y��+�9p��v{��h	~�Y���_���'�(�v���zo���z\�D,p��#8M��1��@&/�X�Ԥ*V�J�Cu�}�2S;c4Y���uS���뼩f����Pt��a}���c�����z��^<��S֫j�(c�;c5�ݶ��/C�ȑ�㕒m_������ۉ<\`�AL�P&-����o�x��a��,������{�ZЅ���#��N �ʊ��"��k��<�|Z|�4��C8��0c��-xʌ2m���ŉ~_�	V�Fv��o�8L��X_\�� [���l�T�:�4��N���h<�'H����`2ެ:k6:�s2t=�ld
5+�\�B:�%��t48$�z�~������1䟎�풹<�+�R�>e��Z��3�-dL�dP����3k���,�k�gJDd:q��@@5�B$�@�yNn�n�����w��6�ު�R�'��f3�����s(?�}�w֋���rE2b����)&G�!�j�'�&�^+�ݶJ�R�:�s�*��{I�b%9�:�:������|�qm�@���q�W\!�ˆsah�G�;>� �ȓ����[�)ew�+�]<'��3�7�~WYseb���V��o�`=k��3%�A��A+*���%��T��Pxs�e�5u�Դ@%Q��W�Nw!�R�4��b8�7� ��P�;7Sc׫�q/:�6�LR���Mā��g��C%�B�:�Y᎜Pb��Ѡ]qXd��2cиݨ�G�|��0���.7�%����cF-2��$�š�N�����q�|�ZMv�z�&lӭ�1s��/:�����0�'�ǿX��3�����A��zE�ngn@�9/g�}8�q���RWTag�u�$��"�5�1)R늄�t�v*
�d�㭔1P�Vw�8 �<�]�-��t�):����z/uw��7S��z��� �{zY�����*�[������@��=m��M]�=�&|���M�0ٴi��F���ݮ�����'�'t�7��pڎ�"�Q�i |��"-2)2'�b��
��]�����������8"����]�n�ݯ�=�8�_8E$TN�ya$�(r��;�Ud�8|t��qZq������o� *��(N��]7�#�)�,<!� M��w\'t*��ʃv%}���F>��0�az��)���@$^���pI������(���q�|�ۜ�7NU��)�g���T�T&B����<Ty?:�!N��[�1�εN�N�+�b� d<[�Q��B�4uBz��2�I��{t�"�z�gKWy�Z��,O#/��DE���3!���if������=,ƩG=བྷ��-އ:�}�@�w�P$	�TF*sc[�����f�X���{�7~��μ�E�*��~&������v�Kp��N 5�/���{/|׺��`-=`M�Yڙ���~��"U�'v�If��ڴ����}@ۻ��~_�穂�T*��%(I.IX�Q��4(B���2��6���w�I�0�|��<����qb!c[	7�� �rG���s��r������w��~w����BE*��$qC��a,bυ�I'��y�>>[�R�����z��b�27�S�Y?S����v�8q��g.��l7@��.��?xG����J5'x���uR��8r����;"/�b߃��^��f�D�3J8��w�@��3U�Z�p����ir�Kݖ�Ã����]�-�t�L�F	GN�k�� �n9��Ω�aI+��P��$���H�InYí��í.�YKܘ�F���IQ �u:V��c90��ǀ�<�h��m�&4�SZz �w+�5���2��U[q������J�_�k2drTu�V�Ƿ��I���� �t;ysu{��X7^�%�+
����y�i��e���#�jJk渠�v����v�v�}dO��'�INS��VW���E\{ΦR�&�5���<��naH�@��kj�� )�����]5e~����
�E�@s	�a��l�� M�3��� �N�K�qki��ZɍnZz+n���&
*ptG]����M"�G����uC��^�t;���r�D���E�fX�;��)P���r7���?˖C��Nv��L�}��G
��q3fV�g�VEV%f�L_֔�Zr[�3U�4�ݖ~jA�R��V2o����#���+�ɞ{r���Z��f9�6*_�
j��]C��E%�V��F��B���Ƅ"։�dCK�@��5�J��S����_e�*RJ���NR�����i�K�(B����jpE��^�#\ޏwFp+��4�BV�O���i��-�<vmI�q���b��\�Rܑ���H,�0��°�O8c��~l(�u�I���s��������v!����·�7:G)�yGJ���e��A�S2[��6T�9a�7� ��3� �m?sm����ɧ~��&Y��kS}g� �����K/��HUaN�B������B,����8��إ9	�m�!o��c�57/ak t���_�#Qϲ�S��@
�G5�L�6@�L^sKW�%j^.�� 2���*Z��G�z�p��qs�Yw(]*��=����6���H�%�TY�G�[<�%ģ�0Kj��X��MSu�(�~<�Y��pε��&��՚(ÇO9�u��^�\q�W;t��[M���r����Z�<�RO�(XS�
� Ր/�۩Ц���n�&����}ј&J�[���j�Wn�I�2������tG��߉5v��PJh��1�- �d���=,�H�Q����x�EE���=�o�B&���8I�sZ��_쇟�n�;��^5��B��H�Y,E�K�����j�&��T��[X����������9L��a��.���fD�?�4�o<Ѻ馹޹����,�~� �  ;O���vb���M�P�'�ܳ�
������'�(�����٥!���'��W�9�����f�ic:��/M��^��N�|]G�)V�2�3�rI���aKJ�\�j%HQ=�M���aqM�>De���iU9���4�����U�"��n!$�i�Nu*�1�s75��	��3N��&,	<��]�Ϩ�����Q�qC��1@�����q�y*�E.��� e�p����q�<�G��-[O�^�_����u7.:��I���;�N��nBn5 ���H���&�[��LK�����Đ῭G��iר�j�qu�^íL��T�$6�KN���j4�a��fzǺ��'\a���^�`t�i����Ơ�$��@
PcH������ ,�0	�{J޶1�`�;����
*)�#�n�����h���9 ��xr3�����{!}/̇�,�c�g�d��!גR7�+y(��T�F$�����چ�vh� �wy��j�n2�	�,H"T�Q$�8��D� ��8I��E���s�r��u�w��p<��nM �xJ��j�7�j�сƙMLHry���{=�m����z^��L��)H�!,�̈́��k���j�
�������\0R�MnNsM����/e�ͨx/iv����K�N��#��D��\$����͋ ~���_/�y���A���V�WVO����M�����n��o	���0g�\���,�@��6ȸ{���r*]{9��1fc�2�hv����Qʯ�))܃��.}��@Ev�,yb�	%�H�0���wS�k:�6e�W{>r0��V�z�c�2�-�E�P�%�f_敠�옫$Q�����"G0����DRl���Kq^���>L�<g�嫥�G�1x\���B�իq��Y@���'��"E�H���Ņ����Ǝ>����qޒ���4Uǟ����_x��<��*)��Kay�!�TJ/���m^+3L�n�-�3i�wk
U3�����}�Gkn�KJ�f�-�
��k4���5M?�[�ڌ�u��Q�׍U65u[�3�^J�u�'
�Ҕ�f�ϴ����EW��m5�:�-�>�����wc%] Ơ"�!=;�yG�&��p���i���Z�RY?P�:�Y�Y%nZ^�ԓ��Ůu�+UQ�Bf�f�.��U�1c��u�)KB�Rf읶0�5մZ�Tit.x�-v��i>B���V�����9/[�{��; &@t��-=���i��������$h��v?�ٕ�c���7��U�{	wQ�G~t�B?cӬ{�u�v��]���x��0��[�}������aҾ�����FҜ;o�uj�}��^��w���=�}��g����]�>��O�㾙���S������p��z�<���~Noؼbn���Y�����f%�({wُ�Ԭ���>ӹ�3�5�q&9�Is�����f$����f�g�p�a�=�hx�v]3L����X��>�-O�-��9܉h.�y�����y۬}�0ޜ0��N��b�n[�ݚ�i�;;���,Pg7;w۶?ɝ��{9��%H����=6t�����ۻ8\���`�3W������h���n�_���o��47��� �������\IN��q�*b/�
��~�H��v 2��;~ �FP}�����      �   �  x��WMs�6��W����Z)E����Di�:vǲ��t:\��I�@˚L�{$�8����&�v߾�_�����,.�/I^�)g/3��UԬt`4�pz~3_��g)���T���"K{�D�g秿�Wˋ���W��:�R�5gdI�|������mT�L���R���(n�X�� ��ܳ�u����'h��w���3d��5�H/��%~�G|�b�_��"�������+��'#*"�^AS��*���˯�H��D���4�������*��<+2�x��	�>����|E�a�0��� �d�b����x�`S�)�7��I�^O�i����8@0���܁0r!�&��0JFM2�a	U��uI"�&%�I%%<%*�� �y�����[mP㎼p�J%�?"��ʷ�{D� �,�����y!�ˁ�0&�a�J���kC6
�A��7IEMSL!���ch�c8i1t�8S@o1^h�z#4���<F�a=C���$gU@���,2�Ju�cҜa�����i,��#&EDQB��0����	�+��� fU�C�؂�T�� �M!�H����6k��=�f)�v�,WP>b)��<��Fʰ��Ɂ��R{ϣ\����;��O�v��E��Td(� v�o��Te`��Ң�A���U*1t�I�Q��4��=���X5������._	��<K!>����\6j���;�}±+�nI(�����௩�%|������H]];�c�܀�a2���[{ǴAp��&8���7Z|�c.�:dZh�A���m��h����U	����v3HT&�.��rz�_���M�������������4(7$+Xտ��*��L����$�!���߿������`���#��$�x�����;~�����g.n����q<�" L���G�?�� 
�t�C����~}�x�2c�}J�E��Z�������ջ˛���G���fyi���N��'ۚwgu�-���zs�[7!�خ�܍��G�I���*C�S��I�FwXГ������v��_�ֱw���#TI����̇0���<�ڤ���+����к�gi8��'8� T�ҕ�d�=���ek�=F@�=�}���p�Y���$���A[Au"�l2�e�a!gOg�{�>"�@q�;*�\�0��Z�_�����n��ߍ��5Bm���_��8�~��n�t�9����L2{A5\=x��	�9���f�Lw�׼��7T������P��r���� |��Z�f��{%q�;��v����Gk.v^(��+�T�Ŏ�qT��#��"��̀ne\s��[�<���M�}��W�
sr8Em��z"�w�'w./�΢���	���x���xJ�A8��QȦtf;׋���s�      �   
   x���          �      x��\�r�F�}����vcY�*T�R�-_��Ga��8Q�n��@�&M?�g���|ɞ, �-R�ȍ^F8�@73󜓙�w?���ǟ��~��o��`��]�.t��>�nh�S�w��Lc���۟�~���+b-�*2Y�)�ӊ�ᣬ�*�xu��W٫_��5�����B�}ۏc��nl����m��^�����ö�}v��s�LY��G�3����h�Mv���C��i�l��xM��y^0��\f�|�����E�_�x-9����oq$�ԅw�p�`JjΌ.k����F�Uy<:�v���_���K�;ѽ�c����d�z��/�K?�Z�5���쮙����ޙ6�cl\�[3 xL6NCSv�N&6%���K�o��γ��seɽ�U����(|�o̮i�7}���].�A5]��P�D��bt}�e��W:�Q�Y3�p��F�L�
[�J�Q�L�Ymp��E������� ��/�"gu(�+��t�YTR�R�J�5>H�q�fk�6t��O��]�D�>t��$���8�g;�j���H3.�&��=B�z]�ײ�ּ�J?DH�N9�ƋX3�m�lt�y�;�UT�-^!*J�Mۏ�~{��n:!�1�/�P�P�}�p����`��5aB�u���Dm�c���o��*���< ��ajSNIf��3]()�W�9���P���w��?�6�c�9����8���M?�g&����K�"�J<��R��8�>�M�B
�3��
_YHf�*gY��XE_�/�U�/�1�7C��8aq�oq���^���ʯT�`C�6�a�:���'��0P<��7���Q�"gumKTi�PvBʹ��q[�Z��G�P
)+��2C��1�se]n�9�=�7�`�A�_��iT��0�KPl��L���'3n�Hî��lqޘ5]��3ϵ�� �!�)��Nܢ�=0��� T����)�C����;�
_3�g�;��c��ď*�O���3s���������ǋ���.-՟9�.�D�ISW���\�������Q�����U�B�fc\qp���d�Q�
��45��}iZԗ�O��llpu��]�̔ut
H������M�����)��-���5��b�m���
�չ��RC
�UhV�(Jmjm.#��Z�����wC��Gd�/��{�Y���Sr�j�xp>�
:�{E�8�	**qfg��xD�S�yc��*�3N#�T�*��-
q�B��*!2C! ��%��L&�X��.uQ�s��c0�Oߘ�߆i:�LTt��D}mzg��.܍���<��HO �tsL����C͂�i��U�94-J_�4eS�ݑ5�wo�C�q�Z����Z	Y珀-Mm��傄�4�E�xi��dp��\�`k��y:�4"�0.��
�+�9��C]�+ ��l�#��<@T!���m�o& �ۤ���r��E�ܙ�mO�h��F�#�]�t�~h����_��u��+%��!x�<k�MT4�Y:Ws�]P���2����3|d�̐���Gz����E~�f�h�0!��b!�
ʽ�ˌ&��0��v��[��,l�M�>�Q�H-��U�L�R2�,�LA	��*�Ȃ_F�>H"�!��;�y��H�!�A��
8�BbI��)9�^�*�YeQ� ]����(n����0�������1]n�������3�XF�y�Lڀ��橮�)�ʹ��a�'�G,�yI1r��䡅�]6C�+$]w��)!�'�{�]:�j��c�-T�i��`�+$�mIJ'Qh���7�`H�!\�N��Ŵ�`+ja�uL���p���܋�Z��͍�eo����n��m�M�N�"�`�)���9o7��́��_ �۵�1�3w=��� H&�u��e�cd�_?�\P�� �"L��^k\.w�����Q6����,�P���2��8�r�4�,".Fbn7e?�)�Cm�#��BG�&k1�7p�p����޺Ϛ�.�8���6R_d��{��x>}B��*�,�D��U f�rdZ!��
��ps��/	�ǟ�1��'��g�߄�1m;�
�CmD�Z`.f�[�)}�r�X=6O�pJ�?��V^j���L	nQ�b����(�_>uF��MP�~���)w�뒽�>��1W�Ł��wEAu�lZ��D"��Q���t�4{������t��t)t�45��p�ft����Kk_4_�d���ɛ<HX�R�9�zD��8��Aa\�,p�	ɬ��tۄې���t�h\�f���k!�e��>�˝W�H���ˋ�b@�l�V^F�������u+�)�e�t�t�W1�zA45H�xhk�C*�1N-��#���f)��#� gL�޲��;b?L�����QT����yy]���Q�����qh�W���5��2���
��p��8SIH�wa@����ַG�VO���M��>��EY�-����qm7]�����t�gaʍ�%�4�,�wƴf�+�B]C��h8+���j�����Ͼ����?zr�+� �斚w��?�S� a�"��� z4�!1�����e�B*�+B����1
�ߤ~I�����c�ݒ?o��?�fL��n�n�Q&Y�Ӏe���^-Ѵf"�*��L��yz��*V������J���-��S�(pr(�}�BUU����y���*+T?BM�z�#�D.�ۦ��ߙ��2���lc�[�5���y;E �6۔���
%�CaqDL_K.��-�0�Ei+�#Mb�3�*YUU����L>�|E���q15C
���ќ0���4gA,%m{���9��#e�<�K��Q���2�R���3A3E�t��"��J�H؂:7�Y��1��=�����!֛���6���$I�}��:����F���S��Z�>�(��+ɂ!�/k�P����R%���]O�G}$��̹̈́�	4�r)�H�l�ϛ��Cn�!��[��$
����h@��ī]��9��*K��`8��\�x�R%B�D�=�p�j(���p�C�p�>/U��ܭ�Ą��;�e�ڸJ�2�G��:~��6�]�D��mΌ��o�CȂ?�y��!��n�O��^sy���*�����"_6�3:,���|����/	c�fA��l�ܘ�Y��]�����b��۞Z�@�����0F}�iv�Ӻ�@-����D++�τ.7e)�1�U�
�[*e*��)�y�L]ʹi�}�9����r������qm�=�Ք/f�Rxu��xe�
!6��3���6E��~���N����4 XX�����ڪ�X�}I ��ݤ�8��u�=Ho8��a��đbgK8��&)�G���S4ԕ�bw�/��g��d�r�4�����u10Y�RG�k]]�=�+�5��*�hV�0�mD�
BX_���^���о�ʾO$p؝��V|a���s�Q�b�w���"3�i��"q���:ΰĵV�ՅQeP�A�ʔ1��+ŭ)*�ח�a=�4���`���)������ٶGB&k �r�Mn��0��](JVJ�z�g�V�q!cYrUW�2��0Py:F�
���L
��Rֽ1�<��F��61��R���H��y&6�����0#�b*D���qh���}!��4lҦbZgs�����^��e��4@�}�i�B�t�.���C�Y<l�R���K�VS֬.�dEb^���2%��tJ�����6���ͽ[ھtW�CG���)TJ�"�fNZ�;�q�"��OOM<"+R��bpp�=�emhIh��J��е�_�zX�����G3��B���zW�6�el�B���P�/	&%^��$�ʾ�vJJ*����9K�uj*����oe�Uj0��Lʼ&���ñ��;�eCM�v���f�L�*��c�(�pFs����en�+�efmOD�[��9Ye_��5�!�E�R�4u��LX:4��q���F�қ� b 5L����_w���6�0���~���YHC�y��`��pz&b�B^:Q�1�e��
]�9�#+�ʁv
�֢.��BG�cY�է�%�_��r'�Ms����
�k��/;���� �  ��pǅ���?ҁ���?7�6	�� ������Q��KgeE�S4��+�eek�(M�"W�1LO2O+XԱO-�-p#5��A�Iq��{a�n ����B|�p �K�mv�M�����ӈ����Z�gb&ct�f����%���U���Awzy"fT�w��O�~)~��s{ެ����xjxQ:1L�� 	$�����ۜHinĦ���qp	�>���Yɬ.j?XXMk��#�Qʹv�M��>�J]手'��Ƒ�@՟�<��z���K�Ǜ,�+��9����h��?��-�LmI�����U����4g�.��&�W�&N�~-��������c!��k��I� w2�9/��/�@�
ymrńב�2==cH�����z�T�~~2�?w��ND�(���&�B��}k�e5M��e�m��_$"��f�@n�����-G��u-�Z<r�`pKM�[-Z�aY�k���U�i�?�c�fJM�7ۦ�鹱�����N���4#�z����\!nǴ<�CB���:0=�o�a��f��R������ �E�W]Zfs�Z���u�h��ĎR��8��i?d�&n���x�w(�n�6Q�!���+�����-��>Rw�0�?PrZ��g��2<|&~&:U��2W����� ��C�Gt���'�w:77G2{^b]?�2�n�nyNέ٭k5�W�8���=M��`3{"�~.�������c��y~�9���$�*�%��Z��(I�GFJ�K[�(�
�}L+k�Pq�
i�˅pW�2���'���gg{ �M�Z�����9{������#��i�c�����G�4���#q��4N�yTO�lϹz���<DZ��B���ZUD�����*��qo)>�`u5�K���C��$��Y�a��h�I�I66��i����,�;g85�I��2�0��.)��M;Od�&���pK��G5�3�q^K��i�G^���\���Z�p��D�d�x��4�ov�)���i����ɜuyk~�
?�wh��B7�s�:9��iܖ�1�?�@�g���z�ג�UQ3U�%�XU���	!/���#>y��==����5����Zt�ޯ+�����S<��O�|�6�%�Ei �d{3��,�X�@6��0П�1�y�;,r͑�J2�+Ät>'���Ixa#��$��9Ӷ��'i������F w�ڪ��帳�V���u��mS��ݟ�A]�;i��5j�j��H��r�N\��b�<���"?���%�j�%���"EFEz�R�Xм���/���@==1A}�E�,M���i�\��{��->q{��<��kvk��t��!;^�<5�m�>�JiiB��s�TKV[8m�eY Q:/����<M���Mh��Z���82gs�e�3=���J0�ӭ��!tsY���h��-1/����5��Fd�v%g�&G]8r��#6!���⧗�I>J*�_�ps)�h(������g�6C��Y���GZ��Qc��| $p`��ݲ�nlh犘q"���9slKB?�%��S��i��(�
�/w`��hz�3ң<��Q+S8'���h�&ϙ)i���J	�d$�,�)��O_�5��_t���l�	�}ߌKˋ8�/-Y�=��eo�sR�6��av{� ��?A���+��Gh9����6V�h���Ӥ(T^�ʇ�2��'�u|�8��!�h�m����ż0wlu���j�=n�5a\��N"�����ۢ��	Zp���1e�E�p���6�y.��j����l�9�g�n����d7�]w����>df=v~�n֋]] ����cK�;&�E��؞��m ���&�����rYCT[�e�8��EE.*[\F�<�$�G!֥�4a�������^4ITJ�|0?ꅷ���C%P�w���N�֌OEX8h��8�K�pS?���/���      �   e  x��WK�E��W�]��^�]5��^��5����`����o����Y�|Lu�9UէN�=~z�ӳ���Ϟ���G{��oo�|=_�?o껗��~��M���77??�~��拇E��J2@[W0�+���3��X��yؕmVf��".K�*�PZ�{��(�?��������~w�c���|C���([vK_a�߯��c�B��Ҁb%>���������/X�����7�>�L;�M�����ʱ�
ܜ@���	�ZN�՚��$m��7+���vmY��Z�A�Z���9��K�N;ۖI�	�ޗ���̌�J�J1h8ki��5��������$�c����c�B�鄞ʬ��5���l%;�3I[2Ԣ�E���`"ٚ2B�����v�-��	mK��Kł�(`�z�����%i�Ny��g��#�w����Ƙ��mB/ux7v�$mݑ�\<a>S�hq]��ȫ�bJ�:�C��p �ꗤ��&/GQ�$�{��VQ:���L8<L�!�嚴ˎ�N|:�[�h.�����],1Ś�,N)�K�k����<�-�Eʘ���˛;x(ZE^|U�J��S��j���BȌ���qʋ�.���$m�SژD�i�?�V��¡zK9/,���|Is�Fm#���)y�����s�:%)]�:R���i���o�}��qWّ6򷘟��FwPs���X�!�I� ��0���IM�|b7JȮ�̭�AK���gQ%���ڵ��ٲ!����_1��h"��K[�[�D�c��h�:u���
}�}�f�I��F*��VE�rSw���8,qig����$<zJ�b�+/���f?��1(5�Tmq�K����?���	!���      �      x�Ž�rG�-�����^��ɨ�g�<(h[��-K}$�{�ӎ��e(�*@4����a�8�/9sfV���$p�Y��"�ʚ�1oc>{���7ͳo^6�_t�ti��טΗi��_�_��|56�<{�����_� ���I�'B�L�t�d�1��(ģ���OOϾ��G����{�6��ej�Rӭ��Ej.����_�E/~y�|��k�$-'-mZ�Ǽ=��R��G+���9����%6�L�w�8��)��"]_��bL��������}�ݛg/_�W�m��7����oޅMׯ�p��hOS�o�&X����DpƈQ1iYV�-��~o��gg�_���S��כ.7;��Ϸ	/�[J�>�G�"��գn��ǒ�-+j޿e�I	�	�����Sf�$��,��6�Yn-K"�5#�IC���HEL"�l>"��f�V�y��=�[��h���/�!hk1�'��]�#!�Ckږ�����GJ?�H���V��'�)޳z��)�V��oY�6F#5\�4Q�
KGh2Ag#��8����^��D%A_Z�up�����G:�����6뻟^�|��x��iC��g��������ʏ?oѴ�1���9m�P-���3���O�D���6D]+�9����{�h���`��p�����m�p�U��x�ݜ6ߦ�~�nsR��z��������r��Ԣ�s��y7,�G�����b~�E�/������|������4qH�� �5���,��KЯ���v��~X�4�ƭ�������t�\&�.��%��+����S��v�5p9|3�ܹզ�������\�a�/���6�O ձ�H�oZ�7Wp'�޵�\��]��� ���~�m���ոI|.�Co{����΢₵�eJxpL���s0ƆZ���4�@�2���ӻ�9_�UHp$�rH�>��cA�)�����^��\�M�8m�c*���A�.ңG#</wv��זG,��j,W5��]�y��GQ<�n*��i��.��4��7Wɽ���*\q���|p����O�1��h�"<g�����K)�#��[?Q������G<�1-r�]�c�iEt����zH�]�W���<�0��_�ݑo��Ʒݰi��vp[P��X�7��A�&�/v�<�����:�%� <* 0��t4)SѦ�H��k{�A�z�//N��N�_}ӼN�Y>)�}{t�������ʖ���`�����Z�T��u��_��s4��;���y�١	l�n=�4��ޡ��Q_�Il6�U�c��գG`z�M1��q� '���*�-�y������"��z�E��B3�~�Fw�u����eB�6Wn��1�j|�K��.�ƻKeJ�s�-i��,#�	.�|x����=��-(�8Y<P˼��xz��ߎ�6���]��T��j �w���6��9P�K�ܥ�o&��W�O�������W�_d;�'w��ϻ�\�K��|��u�l�Sfp����������nh޺eJ��g[p�c��n�{x�ͦ�Ӝ�̉�D
!$�8���\K}��3,f�!���t��w�]ߤ� ��Vż���Lp�z�Z��� ���Df�H�T�=�֝۽@��O�@ժ�(�(�p������
,��W�>�x�w�j�H�-%BSK��y��\����)%�(sl~ݎ���S������w N����Mb���h�Q�@����+�z;ĢO��z�к��ꯏnsn*��)�9�#w�"%1� �ڻ�Xy�[�»�����}?����3V�t�7� �+�7y�8~@��V�H��*Vt����B���;�+�XK Tp�ꘖQ"���rC{ϰ_� ���� |���=�T;���wy��l; H@���ϯ�r �+�;L��K���@�
�����+W���n���	�b"�&E�����7�ՔB����e�(߃T�� �4� ˞����g�C�p8�d���A��o� j�aX�WaH��bAKܕ*|:���^��E��h����g��v�]��xU���Yv ����6g�}>m.S�We���ap��RO#D\܂��6n(<����ٜ���o=��|���\���,��	���6yAr�6����nT�xV�iZs�/��'ۂ����q�4;(�\�`>� q�Ӛ��U%��:X�k�
�N8O��߅��ڸnqRp��������6� ��m��L���j���VE�'s1-�J3v%��p����▗+�g��/��j�Ra�[�!�IqR:���[p*#��P6�`�b��L��3��8� �o�_Ֆ+dM����cL(� �%A���(�<U��9��^���//Ξ7�z��yC�._��c.O�2�%-%Mb`nH����@�yH�g!ں��X�tܮ���	Pa��y�dl�6՘E�]�X����~�FA�D�{�ּDD�:?�l%�E�	G�3�%��E���.�4��AtU�X.�+�.�b�!\rK���T��L�~�c0P�ܡ���o��7����l�!_�e�®�.��d��*o!���x����ak>hR�/y��ɀ`�T���>�e&�����(��	��|���+��������z��ً���.M���3�LD����˅�!bR�~�r��M~�{��o5cJ�2Hو��I�ݢ[��~�Q�]�!͉�����-����>s���_ƃۡTR�u�;<R�~���"��.A*�8�Ԕ�m��V"��L��>�H��lx����G,����]� Kn��M�*/�v���x�>�^�k�����+	�+@EC* ���׿M{���"<��4�� 		�beE��r0�<�O����Of�x�*����GI���/�~?��f��cy�����Є��6�Mt?k��m���x��`�������r֮|�O��ɽ=Ȣ'm3���x�8�S�Ǩ����p�kn<��ߥ`6g�$�ὓ��4� bˁK�\���S�)�����<����e�DI9O�r��`��"��5�ͷW��v.�"O��Kw����K��Y� 00�[�*%�]����.j,��4�]F�)�5���D+��L��p�V�9=�ذ �f��2����$[]$G��\w̖�b&�����廗�j�~��ٷ��% �@>,���bz�_���x��&�v��rq��<F���t�p�*�d8om|8�SyU~��o�k�dv�p�9��ZB��ɵF�ӱҕwP�9�V�l���<Z�J F� NK#�C��>���|;C���Y��G�����-ر��t��:���=-w�R+l[��f�����s�� �øg�aޭ�P�{�M)��RY��eW
�_,3}�Liνb�h� �k���!1��Y�y��m��#q��%�b�ȅ�77m&V�I�E<X��y8���j��=b��~XNeH��*�a����6U)��ޡL�6MDc7�Кg�9��!����ε^L��q��
���m�T���?��a���)�j�`���\,�.pL����C ی��r�y9P���ɜ�^ �Ws�����-<�������~�� ��zTKr�&�d1������֚�@P9��I�u�$l�m�e$�J��b<�p�9�����*=�1�y��ok���Iߓ)>ċ sV���E<4.�m�۫i4 X�������s�}��?�J��eFk4vxa<��x\}M�Ύ/+�ή�ɹf����٭b�3�yQfx ��� �C�X�~��k��+�A��*�-�v��ڟ7�/�3�vk�q�F�&`��00��0E��Jai�;���3�����S�)b�\%c<%9�_ByA7��V(�F�p9@6A���­��� �$���Zq�U����0Ϻ̨�p&�ã�"#�J�4���x�V��W �J �V�L�A��:O�ɍW�<t���H�r-�T�
,?�܁/����j�������*m�7XQZԺ��q1Ճn�U�bm;b��Ŷ8��d��Z    �Jp"��{���
��;V]����m@�E6��d<a�q
A���|���/�!J>{���o����;l����ߟ�o��r�Z	�?�HY�t��W�XxJ�&,��p$G�5�}���җn�@��Z����^	]N�곊=��1[������M7^')��>�U4]WZ�!0���9�+�t(c�S�������CL�:L7>(	v6�5�߼z��M�ϧ/��꤉�����\������n�`�޹���@�z��A8q�O���sU����e�65 ���p��[�!lI�6�����^|A>�V�%��a
�#� *@M4|����)uk��3������~x���f�oHq��Aρf��4�1^�|zi�޾Vw�z���7��ų����/~x�껧ؤ�S���b�j���Z������?ܩ�h��*�y��ya]����%D�pP����c���y�c�)޾�@>�s
��0Ǣ6�K8X'�y�.	1|��~��S	fiϸ[��$�3���e]��'͋���T���֩�/��7�>}`�8�`�����x	�>��( �ّ���Sum�o�J�g�ɟ��+Dǉ���=�SC��-�<c�~m��c\���� ���R��U�-��N���:@�LHm���t"�+E�T)q��U�l��n
�o����k�Y1k5Q�A�I�`��̔�枑Ї��݅�`j�@�7�o`�c�����%��g��1��p����?���'��6��2nh�Iǌ���@c�>r��<p����E��{�{���|�v�cǙ�H�LL�.id�]��6i�i�B�A��G�1	b���s-9��ؚ���M;F�x��gQR%|�ݐ�R06&�$7=�ʛ��-&=�g8�;[bX�$�4�{�豆�s5��,խ1s�*�\b��D�6%q%���s9�t�M�/Lvžt��b�U�F��t����/�"��D%�����Ʉ�:�{�I.�I���G��E��1�~R����PE�畊V���4N�J���λ�͵_�ty	,ߺ����es]�M��i�b�\U; :�(�f��Q?K�U~v J\������vNs ��@r���i4K�+� �lmdG*�I1������:0C����(�30F�����%���1>��}V���k���{�m �.OO�gSE�c�nW`�a��� �-����s'�5 -��!�B�\k'�P2�}F�D/!B`�52�ݑ2�w��	���O
�~�;��< �K@�q|�2�U�� �P���&������xWc� �Ɍ�V�p�0˨	ལ=R����\���j��B��'7��K_��S��ՄE?����Gp�TJݲt�R�yLm��|��K� G'��Df.�ْ�TK69�6�c���I��1�*�ж�t�B��q��p�J9���,/�JegT,f���&s�zu�
�ms�}��j��y|[�oܮ� 4�󫾰���&Qʆ��`!��D�J���/6P�pR��g�WH�P��H!�̴��ԻSZO�G7�K���zŪBV��7E��y�
�kx�x1�.�g���-�p�P�%\J��G���E��ֱ@L�V�dZފ!4F����-*�{�8c�XaJ.N�q!lGl�~���8�M-���⤠�#�߰�-H@������V�.�xLTrz�y�k��g�������:,K�b��!S�W��4^���\֚	Vɇ���=��LS=��u�����~(���/�x��gVǷ��G)�C$���u%�X���	'��B���I U��t{����{N���Dq�"�.%=::I�6�ˌ�<$}�z�]�of��I�͓f7I]��9d��݀��]x�#R��h����N엹�!�>b����A`�uBѐ�vxı�,��#4�!J.9u����S}23 �i�ʥ~yQ��!\T�d:X���Eu��%�ߥϧy�4��JJ�s���[�d�&���c��\����&��� �<��W x���Y��=T=��O$ʤ�%��En5��8��H��L7�y�(}�|f�m�qF�Iin2�T�_R'sR���K0���� �ZqG����p�|9L�e���%�9jaBF&GT�q�Pg�Y�m�1��
�|{�Hk��]��T�)�ƚG�i�}��Q#i4	��==Ji��(E�� �0��o�I��r�f���H�Q��9� /�l=�zܡ��H��U�J&���	t�c�狳����m8�p�D�*�Z�����53{X��[G��N�0�gY*�~<C�o�=��u����={��X'�S�=a)ק�Ż�r0�U��H���,�n��=mΖ}ŔK�����?}Ք��:��:�mc��+R�Y�p�P�S'��B�BN�]�G�
�����F+DҚh��z�t�â�uJ{'�����~8��BmZ�R�j7�䇽�C�]�/�w+�t�H�5N�A^��tS֢A�X:�:�f*�J`Z��ȩ�%�gyʜi��<�%�M,6.�ٚx$V��=�7��^�~6���p�����/oi���ZH��;�E�e$���ґ�]�3� �����I����d"��By��i���p����n�'8����˟�?����S�q��ϐM�"K:��ƴJ��_��[� 2$I���Q9z���)�����~��Yz'`֖`���*������,�����*v%����<�A�6���йL��|�d�6�sy��T�7`�
� ԙX��L����|�#b�y�pH/`� �N�]�(P;s�X+�����$�����釳7?=ݑ%����KT�ĚAo�}5����oWO�V�g@���s�0�} tHu"�rLD)�臒
~�}�N�uc��<5	��Y�x<�8�'RG���(LՅ�-�JOv}�����~Ғ��~nS9u�3-��m1��+�Lc�nk8^�h���Zxgd�ڸ��ŇZ��(E���NdOl����G���ڇ��>�z�w�Ic��R8b���uF �IG��9iv�l������3��*2oB��1S4}t5���I�F[ �.��̄� g �*3c��ؑxn��jO��
���ٚ*�<��)%��Un���s0�s�p�%�DsA�U�&�w��=���z�RB�1��_lsm�����C��3�?V-HbP�)X�6�=�g����z��[�(u���I A)a�O��l�V�q���;�۔y�6�@,�E � �\��чGq�C��$��'G|����A�"+-ґ�'n�ovߪ6�+�̊�� �j�m\����#U�f�1h��6ـ�7�������ژt�ٙ����<��(��9��ƕ\W�C�j=���s�� r,f.��3jm,N=i�V�%��2}s�G�4����2C�l�"�2j���|�Rݭ5dG��.i3��\T����v���`�-Ӳ����%�(�X��k����Kb�[���L`+����0�3Q�-��v�i2i���s�_�	��#�L�9�	���`����h�=?��u�}6E��{d`�V�i�1���6��]��)qU��]KWMS��w�:�[|.��������"E��`h�%:��|`��{��HY'4.ܲz��[,g�*A��l3�����c�9t������:߃�m���*���G#D�����ږxC-��)�<�`y'Q��W�{�u��Ղ-� Nު1�'�AQ�={�}%�s#�r<i�����c�b�ͱS֤L8� ��a��:8�k�Ra�!.	��$��Y[~���������v������F��({�"�i�κ��J�i�#g�&�61m,�F�L ���\*��}H�g��S\�^�+�3n.K��糰J&��͍y���t~�`;9��B�����ײ�Oc�H���<No����\ˌ��Qؠ�P�kT�Fk%\�R��rAsC�Z	�*a��.���`7��Z��ұ~b	��ִ1d^6�	90E��������@~�J�u�    ��R�:D�R��RF�B����V`�M�a�EűF��hs࡞ɉ62SX-qj�xb r��!�ڪ#U��j����S��o5�T��YK��&��$��yV�u�c�ռ����x������L�[��]�u��De��*I� }خP>k�� G�Vy�7'p67�*ÈJ-�̜�G�c��룮�<��2��N���R��"(�OMY���$�D桝���.w�޴�b����8���2\p�ζ�_L���:ELHuQ�n��o=��~�P͗�R�Za�/J0�D��Kjb���g[���q�ߦ�D�J���@,�����w��[[% U>�8�R]�N��MzM��B3��� YZ��<R�XkÃ��)��&�J�_�'¯����O�����n����&�ޜܐ���s\ԝ%.��n���42���<lѽγKw�DJ��
����B�K�ҁ(o�K����`?֖wp�Q{�Z�H�<Ì*�,a%��� �SP	F�>�^u���7נTv���ʔ[�"��@�ʦU?�Ͼ��F��d'b��ܝKR;��ƀ�k)����L�h�����oσ������aץ6�*j��V�����=��rH�ʪ�B��ȍ��-NP�T�2S�<`��ӣ�,�c9B��s����@���%ڂ�gI��c����*�O��8��op�z�|�2���nn@��Ya��½Qvi��^��	-��kQƸ�fpúp#eg�5�I��}��Ε�OS��v39��r��t!��e6���~�0;e�J�M��Ӫ�+��fR8佃�@��[.�u�n�����-rc_;�n���~y�(㆗�܆;|������t��*�w�w-���!�`�*��D"*�H�_��{.�ޱ7�wqO�R��
��˔�o5��yf9%��#@x梲�'9P��-��E�yPF��o��yE��{�~z�3r
>��]�i^<��7�:
��Q��-=�B����&�0w���`fN��R뢍�ԏ���(>�1X�nw]h�z �s�ܹ����^w^�-пua���g'�K��Z�ѹ�@��
�`�ƹIyݲ�X
�U�z�f�jN�i@n�bZ� ^�W��}V޴R34������O����̓�:V��'���ϴ��>��G��� DR �^$�5�v�g:�8��$@��I\v��D~ɭ��梇@�ag�t�S.G��:*��Ii�6��f��f֤
ZR4�n0�V*���?+���ؕ����KN鷐�s�9�Sr���c�h�+[��}���L�kh\��e8q�$"[.ST)�|$�����#˷�z\��q�=�+dc��k����\�U&l0���̵�<�Z�����=���'��i~��檹*����5:��(��g*��d)i!��@�X$MNY)��Os�6�[���Ly��������}*�T/�����:䡘���[w��xz=�j�m�,�2�9/�}H�����'�s�uQрǄ� X�$�E�b)}�-k3;Vf���6��P4�ƴ�k7�@bBl����O��'� Υ^Qs��xpo���w��H�k6�@%�����ʩ˅���F��
A"��M]��C�_�K�")>�ab���@#"��0-M�s������-f��R0���6�[��灔y�r��덻&�:b����Ƌ�3�2xȈ�7%�V�q�t9@���<�����@8k�c$(O�d��bῃ`Oy�
7�����u�R8�VN'�Ў����W�ŏnu�g������ 6Jd`�y���G���Z:����{�J��J���ut�(�����fn�w�b�D�U�p�H��xHK�@Ü�� �
�R)�%�	�D�(��JulM�Hw�xl����7����B�]��W��-FT2o�܎hOJK:k7N�)�؂]���:�;n\�,�8Y�p[��2�/�-���&��s$����6�\G�N�ZJ�J4����A�)��	�V��u�CW��h0�,�5��3c�{���rwI5V�<2E\,\�<@`n�`=AD��2��>��l��9�9���]]��׫�J���R��[�O����f�j>�^�v��eYr\p�L�D�L���Y/��Y�c���rj|_����a��fZ��լ��;��*�7�����}�Y�Zc'�V�j�(�D�L*P#�6G�&�^1gBE���zꪝ���	y EܼXcL%��풂X��ma_n��Z�u7e��D��kz���1	︊n�MlsQ3S�Ɏ��r]�i��`g�����[8}�Z����M@~�P�g�X3�w�)J*0��p�M�j�1�w5���O��..$��UҒd
�"|
��<
V1ZF���B�w�v�\��j��m�
�AW����/�aR���_>�l|T!I���G� �L��"8��{>��4�V���b�������C���IsV�\m��O��W�*.�*�r7^N�ns�(���1D��di�U1�p�d�}���qҎ��*,�5+?Z���at7R	�jja��U(YcS�y�J�U�!3	N+z��ɭ&�FK����6��?\t6w�����O�˖�Jx2�&ޕ��ݭv,C�'��81~A~�J6��xt���[l*LS� ��v����?�w�/>|���l�����7Z�s���h�mv��w*5/��A嵯Dq����&R�ݘf��&*�1M��0�m���rjײ:�n�
sH���,�o���P@L�4W$:!6A�#-o����w�>�%��zS�ɫ\KZ�q�m��g2�|ڪ����/��%fp2�1X��G�$	��5�ș��y�~�����:�a-WYi����gJ�_Q�>H#����@�?"3��B�4Op��7㯧5մ�ٺ�0Bؿ)~b�,8��S[�ƙ3�l�y��D]����a��X�pć2ҏM��y�"Y&�8R��%H�C:���K���07�6,�U��2���],���c ��܂~�������������1kM�����J␮3NC�(��7���ǖ�/��g_s@�q���.[_'ʆ�"c��n�׺��T91�αE"�A�Yخ�p��]&%b���'ڢw�Jl5-�sˉ�f�S�A�� ��v�ADRM�~��4(T{X0�xyZf�e;۴鼛C�~�e��{�����	���!��&%9��{V�-��;¼N�Y�x8R��]$Zߴ�;FVL�~�eL�>`�f%�f�\�+:�q��z`���dE3I�5G�?db�8�.]3���9�$g������P&�P�.�� �����ƞ��r��W a�䙦�N�����t2�Jă����0#��1��'�]ƥ@�D��Ȼ!R��%�Q�'�kO�F��_�v��F)��I��)'Ib�P�YGc,R}���
-hΉh�k	 *�	g�VabW�'ڮ�{�����6ϟ~��WO��Ξ?��.�z�=f�i�)��9aS����XxF�͠i�.$��l�d����?�g�B!��h��������Z n����kd��w�г.zl�o�n���>��� %�g�p�L.4�e�bѭ��]ɾ.+���3d��YuKL�"I��hf�Z����5��{��i�τ/�݌�.
�Kq)^���	l(�ݛ_���=�ē{N�m�r?�l�Pi����6���k���Į%E�򇧯_�|����/?�����u<[!d&�[���%F��A�R&?Rt����a���b�Muc*{�0e~��L�:��Į$I�$�'N�g�@��( Fl��#��'�ͧ�|6��aA�#6lܼ���)�Ѿ���P���%`虭��e[����PeS��������dJ)�_�&�v�Ǳy���K�� f���7�~��ͣG���� ��"I�����l��A!��b�SJ)_x�T�VH��3!�=�k��"��%�2iD'Yݳo�Sȹ�p+e���o@
!X�e�E�����hy�
�=�mX+�.ف+P�J{�r���7��������������R���K�q=i�.5���S��j�� �|�J�dA����+�r�\p��Htk��k�6e�*j�`9!j����k_;�ѻ��@sZ��q� u+V�ȸ4a�
��    .	,�#��K��%Q��s�r���g��W`{l�6�x�X�{Q���%��e��sn�E�y���~�pt�u�žZ��R��������q�t�Vn�T�RJ��M�oSZO�a�@�y��?�
���U�BUOs�qe����0� i5W5_K�/?���)XN��6�x�^��'Ń��Hܘ�V⹱���߂a�3��P�1=�4/���Ǉ�cD�攈��*A�&^��P��R:Ey,B�������_>�C�+L7�!hH�z���4�iY!E	�I+���ڹ�gnw��1u�v�B�E���G����fї"�~���1� ���V���a��J:�L�ឭ�m=o��0�ܗS������1�9�#@���5���x��RK�4��>>��6������-@����v'ŐG�T��%A��=W,
bP�dYs ���㛏,H�� ���Nc �Cv� p�^���ќFkZ�"�m��5��YtPD�ȒT�����ڱ��?WmwjQ�!e*vN�^v���%�_�]�ӆ���P��*Ň���G�/>�u��ޛ������D}���8`w5�Kx�C�0�D�!&�+w�X���+\��w']4��E�r*����a��O R3
�Lp[GJ��E'���s�uL�2Y�s����[,p�ftWue���]$��ѴS���(]R�ƃ�ܛV}�)��[��J?6����#{]aF�Ħ�ڄ_S�q�����j;��Z3�K����=<�Tkl������*Y�Y�N �  @�����%�:߳~l��� �|�ޚ9��D0���	��%Z�����j6���f�O8ٺ�b>�j,vC�.Mr�+�U����zPr�eZ#Չ���r�c�\7�g�a��[HF�O�L�P>u��u�"K����y��a��7b����/*un8$�
8`�Q�؂{��`�.�A��Φ;�8�{l�2wN��S⣉�����I��sOl�e#��Dot���H��I�=��8��A8�6h���4���y��NVV��4L<-�m�@��}�H�+|G�2�����$鑩 >j���`z@}���0��4[�Nb"Ԗy0���cM��E�.*X�FTV�Sy�N������B���r	�I���D�-بg�q��p���`J��I���S���vѬ;ڮ��C�Tѩ�"/b�Z�|�B@-���5�}@�0��Tk���I�Z�O ��*���U��+=\�`�
{6uQv���Wu.l��`���$ڴ���A���4׮�$Q܉�|&� �"��9�xȭ�`���,\:��\ޕx�B�u���� �P���%<�O(�8}]��
�/D��\��Go���N��!.Q�` =f���bۺc������]~��M�q1���牼}�ٱ��i^b���=���O7xA�ٛ��t��bH	<ͱ��Ғ4����#ުS�
�:���Ht%�W�	��4w"�5K��zhL5�1P�B�M����<�_�a�+\	/�J�)}��p�{�r?z��.{&$�cjV#�$��3��\Ǉ���	i��c7Z� �q�LtV��h:s�F	O&�q���Zb��\�6�{nV�։k@zͥX�&�2�4s"L��;˃pm�'q��Y�Ti�	�p�X)�Ǵx������ű�p�p\�
h/�t���������-�r ��-Bpxo�!�W௼\�hp�HC�wl��˴�8*]���nФw}}�o�	�ׯ,��W���&�bsd���\��h��i!.T�H�)z@ʀ��0��ڪV=Xo��{���6㢿�م�W�{^�����V��f؞�#�S�*s!�D�S7���.��=�(�7�����͔8	F�XN��Z�|��\
�J*S��7n.�,�Ԃ3E��D˖�7���������b���럱��ۧ�-�'E�S�N��쇙W/���p�^Dʡ����;�~~�1��s�}7q���릍xe�D��xd��(J5��R7[���*��8
2�e�b�ۋ~ӟn}Q��#(�D������o���4y�x2MckyY�L���cy1�	|�r-��X��$����f�Ѱ�~�5aH�m�|�*��Sg�@��F9T^�d0��*&�GJ�}���H���H��N��Ds��Wh����ӌ��1N�A�Hp��7K�#��W���[宪��ؚkΠ�2@�\$����s�8[Ĺ(�*���Zy���C�B38ۏ��X&�	�P˄;Rt���%#_�Ũ5H�z�� ��H �d��:���[TGT��.P���`��Z�l+cr���Z�rk��
���J�[��v(�����#+�U�L�=�V�L)����;�8q��.��j�[�^��u(I��r/��<��C���NRQ�e�"���c(��.i�ڟp��.E"��V 8�,ܳm�H[�Q��s��T���Z�L,�]�TlƏ�l񮛱��(w�<;ֱ�)�8^����	�A���Pw������
�7�Q#ڪ\�z��-RH�?`�Y� ���K�2p�i�h��)�����E��Wv~|�m�J����Bi�]��)����H1��hops��ߘ�GQ���4����I�qb�)����W�N����y��y*�5�vᶵe{��ɕU3S��)�,�L�Z	�N��4_���-�ݼ�wUG��ֿ R�P+J;a7�����̳%=�伫�zm,.�4#�M���s>٧���0/T����#p;@W
�c��v�!a��0Eim��u�&͉ �N\!R4��N�=[�#�s_�<�}��!����Ɗ�5L��<�6y�)�Vk��M�E��7�D�p�ғ6� �E��O�'��|���ُO�=-��O�^=�w���O_�K?u��>��1��V0n臶"���` l��,�D����x��*�_y����Hʱ�4�%q�SZt
��Y'�����9�+���JM�ͻ�~3�4��Y׉���dduf��E�독N!���&��G"겭���=�܆�i���Og�J��jy��*����h~�n��u	3���!̯��R�~�!ţJ��1�d� FyM�`IX��>Vn�k�G�p<���b�ck8���Q��f`�pE��ɴ�i*��������p��B�����L��	$�C9�ޑ�pYii�Y��sa�1R<���/rQ=z��nqb)�� ������l!�.�ȵ7➅����� /����n���Kn����qp���˔�5!J�͎��� �I�b��p@Z�Qa��b"�Ō��c�?�0�nwb��k���˶���+kr�V�V�c��o�?�c W�u9s���J������-!��lӼ�q�0}��������[#X��2�4��[�u��{����_�W�W��J�m&&�_	sr�a�@7��m-��`����L����l.>?��%�D!�Ȇ[A� �X87�i�1 q��1|�g��W���JIbhTȩI�I�T<�N]����8�K��ĜNF�0H��wQ#%�i�3��Ӷ���n���?���ʄ2a=3��$7�Q�0X\� pO�p��K�1�'��F������u�9�ڏ���h�03r �IN��e�ZlѦZv�؋�2-<�>�g�������f�!��kNX(G5
��䎶h�.:47�f��nh?�i�����7�z�1�'͛�M;�����R4.�*�j��/4-ɫ'+eP�P4ķ��O��>��`o�|����E��In1�3�L��b]h0�ps؅�y�D�m�X:p����[^�v�;��׼'ｰ��K�7G�ڂ���0��~<*i��0����h��T}l��0ߖ���
ċ 1�x�
J�k)Q�g9V;��r�Ļ��w2>�$>e��Ua F_��[.�v�Ԧ�T���R����[i�<V��Щ/	?�r��j�BLG@Eԃ�ˮ0�`�0����~0�=y����	f�R'+����
]�r�B�3��/&q ��T�������7���d ��;$�+����lj�P�'����c�1@$�� :  ��)���s��I��u@w�kN��aF|S]UmpE㊭�9�h�u*���G<��i����M�E��\A�7Nz����~0&]�����T,�D�,#��f{~^���=��R(��s1��P��ı'�0�-��|��7����ECֹ�ïw�`��%c$�ñ���h��a�,)��jF�)�&�0	�|5�!�u9Zs��m���y�nY����j?.;,���E���P��X�1>צ�&���� �<W׳솷eo�u5:�u���qXv;@�#e������@\�\���{�t�6�������A�%3A)XG���=��[�%I)��k�:���ʷ
�p�`r`#��,��� ��dT�	�� x�΂��G/�����¿*��Ӯ�]JJn�����r!O[���؍�?���=c����-r����U�_��(�m6�`v0���8�tn�K�U�l&?6�|�+�6{�)��,L}�^
C�=�։c�ḋbL���3���ڜG�86�]f�u����#�ʞ��<m�&��!�;��`c
�[����"��a�>(/K�w���[��sr��[��Rz���Wᢤh�ϻo����_J�XF��ݮ&c�7�'�*8J����h�Nw���@(<����*Rp� "��}� Wp���v7-�~�W:�'�u�q��P���ü�|���$��i�z��i�C��X�1����G�����%i6�&�zΈ�L�u~�] ���:��㲬qH��T����7rv�2��l���ˀ������ܘ�<I����ua�Qec�������ƫ�@�0�9g$�
�����ն-��(��H��Y��˫��PY��s��`eD`ژU�A�P�rW$a^���^��䈴�Q�I��a�#�$*4@Bi ;��C��|���0vֽ�f��F����Xj��++��eҬ��7j�Ѵ����u�'��/����!��eqn���2At��L��B��5힟24���W����\8SΥ�=�,�D��sG�3<����K}Ϯ�F�<��m�_��6	. �H����1�V#x�FqI凓N���E�l      �   �  x�͕M��V���+��42G_�H,�)4I��|�@
����踻�r7��Ȳ�H���wozy|~���?ڧ�}{�����e��y~�����O޾�|sm���Z��@z/���T̘5-�7��OO]1���r�D
�!�%�N�s�)�4n��u�]W��HDlA�j��f��2D�F���e~����Z�j@ڣ�͊r��5�JNS&x)Rՠi��ʘ�}ٿ��pf��i<@Z0�+nK�(8V��\�V�j^�%)�l(Z��8�#8"
Ծ2���4S��s/�h'�Ѷ$�O���J�0�����נ��� �%�'	��ڻ��'��&��,U����q�a༳n�-�����n��ƌq�*��`G��kÜ�C\��x4AV`j�PL����āx���%��,k�W(!��kuZ��Q]+�'�l���p����Q�4�t�B^q�KJ��nf)���La4LPӊ�/:N1�mL������%���gq�E�$\6��<v��ܥ3�(mY�B+�V$��J���F���ҍ��	7T�.��Lj������p �ܸg1�=q�4c���cV#_�Y�
���[���AbҖ
J9�C<õ&�Y#��C����ŭ����8Ăfl�I􍑡Z,�أ�x�5�+gx[�y����V�pX�}1G����h�L�G�vR��8���e%0kѭ�=�a����Z!�C�v‾���[�ߜ�a�:
��0�1����W�Fg]<<�	|�2      �   �	  x��X]o��}ϯ���THJ�$��Py�[�6(�bȹ��"9\iU[�׾�KO�����;���"�����;�{��7�땘/VKQ�I�ӾM�$+�M���n���t�I��'��� ����x�Drd��=�������ͮ��|��^�����z�x1��WW�/�����jC"5eF5�)���s��XײT��
��.{"�yNJ�t�Um2�V�R�Vd�)�ҷT[�lp���K��=Q��ؑ�u�����4��n )�+aSYg���&Ke�/o��1��	�`֭R+<���VF�R��<�L�V�ր��\�����ZZ��T��e����R��d���?��Li��uKg���b.v�xo�rMu��ƴ�M�'��ʽ��,��x�6B7���o�4�o�ł��IMr��-����_�uOS<uᗴ@ޥ����YO�U�j��Rb�0q�S��^��9n�Y���k��9���w���o�[%�=����p֩'
����<~aHG�8�0��{�P�S��C�)o]���j�}�>�� 6m��Q�I�n6���#�ٕ�ᅟ�_����WW���#��0�1\�A8ǃ����b�߿9��X�G*NA��ě�&�K�0��q0�Gwog�;=�����)K*H2�F^2���T�7IF�K�A��QvO�ٟ@ٷ������|�^���~��枦7M��1e���%�<S�)���e�D[��n��Z3H���¶e_�1ط�JdY�L�*��&խI;��ɍC?�2��޽��4o���kV7��$�>o����1VW�-ٍ����xݴG�2MuzP EXQ�;�2-�H)(���Timv�Qv )a�I�=h�����X?v���^"-@�i�A}'X]�(�Y!b�}}�=M7DN9�i.�
Ͼ�/��?�|8��oR u/d�Bǹc�p��Ch�nc���g̽IK܆�Qn��iB_����pt1���G�:��h���`��kF�̼`�8
����s�J��W^4�Co�zr4I�$���d2�avRa9���1}3�^��-V��b���C��K*��!�i�*Ev{(5R��ʣ�6����/�v�:�� N�1[˵�0��Q�T_�0���%K�$xbZ�\A�A������͖ " �m.�3]T�uR=�(��+�a�X>y(�(��0��vcv]�F�Q~q�+ #B�����Y�u|c���!����
���ܹ"���-���Iq%��*��٠F>&+�]��T��e�/LM_���o�N ��0��qt�_ض0�)����*�I�yq�#Ij8	�o����rs�\^��o���(?;�z9_|�!��Wd���}X�ܘ�J���-�%����6�<8�cm������e�ڞ�ʻ�)kM-5�^�08�ˣ��@R�΂�����c�G��#(x <l��+�*C�Zb!�H��u�ps���BD�g�ve_+���SF �"�%��a>=�����;��y�L�7��Ĵ��V��(�@yVSަ�&�=�tF>������St��q�d�X%�0d�J�l�H�JM��7D��c�
܊�����\Q[�����Rػ�Oa�:���R�&�Y�K2�b���z�7�� f�{��NV� ًJV�����}1��5�\8���,��@�� b���#I�&�˿К$9��A���P��XP�u�1$@�"A2�����p�p�-�Hg��oRS`z�:���c��`x��A�I��,��N`��	��e��B��b�.��.���st���^r��\.8:�(70��Lp�m畹���JJ�o�ٮ�"e֤`���h^�#{�g_�/H���il\�ڴ��Y+�"t6?�����^r�3��P"�8c �q�������?����VL����K�;(Fe_����Boj��%e�S��Mv)>���t�a	�~=��r�?ǣ[��#|�/m���w�e����p.y��®���S��4�����R�]|B��v�}.�
}�b�������G	:G�S��G�(KS�0�/(w�B���8��X}C�F������K��'�s�nv�k'�w����S���^޺�[�YJ��0#��L���i�8�a�	����Siv�Y�P�w]��P�%qtD�X������o[�.Ϲf^�)@uw��	�CÜn��uq(l��-sT�	�*�[!!=|�鴀%���M��b��
�{�;I-��;L����q�:s�?�^����~�S"�+(��sN��:Xd�WբM@Y,�;�;ҏ+���p2*M�NI�I2�8���)y5(ʆ;��ĽstM�p~y�z� �܉�;�p	๷U��H�\t�i>I%��sJ%�;�q~^w'u�Da8��3�[��CKW5
k�,����1���>D��ă��T��a���8�� ��G��x�%� ���4z ]O��:f��      �   }  x����n�0���� ��vb'Wel����ڍ���vZ�4��tZ�x^�'�bBE�����s���dr1;����b~	�MY;�l뾃����d�]C���U�u�pq3�ұ�R1.��A�B�LG��I���H��Y鴳Fr��Z�Rn=�="�Nk����F��X̘պb��3&�̧(��Jg*#'��������z<?>�~{4�.�bgL�r���.Qdd�ʘr9��Z��䂹2��N2��\~����Ɠ�58m��Ec�
�6tt�k;�S\�zcw�~�Ì��$ç��pV%B�16�K}�xXyl���V���[�5�c�Y,I�`㠊�7nW�F�)9pY$���B�ju(�L�W�dF{�I�JC��F�1F_�3�9Q8����[�Ml������_s��Ӝb�c����+|��)Y�C�j��Bӷ�B���V���MCH�O�$���V�����]�̓�*))��O'mY	Ǭ�e�%Y&��Ҥʉy�CB�w]�9k-y�#�j��K�_�-HއE����е��,%x��k�xb�1Zס�ϡ��@��3��s�6��#����Hy��H(nG�%:�S���8BjS�_�6+�W"�����H��8      �   &  x���;k�0���
��-��,�N�.��`\h�.�=��?���ײCZJ����ΑJ���u��l����*��v�z{N7���l)��\��Ӯ�����|乓�U_�u>�e���Ɠ]��Ck�l�88W0�BB	戲8`1��/�,z�a�i�d�4�E����Ǻ:Y5�ܱ��æ��_�_�`�z�F4����6�`zp���(�Y��ه���~ӗ��gT)#�M����$R\(��A��������H�T�����(ґ����8z�/��L&��v��     