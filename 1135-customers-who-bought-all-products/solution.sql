# Write your MySQL query statement below
select Customer.customer_id
from Customer, Product 
where Customer.product_key = Product.product_key
group by Customer.customer_id
having count(distinct Customer.product_key) = (select count(*) from Product)
