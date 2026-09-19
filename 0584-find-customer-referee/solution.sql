# Write your MySQL query statement below
select cstm.name from Customer cstm left join Customer ref on cstm.referee_id = ref.id
where cstm.referee_id <> 2 or cstm.referee_id is null
