# TransformerApp v0.1.1
TransformerApp is a python based helper for compiling specifications, designing turns, and finding wire diameters in power converter transformer design.
## Features
The application includes 3 utilities to support engineers in designing a transformer:
- circuit compiler: takes in circuit specification and calculate maximum current, turns ratio, etc.
- turns designer: calculate the number of turns for each winding with excel core database
- wire diameter designer: find a feasible/optimal diameter solution that fits the bobbin without exceeding designated current density

The current version supports the following common topologies of power converters specification compilation, current calculation, etc. (circuit compiler)
- flyback
- forward

However, the turns designer and wire diameter designer are independent of the circuit compiler. That is, as long as you specify the constraints clearly, you can still design the turns and find a feasible solution to the wire diameter design!

The application also supports yaml export and import, which allows the user to save his or her progress!

## Quick Start
To run the script, please install the dependencies first. Under ```TransformerApp\```
```pip install -r requirements.txt```
To run the entire application, under ```TransformerApp\```
```python main.py```
And you're good to go!

---


If a single execution file is preferred, here's an easy instruction. Run
```pip install pyinstaller```
if you don't have the package in your environment yet.
Then, under ```TransformerApp\```, run
```pyinstaller --onefile main.py```
This command produces a .exe file available for the user. You can always include options to your taste. However, the core data file is not packed together, you should still load it or append it explicitly.

## Details
For more details on how to use the application or development notes, please refer to ```doc\UserManual.docx``` and ```doc\DevelopmentNotes.docx```.

## Changelog

### [v0.1.0] 2025-08-06
Initial release