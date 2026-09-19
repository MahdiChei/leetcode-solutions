# Write your MySQL query statement below

select Students.student_id, Students.student_name, Subjects.subject_name, count(Examinations.student_id) as 'attended_exams'
from Students
cross join Subjects
left join Examinations on Subjects.subject_name = Examinations.subject_name
and Students.student_id = Examinations.student_id
group by Students.student_id, Students.student_name, Subjects.subject_name
order by Students.student_id, Subjects.subject_name
