from luma.core.serial import i2c, spi
from luma.core.render import canvas
from luma.oled.device import ssd1306, ssd1325, ssd1331, sh1106
import time

serial = i2c(port=1, address=0x3C)

device = ssd1306(serial)


while True:
    with canvas(device) as draw:
        draw.rectangle(device.bounding_box, outline="white", fill="black")
        draw.text((10, 10), "Line1", fill="white")
        draw.text((10, 20), "Line1", fill="white")
        draw.text((10, 30), "Hello World", fill="white")



