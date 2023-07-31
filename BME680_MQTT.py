import time
import machine
import network
from breakout_bme68x import BreakoutBME68X
from pimoroni_i2c import PimoroniI2C
from umqtt.simple import MQTTClient

# Wi-Fi Configuration
WIFI_SSID = "YOUR_WIFI_NAME"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"

# MQTT Configuration
#BASED ON YOUR CONFIGURATION, PUT THE BELOW INFO
MQTT_SERVER = 'broker.hivemq.com'
CLIENT_ID = '####'
TOPIC_TEMP = b'####/Temp'
TOPIC_HUMIDITY = b'####/Humidity'
TOPIC_PRESSURE = b'####/Pressure'
TOPIC_GAS = b'####/Gas'

# Pin Configuration
PINS_BREAKOUT_GARDEN = {"sda": 4, "scl": 5}

# Connect to Wi-Fi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(WIFI_SSID, WIFI_PASSWORD)

# Connect to MQTT Broker
def mqtt_connect():
    client = MQTTClient(CLIENT_ID, MQTT_SERVER, keepalive=60)
    client.connect()
    print('Connected to %s MQTT Broker' % MQTT_SERVER)
    return client

def reconnect():
    print('Failed to connect to the MQTT Broker. Reconnecting...')
    time.sleep(5)
    machine.reset()

# Initialize BME680 Sensor
i2c = PimoroniI2C(**PINS_BREAKOUT_GARDEN)
bme = BreakoutBME68X(i2c)

# Initialize LED pin
led =  machine.Pin('LED', machine.Pin.OUT) # Assuming LED is connected to GPIO 2

# Gas Resistance to Gas Level Conversion Parameters
GAS_RESISTANCE_BASE = 100000  # Reference resistance value for clean air
GAS_LEVEL_BASE = 500 / GAS_RESISTANCE_BASE  # Gas level conversion to ppm

# Main Loop
retries = 0
while True:
    try:
        temperature, pressure, humidity, gas, status, _, _ = bme.read()

        print("{:0.2f}°C, {:0.2f} Pa, {:0.2f}%, {:0.2f} Ohms".format(
            temperature, pressure, humidity, gas))

        temperature = round(temperature, 1)
        pressure = round(pressure / 1000, 2)  # Convert pressure to kPa
        humidity = round(humidity, 1)

        # Calculate gas level in ppm
        gas_level = gas * GAS_LEVEL_BASE
        gas_level = max(0, min(gas_level, 500))  # Clamp the value between 0 and 500
        gas_level = round(gas_level, 2)

        client = mqtt_connect()
        client.publish(TOPIC_TEMP, str(temperature))
        client.publish(TOPIC_PRESSURE, str(pressure))
        client.publish(TOPIC_HUMIDITY, str(humidity))
        client.publish(TOPIC_GAS, str(gas_level))
        client.disconnect()

        # Blink the LED
        led.on()
        time.sleep(0.1)
        led.off()

        time.sleep(4.9)  # Delay for 4.9 seconds (total delay will be 5 seconds)
        retries = 0  # Reset retry count after a successful iteration
    except Exception as e:
        print('An error occurred:', str(e))
        reconnect()
        retries += 1



