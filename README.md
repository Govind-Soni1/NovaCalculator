# Nova Calculator

A modern desktop calculator built with Python and Tkinter, inspired by the Windows Calculator experience.

Nova Calculator provides a clean interface, standard arithmetic operations, compact and expanded modes, and calculation history.

## Features

* Standard arithmetic operations
* Percentage, reciprocal, square, and square root
* Keyboard input support
* Compact and expanded window modes
* Resizable desktop interface
* Calculation history
* Custom application icon
* Windows executable support

## Built With

* Python
* Tkinter
* PyInstaller

## Getting Started

### Prerequisites

* Python 3.10 or newer
* Windows operating system

### Run from source

Clone the repository:

```bash
git clone https://github.com/Govind-Soni1/NovaCalculator.git
```

Navigate to the project directory:

```bash
cd NovaCalculator
```

Run the application:

```bash
python nova_calculator.py
```

## Build the Windows Executable

Install PyInstaller:

```bash
pip install pyinstaller
```

Build the application:

```bash
pyinstaller --clean --noconfirm --onefile --windowed --icon=calculator.ico --add-data "calculator.png;." --name="NovaCalculator" nova_calculator.py
```

The executable will be generated in the `dist` directory.

## Project Structure

```text
NovaCalculator/
├── assets/
├── nova_calculator.py
├── README.md
├── .gitignore
└── LICENSE
```

## Future Improvements

* Persistent calculation history
* Fully functional memory operations
* Additional mathematical functions
* Improved interface animations
* Enhanced keyboard shortcuts

## License

See the LICENSE file for details.
