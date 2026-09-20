class Solution(object):
    def findMaxConsecutiveOnes(self, nums):
        """
        :type nums: List[int]
        :rtype: int
        """
        consic = 0
        max_consic = 0
        for i in range(len(nums)):
            if nums[i] is 1:
                consic = consic + 1
                if max_consic < consic:
                    max_consic = consic
            else:
                consic = 0
        return max_consic
