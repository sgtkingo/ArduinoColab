# Arduino Colab Project 

# Arduino Bridge 
This is HW<->frontend bridge component of [Arduino Colab Project](https://github.com/sgtkingo/ArduinoColab.git).

---

## How to Use

### 1. Running the Remote Server

To use the remote backend (for cloud or remote Jupyter/Colab environments), you need to run the remote server on the machine connected to your Arduino hardware.

**Install dependencies:**
```bash
pip install -r .\requirements.txt
```

**Run the server:**
**RUN** server with default settings (localhost):
```bash
python -m arduino_colab_server.py
```
*OR* use custom port and token:
```bash
python -m arduino_colab_server.py --port 5000 --token YOUR_TOKEN
```
- Replace `YOUR_TOKEN` with a secure token of your choice.
- The server will listen for requests from the frontend (Colab/Jupyter).

### 1.1 Open server site in web-browser
**Open** server URL address in web-browser and copy *TOKEN*, and *Server URL* if needed.

### 2. Connecting from the Client (Colab/Jupyter)

In your Jupyter/Colab notebook, load the magics and set up the remote backend:

```python
%load_ext arduino_colab_kernel.magic_project
%load_ext arduino_colab_kernel.magic_board
%load_ext arduino_colab_kernel.magic_code
%load_ext arduino_colab_kernel.magic_serial

MY_API_TOKEN = input("Enter your API token: ")  # Use the same token as the server
REMOTE_URL = "http://<server-ip>:<server-port>"  # Replace <server-ip> and <server-port> with your server's IP address and port (*Optional*)

# Load or initialize a project in remote mode
%project load --mode remote --remote_url $REMOTE_URL --token $MY_API_TOKEN
# init
%project init --mode remote --remote_url $REMOTE_URL --token $MY_API_TOKEN

# or use simplify version with default server address:
%project load --mode remote --token {MY_API_TOKEN}
# init
%project init --mode remote --token {MY_API_TOKEN}
```

### 3. Workflow

- Use `%project`, `%board`, `%%code`, and `%serial` magics as usual.
- All compile/upload/serial operations will be forwarded to the remote server.

---

## Example

```python
# Set up remote backend
MY_API_TOKEN = "YOUR_TOKEN"
REMOTE_URL = "http://192.168.1.100:5000"

%project init my_project --mode remote --remote_url $REMOTE_URL --token $MY_API_TOKEN
%board select uno
%%code setup
pinMode(13, OUTPUT);
%%code loop
digitalWrite(13, HIGH); delay(500); digitalWrite(13, LOW); delay(500);
%board upload
%serial listen --duration 10
```

---

## Security

- Always use a strong, secret token for authentication.
- Never expose your remote server to the public internet without proper security.

---

For more details, see project Arduino Colab on [Github](https://github.com/sgtkingo/ArduinoColab)