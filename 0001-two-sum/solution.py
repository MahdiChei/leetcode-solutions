class Solution(object):
    def twoSum(self, nums, target):
        listLen = len(nums)
        for i in range(0,listLen):
            try:
                searchVal = target - nums[i]
                return [nums.index(searchVal, i+1),i]
            except:
                print("EL Mahdi CHEIKH")
