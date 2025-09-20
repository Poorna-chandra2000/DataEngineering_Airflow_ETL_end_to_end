-- This model reads the raw table and creates a cleaned version
with raw as (
    select
        id,
        user_id,
        title,
        body,
        processed_at
    from public.posts_raw
)


select
    id,
    user_id,
    title,
    body,
    processed_at
from raw
where user_id <= 5