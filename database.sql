create table twitters (
    id serial primary key,
    twitter_id bigint unique not null,
    screen_name text check (screen_name != ''),
    updated_time timestamptz not null default now()
);

create table twitter_followers (
    twitter_id integer not null references twitters,
    follower_id integer not null references twitters,
    updated_time timestamptz not null default now(),
    unique (twitter_id, follower_id)
);
create index on twitter_followers (follower_id);

create table users (
    id serial primary key,
    twitter_id integer unique not null references twitters,
    access_token text check (access_token != ''),
    access_token_secret text check (access_token_secret != ''),
    updated_time timestamptz not null default now()
);

create table user_mentors (
    user_id integer not null references users,
    mentor_id integer not null references twitters,
    added_time timestamptz not null default now(),
    unique (user_id, mentor_id)
);

create table user_follows (
    user_id integer not null references users,
    followed_id integer not null references twitters,
    followed_time timestamptz not null default now(),
    unfollowed_time timestamptz,
    unique (user_id, followed_id)
);
