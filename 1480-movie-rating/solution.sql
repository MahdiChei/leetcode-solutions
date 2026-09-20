# Write your MySQL query statement below
select results
from (
    select Users.name as results
    from Users, MovieRating
    where Users.user_id = MovieRating.user_id
    group by Users.user_id, Users.name
    order by count(*) desc, Users.name asc
    limit 1
) as user_result

union all

select results
from (
    select Movies.title as results
    from Movies, MovieRating
    where Movies.movie_id = MovieRating.movie_id
    and MovieRating.created_at >= '2020-02-01'
    and MovieRating.created_at < '2020-03-01'
    group by Movies.movie_id, Movies.title
    order by avg(MovieRating.rating) desc, Movies.title asc
    limit 1
) as movie_result;
