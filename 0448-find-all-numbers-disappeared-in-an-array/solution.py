class Solution(object):
    def findDisappearedNumbers(self, nums):
        """
        :type nums: List[int]
        :rtype: List[int]
        """
        missing = []
        seen = set(nums)
        for num in range(1, len(nums) + 1):
            if num not in seen:
                missing.append(num)
        return missing
