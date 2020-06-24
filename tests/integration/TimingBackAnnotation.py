import unittest
import sys
from plumbum import local
import re


#WARNING: this unittest should be run within the integration test folder

class TestTimingBackAnnotation(unittest.TestCase):

    def extractTiming(self,output):

        #patterns for extracting the timing information
        patternVpr = re.compile(r'Final critical path: (?P<time>\S+) ns')
        patternZuma = re.compile(r'Critical path max delay is: (?P<time>\S+) ps')

        #first extract the timing from the output
        timingVprStr = patternVpr.search(output).group('time')
        #findall use the first group here implicitly and return a list of times
        timingZumaStrs =  patternZuma.findall(output)

        #vpr use ns and zuma ps
        timingVpr = float(timingVprStr)*1000
        timingZuma = float(timingZumaStrs[1])

        #return the results
        return (timingVpr,timingZuma)


    def setUp(self):

        #get the path of the compile script
        self.zumaTestDir = local.path(__file__).parent.parent
        self.zumaTestFiles = self.zumaTestDir / "verilog"

        self.zumaDir = self.zumaTestDir.parent

        compilePath = self.zumaDir / "example/compile.sh"
        self.compileScript = local[compilePath]

    def test_combinatorial(self):

        (returnCode,output,stderr) = self.compileScript[
                                            str(self.zumaTestFiles / "simple.v"),
                                            "--config",
                                            str(self.zumaTestFiles / "zuma_config_timing.py")
                                            ].run()

        #first test if the circuits are eqivialent.
        self.assertEqual(returnCode, 0,"Compilation failed: " + output)

        #now check if the timing is the same.
        (timingVpr,timingZuma) = self.extractTiming(output)


        #now check the timing
        #we have sometimes a difference in the lower bits
        self.assertTrue((abs(timingVpr-timingZuma)< 0.1),"Timing differ: zuma: " + str(timingZuma) + "vpr: " +str(timingVpr) + "Output:" + output)

        #run the next test
        (returnCode,output,stderr) = self.compileScript[
                                            str(self.zumaTestFiles / "comb.v"),
                                            "--config",
                                            str(self.zumaTestFiles / "zuma_config_timing.py")
                                            ].run()

        #first test if the circuits are eqivialent.
        self.assertEqual(returnCode, 0,"Compilation failed: " + output)

        #now check if the timing is the same.
        (timingVpr,timingZuma) = self.extractTiming(output)

        #we have sometimes a difference in the lower bits
        self.assertTrue((abs(timingVpr-timingZuma)< 0.1),"Timing differ: zuma: " + str(timingZuma) + "vpr: " +str(timingVpr) + "Output:" + output)


if __name__ == '__main__':
    unittest.main()
