class Solution(object):
    def buildArray(self, target, n):
        """
        :type target: List[int]
        :type n: int
        :rtype: List[str]
        """
        result = []
        numbr = 1
        for i in range(0, len(target)):
            result.append("Push")
            if numbr != target[i]:
                for j in range(numbr, target[i]):
                    if j != target[i]:
                        result.append("Pop")
                        result.append("Push")
                        numbr = j + 1
                    else:
                        result.append("Push")
            numbr += 1
        return result
