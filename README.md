# TelferRITC

Telfer Rotman Interactive Trader Codebase.

Authors : **Max Gosselin, Ben Burk, Dmitry Shorikov, Jack Lau, and Shang Wu.**

This repository is a basic toolset for trading RIT cases made available to all Telfer students participating in future TTC and RITC teams. All code is free to use under MIT license.

Included are the base algo, gui controller, and various helpers. Code is commented incompletely and is presented as is, I am not responsible for maintaining or updating anything and I will not fix your broken programs. Good luck and happy trading!

If you're from another school and you're thinking of biting our code, go ahead -- definitely come buy the team a beer at RITC though :).

### Servers

rit.telfer.uottawa.ca:10001
flserver.rotman.utoronto.ca:10000     <--- (probably your best bet)

## Achitecture v3.0
REST Api polling

IPC to send data to bokeh
https://stackoverflow.com/a/6921402/9518712


## To run

```
Start the RIT client and connect to a server.
Click the API link in the bottom right corner and *set your API key to: MAXMAXMAX*

cd to working dir.

In terminal 1:
bokeh serve gui/script_name.py
open http://localhost:5006/script_name in browser
terminal 1 should say listening...

In terminal 2:
python main.py
```
----

### Dependencies
bokeh
numpy
pandas
requests

----

## Released under the MIT License


Copyright 2019 MAXIME GOSSELIN, UNIVERSITY OF OTTAWA ROTMAN INTERNATIONAL TRADING COMPETITION TEAM

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

