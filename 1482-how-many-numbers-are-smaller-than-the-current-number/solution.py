class Solution(object):
    def smallerNumbersThanCurrent(self, nums):
        """
        :type nums: List[int]
        :rtype: List[int]
        """
        oupt = []
        for i in nums:
            times = 0
            for j in nums:
                if i > j:
                    times = times + 1
            oupt.append(times)
            
        return oupt
