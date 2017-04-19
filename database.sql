create table twitters (
    id serial primary key,
    api_id bigint unique not null,
    screen_name text unique check (screen_name != ''),
    updated_time timestamptz not null default now(),
    followers_updated_time timestamptz,
    leaders_updated_time timestamptz
);

create table twitter_followers (
    leader_id integer not null references twitters,
    follower_id integer not null references twitters,
    added_time timestamptz not null default now(),
    updated_time timestamptz not null default now(),
    unique (leader_id, follower_id)
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
    leader_id integer not null references twitters,
    time timestamptz not null default now(),
    unique (user_id, leader_id)
);
create index on user_follows (user_id, time);

create table user_unfollows (
    user_id integer not null references users,
    leader_id integer not null references twitters,
    time timestamptz not null default now(),
    unique (user_id, leader_id)
);
create index on user_unfollows (user_id, time);
