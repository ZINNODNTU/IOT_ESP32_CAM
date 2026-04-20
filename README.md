# IOT_ESP32_CAM
pip install -r requirements.txt
sudo apt update -y && sudo apt install -y python3-pip python3-venv libgl1 && python3 -m venv venv && source venv/bin/activate && pip install tornado numpy imutils opencv-python websockets requests && python websockets_stream.py

rm -rf IOT_ESP32_CAM
git clone https://github.com/ZINNODNTU/IOT_ESP32_CAM.git
cd IOT_ESP32_CAM
cd python_backend