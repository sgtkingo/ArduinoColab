# Arduino Colab Project 🔌

Jupyter/Colab extension for writing and running Arduino/ESP32 code directly in notebooks.  
This project provides **magic commands** (`%project`, `%board`, `%%code`, `%%serial`) that allow you to:

- structure your Arduino sketch into sections (`globals`, `setup`, `loop`, `functions`),
- manage projects and export them into `.ino`,
- compile and upload code to supported boards (Uno, Nano),
- interact with the serial port directly from Jupyter notebooks.

---

## 🚀 Quick start

### Install the package

```bash
pip install arduino-colab-kernel
```

or for development:

```bash
git clone https://github.com/sgtkingo/ArduinoColab.git
cd ArduinoColab/colab
pip install -e .
```

> ⚠️ Requirement: [Arduino CLI](https://arduino.github.io/arduino-cli/latest/) or [Arduino IDE](https://www.arduino.cc/en/software/) must be installed, or use the binary provided in the package (`tools/arduino-cli.exe` or `arduino-cli` package).

### Initialize a project

```python
%load_ext magic_project
%load_ext magic_board
%load_ext magic_code
%load_ext magic_serial
```

1. Create a project:

```python
%project init demo
```

2. Select board and port:

```python
%board select uno
# Keep automatic port selection or use manual configuration:
%board serial --port COM5 --baud 115200
```

3. Add code into sections:

```python
%%code globals
int led = 13;

%%code setup
pinMode(led, OUTPUT);

%%code loop
digitalWrite(led, HIGH); delay(500);
digitalWrite(led, LOW);  delay(500);
```

4. Upload to the board:

```python
%board upload
```

5. Monitor serial output:

```python
%serial listen 5
```

---

## 📘 Magic commands

### `%project`
Project management.

- `%project init [name]` – create a new project, "sketch" is default 
- `%project load [name]` – load existing project, "sketch" is default   
- `%project clear [section] [cell]` – clear content  
- `%project show` – show project overview  
- `%project export` – export project into `.ino`  
- `%project help` – show help  

---

### `%board`
Board selection and upload.

- `%board select [uno|nano]` – select board  
- `%board status` – show current board configuration  
- `%board serial [--port COMx] [--baud 115200]` – configure serial connection  
- `%board compile [sketch_dir_or_ino]` – compile sketch, using project .ino file as default 
- `%board upload [sketch_dir_or_ino]` – upload sketch, using project .ino file as default    
- `%board list` – list supported boards  
- `%board ports` – list available serial ports  

---

### `%%code`
Arduino code organization into sections.

- `%%code globals` – global variables  
- `%%code setup` – setup section  
- `%%code loop` – main loop  
- `%%code functions` – custom functions  

---

### `%serial`
Serial port interaction.

- `%serial listen [sec]` – listen for serial output  
- `%serial read [lines]` – read a number of lines  
- `%serial write "text"` – send data  

---

## 📊 Architecture

The project consists of four main managers/components, each controlled by its own magic commands:

- **Project Manager** (`%project`) – manages project lifecycle and sections
- **Code Manager** (`%%code`) – organizes code into Arduino sketch sections
- **Board Manager** (`%board`) – compiles and uploads code to boards
- **Serial Port** (`%serial`) – provides serial input/output
---

## ✅ Supported OS
- **Windows 10 (64-bit) and newer version**
- **Linux-based OS**

## 📄 License
MIT (see `LICENSE`).  
See also [Arduino CLI Project `LICENSE`](https://github.com/arduino/arduino-cli/blob/master/LICENSE.txt)