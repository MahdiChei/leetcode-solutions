class Solution:
    def evalRPN(self, tokens: list[str]) -> int:

        temp = []
        for item in tokens:
            match item:
                case "+":
                    num1 = temp.pop()
                    num2 = temp.pop()
                    temp.append(int(num2 + num1))
                case "-":
                    num1 = temp.pop()
                    num2 = temp.pop()
                    temp.append(int(num2 - num1))
                case "*":
                    num1 = temp.pop()
                    num2 = temp.pop()
                    temp.append(int(num2 * num1))
                case "/":
                    num1 = temp.pop()
                    num2 = temp.pop()
                    temp.append(int(num2 / num1))
                case _:
                    temp.append(int(item))
        return temp[0]
