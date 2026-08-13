import os
import sys
import time
import json
import math
import array
from typing import Literal

import pygame

if getattr(sys, "frozen", False):
    os.chdir(sys._MEIPASS)

pygame.init()

WIDTH = 72
HEIGHT = 40
SCALE = 4


class Time:
    def tick_ms(self):
        return int(time.time() * 1000)


class Micropython:
    def viper(self, func):
        return func


class Thumby:
    def __init__(self):
        self._events = []
        self._keys = pygame.key.get_pressed()
        self._input_dirty = True

        self.hardware = self.ThumbyHardware()

        self.button = self.ThumbyButton(self)
        self.buttonA = self.button.buttonA
        self.buttonB = self.button.buttonB
        self.buttonU = self.button.buttonU
        self.buttonD = self.button.buttonD
        self.buttonL = self.button.buttonL
        self.buttonR = self.button.buttonR

        self.graphics = self.ThumbyGraphics(self)
        self.display = self.graphics.display
        self.audio = self.ThumbyAudio()

        self.link = self.ThumbyLink()
        self.saveData = self.ThumbySaves()

    def _poll_input(self):
        if self._input_dirty:
            self._events = pygame.event.get()
            self._keys = pygame.key.get_pressed()
            self._input_dirty = False

            for event in self._events:
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.VIDEORESIZE:
                    self.display._handle_resize(event.w, event.h)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    self.display.toggleFullscreen()

    def _finish_frame(self):
        self._input_dirty = True

    class ThumbyHardware:
        def reset(self):
            raise NotImplementedError()

    class ThumbyButton:
        def __init__(self, thumby):
            self.buttonA = self.Button(thumby=thumby, button=pygame.K_PERIOD)
            self.buttonB = self.Button(thumby=thumby, button=pygame.K_COMMA)
            self.buttonU = self.Button(thumby=thumby, button=pygame.K_w)
            self.buttonD = self.Button(thumby=thumby, button=pygame.K_s)
            self.buttonL = self.Button(thumby=thumby, button=pygame.K_a)
            self.buttonR = self.Button(thumby=thumby, button=pygame.K_d)

            self.button_map = {
                pygame.K_COMMA: self.buttonB,
                pygame.K_PERIOD: self.buttonA,
                pygame.K_w: self.buttonU,
                pygame.K_s: self.buttonD,
                pygame.K_a: self.buttonL,
                pygame.K_d: self.buttonR,
            }

        class Button:
            def __init__(self, thumby, button):
                self.thumby = thumby
                self.button = button

            def pressed(self):
                self.thumby._poll_input()
                return self.thumby._keys[self.button]

            def justPressed(self):
                self.thumby._poll_input()
                for event in self.thumby._events:
                    if event.type == pygame.KEYDOWN and event.key == self.button:
                        return True
                return False

    def inputPressed(self):
        self._poll_input()
        for key in self.button.button_map:
            if self._keys[key]:
                return True
        return False

    def dpadPressed(self):
        self._poll_input()
        return (
            self._keys[pygame.K_UP]
            or self._keys[pygame.K_DOWN]
            or self._keys[pygame.K_LEFT]
            or self._keys[pygame.K_RIGHT]
        )

    def dpadpressed(self):
        self._poll_input()
        for event in self._events:
            if event.type == pygame.KEYDOWN:
                if event.key in [
                    pygame.K_UP,
                    pygame.K_DOWN,
                    pygame.K_LEFT,
                    pygame.K_RIGHT,
                ]:
                    return True
        return False

    def actionPressed(self):
        return self.buttonA.pressed() or self.buttonB.pressed()

    def actionpressed(self):
        return self.buttonA.pressed() or self.buttonB.pressed()

    class Sprite:
        def __init__(
            self, width, height, bitmapData, x=0, y=0, key=-1, mirrorX=0, mirrorY=0
        ):
            self.width = width
            self.height = height
            self.bitmapData = bitmapData
            self.x = x
            self.y = y
            self.key = key
            self.mirrorX = mirrorX
            self.mirrorY = mirrorY
            bytes_per_frame = width * ((height + 7) // 8)
            bitmap_length = len(bitmapData[0]) if isinstance(bitmapData, (tuple, list)) and len(bitmapData) == 2 else len(bitmapData)
            self.frameCount = bitmap_length // bytes_per_frame if bytes_per_frame else 0
            self._frame = 0

        def getFrame(self):
            return self._frame

        def setFrame(self, frame):
            if self.frameCount > 0:
                self._frame = frame % self.frameCount
            else:
                self._frame = 0

    class ThumbyGraphics:
        def __init__(self, thumby):
            self.display = self.Display(thumby)

        class Display:
            def __init__(self, thumby):
                self._thumby = thumby
                self.width = WIDTH
                self.height = HEIGHT

                self.BLACK = 0
                self.WHITE = 1
                self.DARKGRAY = 2
                self.LIGHTGRAY = 3

                self._fps = 0  # non-limiting
                self._surface = pygame.Surface((self.width, self.height))
                self._windowed_size = (self.width * SCALE, self.height * SCALE)
                self._fullscreen = False
                self._screen = self._create_screen(self._windowed_size)
                self._brightness = 255
                self.setFont("font5x7.bin", 5, 7, 1)

            def _create_screen(self, size, fullscreen=False):
                flags = pygame.RESIZABLE | pygame.DOUBLEBUF
                if fullscreen:
                    flags = pygame.FULLSCREEN | pygame.DOUBLEBUF
                    size = (0, 0)
                return pygame.display.set_mode(size, flags)

            def setFullscreen(self, enabled=True):
                self._fullscreen = enabled
                if enabled:
                    self._screen = self._create_screen((0, 0), fullscreen=True)
                else:
                    self._screen = self._create_screen(self._windowed_size)

            def toggleFullscreen(self):
                self.setFullscreen(not self._fullscreen)

            def _handle_resize(self, width, height):
                if not self._fullscreen:
                    self._windowed_size = (max(1, width), max(1, height))
                    self._screen = self._create_screen(self._windowed_size)

            @property
            def _white(self):
                return (self._brightness, self._brightness, self._brightness, 255)

            @property
            def _black(self):
                return (0, 0, 0, 255)

            def _grayColor(self, color):
                if color == 0:
                    return self._black
                if color == 1:
                    return self._white
                if color == 2:
                    gray = int(self._brightness * 0.35)
                    return (gray, gray, gray, 255)
                if color == 3:
                    gray = int(self._brightness * 0.75)
                    return (gray, gray, gray, 255)
                return self._black

            def enableGrayscale(self):
                return None

            def disableGrayscale(self):
                return None

            def show(self):
                self.update()

            def drawText(self, stringToPrint, x, y, color):
                screenWidth, screenHeight = self._surface.get_size()
                maxChar = self.textCharCount

                for char in stringToPrint:
                    charBitmap = ord(char) - 0x20
                    spriteSurface = pygame.Surface(
                        (self.textWidth, self.textHeight), pygame.SRCALPHA, 32
                    )
                    if 0 <= charBitmap <= maxChar:
                        if (
                            0 <= x + self.textWidth <= screenWidth
                            and 0 <= y + self.textHeight <= screenHeight
                        ):
                            sprite = [
                                [False] * self.textWidth for _ in range(self.textHeight)
                            ]
                            self.textBitmapFile.seek(charBitmap * self.textWidth)
                            self.textBitmap = self.textBitmapFile.read(self.textWidth)
                            for i in range(self.textHeight):
                                for j in range(self.textWidth):
                                    sprite[i][j] = (
                                        self.textBitmap[(i >> 3) * self.textWidth + j]
                                        & (1 << (i & 0x07))
                                    ) != 0

                            for i in range(self.textHeight):
                                for j in range(self.textWidth):
                                    if sprite[i][j]:
                                        spriteSurface.set_at((j, i), self._grayColor(color))

                    self._surface.blit(spriteSurface, (x, y))
                    x += self.textWidth + self.textSpaceWidth

            def setFont(self, fontFilePath, width, height, space):
                self.textBitmapSource = fontFilePath
                self.textBitmapFile = open(self.textBitmapSource, "rb")
                self.textWidth = width
                self.textHeight = height
                self.textSpaceWidth = space
                self.textBitmap = bytearray(self.textWidth)
                self.textCharCount = os.stat(self.textBitmapSource)[6] // self.textWidth

            def update(self):
                self._thumby._poll_input()
                screen_width, screen_height = self._screen.get_size()
                scale = min(screen_width / self.width, screen_height / self.height)
                target_width = max(1, int(self.width * scale))
                target_height = max(1, int(self.height * scale))
                upscaled_surface = pygame.transform.scale(
                    self._surface, (target_width, target_height)
                )
                self._screen.fill((0, 0, 0))
                self._screen.blit(
                    upscaled_surface,
                    (
                        (screen_width - target_width) // 2,
                        (screen_height - target_height) // 2,
                    ),
                )
                pygame.display.flip()
                if self._fps != 0:
                    pygame.time.wait(1000 // self._fps)
                self._thumby._finish_frame()

            def setFPS(self, FPS: int = 0) -> None:
                self._fps = FPS

            def fill(self, color):
                self._surface.fill(self._grayColor(color))

            def brightness(self, brightness):
                self._brightness = (brightness / 127) * 255

            def setPixel(self, x: int, y: int, color):
                if 0 <= x < self.width and 0 <= y < self.height:
                    self._surface.set_at((x, y), self._grayColor(color))

            def getPixel(self, x, y):
                if 0 <= x < self.width and 0 <= y < self.height:
                    pixel = self._surface.get_at((x, y))
                    if pixel[:3] == (0, 0, 0):
                        return 0
                    if pixel[:3] == (self._brightness, self._brightness, self._brightness):
                        return 1
                    if pixel[:3] == (int(self._brightness * 0.35),) * 3:
                        return 2
                    if pixel[:3] == (int(self._brightness * 0.75),) * 3:
                        return 3
                return 0

            def drawLine(self, x1, y1, x2, y2, color):
                pygame.draw.line(self._surface, self._grayColor(color), (x1, y1), (x2, y2))

            def drawFilledRectangle(self, x, y, w, h, color):
                pygame.draw.rect(self._surface, self._grayColor(color), (x, y, w, h))

            def drawRectangle(self, x, y, w, h, color):
                pygame.draw.rect(self._surface, self._grayColor(color), (x, y, w, h), 1)

            def blit(self, bitmapData, x, y, width, height, key, mirrorX, mirrorY):
                sprite = Thumby.Sprite(
                    width, height, bitmapData, x, y, key, mirrorX, mirrorY
                )
                self.drawSprite(sprite)

            def blitWithMask(
                self,
                bitmapData,
                x,
                y,
                width,
                height,
                key,
                mirrorX,
                mirrorY,
                maskBitmapData,
            ):
                sprite = Thumby.Sprite(
                    width, height, bitmapData, x, y, key, mirrorX, mirrorY
                )
                maskSprite = Thumby.Sprite(
                    width, height, maskBitmapData, x, y, key, mirrorX, mirrorY
                )
                self.drawSpriteWithMask(sprite, maskSprite)

            def drawSprite(self, sprite):
                surface = pygame.Surface(
                    (sprite.width, sprite.height), pygame.SRCALPHA, 32
                )
                bits_per_byte = 8
                bitmapData = sprite.bitmapData
                grayscale = isinstance(bitmapData, (tuple, list)) and len(bitmapData) == 2
                bytes_per_frame = sprite.width * ((sprite.height + 7) // 8)
                offset = bytes_per_frame * sprite.getFrame()
                row_count = (sprite.height + 7) // 8

                for i in range(bytes_per_frame):
                    source_x = i % sprite.width
                    source_y_block = i // sprite.width
                    draw_x = sprite.width - 1 - source_x if sprite.mirrorX else source_x
                    draw_y_block = row_count - 1 - source_y_block if sprite.mirrorY else source_y_block

                    byte_index = i + offset
                    byte = bitmapData[byte_index] if not grayscale else (bitmapData[0][byte_index] if len(bitmapData[0]) > byte_index else 0)
                    if grayscale:
                        byte2 = bitmapData[1][byte_index] if len(bitmapData[1]) > byte_index else 0
                    else:
                        byte2 = 0
                    for j in range(bits_per_byte):
                        bit_index = 7 - j if sprite.mirrorY else j
                        x = draw_x
                        y = 8 * draw_y_block + j

                        bit = (byte >> bit_index) & 1
                        if grayscale:
                            bit2 = (byte2 >> bit_index) & 1
                            color_value = bit | (bit2 << 1)
                        else:
                            color_value = bit
                        color = self._grayColor(color_value)
                        if sprite.key == -1:
                            surface.set_at((x, y), color)
                        elif sprite.key != color_value:
                            surface.set_at((x, y), color)

                self._surface.blit(
                    surface, (sprite.x, sprite.y), (0, 0, sprite.width, sprite.height)
                )

            def drawSpriteWithMask(self, sprite, maskSprite):
                surface = pygame.Surface(
                    (sprite.width, sprite.height), pygame.SRCALPHA, 32
                )
                mask_surface = pygame.Surface(
                    (sprite.width, sprite.height), pygame.SRCALPHA, 32
                )
                bits_per_byte = 8
                sprite_gray = isinstance(sprite.bitmapData, (tuple, list)) and len(sprite.bitmapData) == 2
                mask_gray = isinstance(maskSprite.bitmapData, (tuple, list)) and len(maskSprite.bitmapData) == 2
                bytes_per_frame = sprite.width * ((sprite.height + 7) // 8)
                offset = bytes_per_frame * sprite.getFrame()
                row_count = (sprite.height + 7) // 8
                for i in range(bytes_per_frame):
                    source_x = i % sprite.width
                    source_y_block = i // sprite.width
                    draw_x = sprite.width - 1 - source_x if sprite.mirrorX else source_x
                    draw_y_block = row_count - 1 - source_y_block if sprite.mirrorY else source_y_block
                    byte_index = i + offset

                    byte = sprite.bitmapData[byte_index] if not sprite_gray else (sprite.bitmapData[0][byte_index] if len(sprite.bitmapData[0]) > byte_index else 0)
                    mask_byte = (
                        maskSprite.bitmapData[byte_index]
                        if not mask_gray
                        else (maskSprite.bitmapData[0][byte_index] if len(maskSprite.bitmapData[0]) > byte_index else 0)
                    )
                    if sprite_gray:
                        byte2 = sprite.bitmapData[1][byte_index] if len(sprite.bitmapData[1]) > byte_index else 0
                    else:
                        byte2 = 0
                    if mask_gray:
                        mask_byte2 = maskSprite.bitmapData[1][byte_index] if len(maskSprite.bitmapData[1]) > byte_index else 0
                    else:
                        mask_byte2 = 0

                    for j in range(bits_per_byte):
                        bit_index = 7 - j if sprite.mirrorY else j
                        x = draw_x
                        y = 8 * draw_y_block + j

                        bit = (byte >> bit_index) & 1
                        mask_bit = (mask_byte >> bit_index) & 1
                        if sprite_gray:
                            bit = bit | ((byte2 >> bit_index) & 1) << 1
                        if mask_gray:
                            mask_bit = mask_bit | ((mask_byte2 >> bit_index) & 1) << 1
                        color = self._grayColor(bit)
                        mask_color = self._grayColor(mask_bit)

                        if sprite.key == -1 and maskSprite.key == -1:
                            surface.set_at((x, y), color)
                            mask_surface.set_at((x, y), mask_color)
                        elif sprite.key != bit and maskSprite.key != mask_bit:
                            surface.set_at((x, y), color)
                            mask_surface.set_at((x, y), mask_color)

                surface.blit(mask_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                self._surface.blit(
                    surface, (sprite.x, sprite.y), (0, 0, sprite.width, sprite.height)
                )

    class ThumbyAudio:
        def __init__(self):
            self._freq = 0

        def play(self, freq, duration):
            self._freq = freq
            sample_rate = 44100  # sampling rate in Hz
            num_samples = int(sample_rate * duration)
            amplitude = 32767
            samples = array.array("h")
            for i in range(num_samples):
                value = int(
                    amplitude * math.sin(2 * math.pi * freq * i / sample_rate)
                )
                samples.append(value)
                samples.append(value)
            pygame.mixer.init(frequency=sample_rate, size=-16, channels=2)
            sound = pygame.mixer.Sound(buffer=samples.tobytes())
            sound.play()

        def playBlocking(self, freq, duration):
            self.play(freq, duration)
            while pygame.mixer.get_busy():
                pygame.time.wait(100)

        def stop(self):
            pygame.mixer.music.stop()

        def setEnabled(self, setting):
            if setting:
                pygame.mixer.unpause()
            else:
                pygame.mixer.pause()

        def set(self, freq):
            self._freq = freq

    class ThumbyLink:
        def send(self, data):
            raise NotImplementedError()

        def receive(self):
            raise NotImplementedError()

    class ThumbySaves:
        def __init__(self):
            self.subdirectoryName = None

            self._data = {}

        def setName(self, subdirectoryName):
            os.makedirs("Saves/" + subdirectoryName, exist_ok=True)
            # creates a persistent.json file for save data to Saves/subdirectoryName/persistent.json
            save_path = "Saves/" + subdirectoryName + "/persistent.json"
            if os.path.exists(save_path):
                try:
                    with open(save_path, "r") as f:
                        data = f.read()
                    self._data = json.loads(data) if data else {}
                except (json.JSONDecodeError, OSError):
                    self._data = {}
            else:
                with open(save_path, "w"):
                    pass
                self._data = {}
            self.subdirectoryName = subdirectoryName

        def setItem(self, key, value):
            self._data[key] = value

        def getItem(self, key):
            return self._data[key]

        def hasItem(self, key):
            return key in self._data

        def delItem(self, key):
            if self.hasItem(key):
                del self._data[key]

        def save(self):
            with open("Saves/" + self.subdirectoryName + "/persistent.json", "w+") as f:
                f.write(json.dumps(self._data))

        def getName(self):
            return self.subdirectoryName
