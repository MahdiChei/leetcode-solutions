class Solution(object):
    def findErrorNums(self, nums):
        """
        :type nums: List[int]
        :rtype: List[int]
        """
        seen_array = set()
        duplicate = -1

        for num in nums:
            if num in seen_array:
                duplicate = num
            else:
                seen_array.add(num)

        for i in range(1, len(nums) + 1):
            if i not in seen_array:
                missing = i
                break

        return [duplicate, missing]
