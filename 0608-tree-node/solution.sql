# Write your MySQL query statement below
select Tr.id,
case
    when Tr.p_id is null then "Root"
    when ((select count(*) from Tree chld where chld.p_id = Tr.id) = 0) then "Leaf"
    when ((select count(*) from Tree chld where chld.p_id = Tr.id) >= 1) then "Inner"
    when ((select count(*) from Tree chld where chld.p_id = Tr.id) = 0) then "Leaf"
    ELSE "EL Mahdi CHEIKH"
end as  "type"
from Tree Tr


