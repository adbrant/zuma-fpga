# ZUMA
## Introduction
This repository contains the ZUMA FPGA overlay architecture system that was introduced by Brant and Lemieux in 2012 and later extended by Wiersema, Bockhorn, Platzner, and several students of Paderborn University.

The folders contain a number of components needed to use ZUMA, 
as well as examples and tests.

### Directory structure
<table>
  <tr>
    <td>doc/</td>
    <td>Contains the <a href="doc/ZUMA.pdf">user's manual</a>.</td>
  </tr>
  <tr>
    <td>example/</td>
    <td>Contains example files to get started.</td>
  </tr>
  <tr>
    <td>external/</td>
    <td>Required third party tools as GIT submodules.</td>
  </tr>
  <tr>
    <td>source/</td>
    <td>Scripts to generate the ZUMA Verilog components and bitstreams.</td>
  </tr>
  <tr>
    <td>tests/</td>
    <td>Included scripts used to test ZUMA components.</td>
  </tr>
  <tr>
    <td>tests/integration/</td>
    <td>Python unit tests for the ZUMA scripts.</td>
  </tr>
  <tr>
    <td>verilog/</td>
    <td>Verilog project files to instantiate a ZUMA system.</td>
  </tr>
  <tr>
    <td>license.txt</td>
    <td>The license under which ZUMA can be used.</td>
  </tr>
  <tr>
    <td>Makefile</td>
    <td>Global Makefile to prepare a working tool flow.</td>
  </tr>
  <tr>
    <td>toolpaths.py</td>
    <td>Global path setup.</td>
  </tr>
</table>

## Building
You will need a Linux installation with a working Python 2.7 installation.
Then just run ```make``` from the root directory.

For more details see the user's manual, [Section 2](doc/ZUMA.pdf).

## Running the Tools
Calling the Python script ```compile.sh test.v``` will automatically build the ZUMA system Verilog ```ZUMA_custom_generated.v```, and a bitstream hex file ```output.hex```, which can be used to synthesize and configure a ZUMA system. 
By passing other circuit files, modifying the example ZUMA configuration file ```zuma_config.py```, or providing an alternative configuration file via the _--config_ command line switch, custom architectures and bitstreams can be generated.

For more details see the user's manual, [Section 3](doc/ZUMA.pdf).

## Including a ZUMA Overlay in a Project
Once the Verilog architecture is created, and a hex bitstream is generated, the ZUMA system can be compiled and used.
The generated Verilog file that describes the virtual fabric, along with the files in the ```verilog/generic/``` and ```verilog/platform/(platform)/``` directories should be included in a new Xilinx / Altera project, although getting it to work for Altera devices might require some (read: significant amount of) additional work.

For more details see the user's manual, [Section 5](doc/ZUMA.pdf).

## License
See the [license file](license.txt) for details.

## List of Contributors
Listed alphabetically.

Arne Bockhorn, Alexander D. Brant, Guy G. F. Lemieux, Monica Keerthipati, Nithin S. Sabu, Tobias Wiersema
