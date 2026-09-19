# Write your MySQL query statement below
select emp.name as 'Employee'
from Employee emp, Employee mgr
where emp.managerId = mgr.id
and emp.salary > mgr.salary
