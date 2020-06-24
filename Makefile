ABC_EXE   := external/vtr/build/abc/abc
ODIN_EXE  := external/vtr/build/ODIN_II/odin_II
VPR       := external/vtr/build/vpr/vpr
YOSYS_EXE := external/yosys/yosys
TESTSVPR8 := StandardToolchain VerilogVerficication
TESTSVPR7 := StandardToolchainVpr7 VerilogVerficicationVpr7
TESTSBOTH := TimingBackAnnotation

EXECUTABLES := $(ABC_EXE) $(ODIN_EXE) $(VPR) $(YOSYS_EXE)
TESTS       := $(TESTSVPR7) $(TESTSVPR8) $(TESTSBOTH)

default: StandardToolchain
all: $(EXECUTABLES) $(TESTSVPR8) $(TESTSBOTH)

abc: $(ABC_EXE)
odin: $(ODIN_EXE)
vpr: $(VPR)
yosys: $(YOSYS_EXE)
tools: abc oding vpr yosys

# Tests are always out-of-date as they can be repeated
.PHONY: clean $(TESTS) all
clean:
	cd external && make clean || echo "external tools not cleaned, or already clean"

# Tests depend on working tools
$(TESTS): $(EXECUTABLES)
	cd tests/integration && python2 -m unittest $@

# Complete VTR flow, depends on being downloaded
$(EXECUTABLES):
	@echo "Building external tools"
	cd external && make
	@echo "Done building external tools"

