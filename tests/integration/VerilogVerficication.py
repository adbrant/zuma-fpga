import unittest
import sys
from plumbum import local


class TestVerilogVerificationChain(unittest.TestCase):

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
                                            str(self.zumaTestFiles / "zuma_config_verification_comb.py")
                                            ].run()
        self.assertEqual(returnCode, 0,"Compilation failed: " + output)

        (returnCode,output,stderr) = self.compileScript[
                                            str(self.zumaTestFiles / "comb.v"),
                                            "--config",
                                            str(self.zumaTestFiles / "zuma_config_verification_comb.py")
                                            ].run()
        self.assertEqual(returnCode, 0,"Compilation failed: " + output)

    def test_sequential(self):
        (returnCode,output,stderr) = self.compileScript[
                                        str(self.zumaTestFiles / "sequential.v"),
                                        "--config",
                                        str(self.zumaTestFiles / "zuma_config_verification_sequential.py")
                                        ].run()
        self.assertEqual(returnCode, 0,"Compilation failed: " + output)

        #test a wrong config
        (returnCode,output,stderr) = self.compileScript[
                                        str(self.zumaTestFiles / "sequential.v"),
                                        "--config",
                                        str(self.zumaTestFiles / "zuma_config_verification_comb.py")
                                        ].run(retcode=(0,1))
        self.assertEqual(returnCode, 1,"Compilation failed: " + output)

if __name__ == '__main__':
    unittest.main()
