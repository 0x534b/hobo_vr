import asyncio
import utilz as u
import time
from win32 import winxpgui
import math as m
import keyboard

import imutils
import cv2
import numpy as np
from imutils.video import VideoStream

def hasCharsInString(str1, str2):
	for i in str1:
		if i in str2:
			return True

	return False

class Poser:
	def __init__(self, addr='127.0.0.1', port=6969):
		self.pose = {
			'x':0,	# left/right
			'y':1,	# up/down
			'z':0,	# forwards/backwards
			'rW':1,
			'rX':0,
			'rY':0,
			'rZ':0,
		}

		self.offsets = {
			'x':0,
			'y':0,
			'z':0,
			'yaw':0,
			'pitch':0,
			'roll':0,
		}

		self.ypr = {'yaw':0, 'pitch':0, 'roll':0} # yaw is real roll, pitch is real yaw, roll is real pitch
		self._send = True
		self._track = True
		self._listen = True
		self._trackDelay = 0.008 # should be less than 0.3
		self._sendDelay = 0.01 # should be less than 0.5
		self._tasks = []

		self.moveStep = 0.005

		self.addr = addr
		self.port = port

	async def _socketInit(self):
		self.reader, self.writer = await asyncio.open_connection(self.addr, self.port,
												   loop=asyncio.get_event_loop())

		self.writer.write(u.convv('poser here'))

	async def close(self):
		while 1:
			await asyncio.sleep(2)
			try:
				if keyboard.is_pressed('q'):
					break

			except:
				break

		print ('closing...')
		self._send = False
		self._track = False
		self._listen = False
		self.writer.write(u.convv('CLOSE'))
		self.writer.close()

		# for i in self._tasks:
		# 	if not i.done() or not i.cancelled():
		# 		i.cancel()

	async def send(self):
		while self._send:
			try:
				msg = u.convv(' '.join([str(i) for _, i in self.pose.items()]))
				self.writer.write(msg)
				await asyncio.sleep(self._sendDelay)

			except:
				self._send = False
				break

	async def getPose(self):
		orangeHigh = (80, 50, 255)
		orangeLow = (20, 0, 200)

		vs = VideoStream(src=0).start()

		px, py, pz = 0, 0, 0

		await asyncio.sleep(2)

		while self._track:
			try:
				# x, y = winxpgui.GetCursorPos()

				# self.ypr['pitch'] = ((960 - x)/960) * m.pi
				# self.ypr['roll'] = ((960 - y)/960) * m.pi

				t0 = m.cos(self.ypr['yaw'] + self.offsets['yaw'])
				t1 = m.sin(self.ypr['yaw'] + self.offsets['yaw'])
				t2 = m.cos(self.ypr['roll'] + self.offsets['roll'])
				t3 = m.sin(self.ypr['roll'] + self.offsets['roll'])
				t4 = m.cos(self.ypr['pitch'] + self.offsets['pitch'])
				t5 = m.sin(self.ypr['pitch'] + self.offsets['pitch'])

				self.pose['rW'] = round(t0 * t2 * t4 + t1 * t3 * t5, 9)
				self.pose['rX'] = round(t0 * t3 * t4 - t1 * t2 * t5, 9)
				self.pose['rY'] = round(t0 * t2 * t5 + t1 * t3 * t4, 9)
				self.pose['rZ'] = round(t1 * t2 * t4 - t0 * t3 * t5, 9)

				await asyncio.sleep(self._trackDelay)

				if keyboard.is_pressed('4'):
					self.offsets['yaw'] -= self.moveStep
				elif keyboard.is_pressed('6'):
					self.offsets['yaw'] += self.moveStep


				if keyboard.is_pressed('8'):
					self.offsets['pitch'] -= self.moveStep
				elif keyboard.is_pressed('5'):
					self.offsets['pitch'] += self.moveStep


				if keyboard.is_pressed('3'):
					self.offsets['roll'] += self.moveStep
				elif keyboard.is_pressed('2'):
					self.offsets['roll'] -= self.moveStep

				frame = vs.read()

				if frame is not None:
					frame = imutils.resize(frame, width=600)

					blurred = cv2.GaussianBlur(frame, (11, 11), 0)

					hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

					mask = cv2.inRange(hsv, orangeLow, orangeHigh)
					mask = cv2.erode(mask, None, iterations=2)
					mask = cv2.dilate(mask, None, iterations=2)

					cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
						cv2.CHAIN_APPROX_SIMPLE)
					cnts = imutils.grab_contours(cnts)

					if len(cnts) > 0:
						c = max(cnts, key=cv2.contourArea)
						((x, y), radius) = cv2.minEnclosingCircle(c)
						px, py, pz = round(0.5 - x/600, 3), round(0.5 - y/450, 3), round(0.5 - (radius*1.2727)/42, 3)
						self.pose['x'] = px
						self.pose['y'] = py + 1
						self.pose['z'] = pz - 1

				if keyboard.is_pressed('7'):
					self.pose['x'] = 0
					self.pose['y'] = 1
					self.pose['z'] = 0

			except:
				self._track = False
				break
		vs.stop()
		cv2.destroyAllWindows()

	async def yprListener(self):
		while self._listen:
			try:
				data = await u.newRead(self.reader)
				if not hasCharsInString(data, 'aqzwsxedcrfvtgbyhnujmikolp[]{}'):
					x, y, z = [float(i) for i in data.strip('\n').strip('\r').split(',')]

					self.ypr['yaw'] = ((z * m.pi/180) - m.pi/2)
					self.ypr['roll'] = (y * m.pi/180) * -1
					self.ypr['pitch'] = (x * m.pi/180)

				await asyncio.sleep(0.01)

			except:
				self._listen = False
				break

	async def main(self):
		await self._socketInit()

		await asyncio.gather(
				self.send(),
				self.getPose(),
				self.yprListener(),
				self.close(),
			)



t = Poser()

asyncio.run(t.main())