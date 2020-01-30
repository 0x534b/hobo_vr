import asyncio
import utilz as u
import time
# from win32 import winxpgui
import math as m
import keyboard

import imutils
import cv2
import numpy as np
from imutils.video import VideoStream
import random

def hasCharsInString(str1, str2):
	for i in str1:
		if i in str2:
			return True

	return False

def swapByOffset(a, b, offset):
	offset = abs(offset)
	return a - a*offset + b*offset, b - b*offset + a*offset

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

		self.poseControllerR = {
			'x':0.5,	# left/right
			'y':1,	# up/down
			'z':0,	# forwards/backwards
			'rW':1,
			'rX':0,
			'rY':0,
			'rZ':0,
			'grip':0,	# 0 or 1
			'system':0,	# 0 or 1
			'menu':0,	# 0 or 1
			'trackpadClick':0,	# 0 or 1
			'triggerValue':0,	# from 0 to 1
			'trackpadX':0,	# from -1 to 1
			'trackpadY':0,	# from -1 to 1
		}
		self.poseControllerL = {
			'x':0.5,	# left/right
			'y':1.1,	# up/down
			'z':0,	# forwards/backwards
			'rW':1,
			'rX':0,
			'rY':0,
			'rZ':0,
			'grip':0,	# 0 or 1
			'system':0,	# 0 or 1
			'menu':0,	# 0 or 1
			'trackpadClick':0,	# 0 or 1
			'triggerValue':0,	# from 0 to 1
			'trackpadX':0,	# from -1 to 1
			'trackpadY':0,	# from -1 to 1
		}

		self.offsets = {
			'x':0,
			'y':0,
			'z':0,
			'roll':0,
			'yaw':0,
			'pitch':0,
		}

		self.ypr = {'roll':0, 'yaw':0, 'pitch':0} # yaw is real roll, pitch is real yaw, roll is real pitch
		self._send = True
		self._track = True
		self._listen = True
		self._trackDelay = 0.002 # should be less than 0.3
		self._sendDelay = 0.04 # should be less than 0.5
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

		print ('closing...', self.offsets)
		self._send = False
		self._track = False
		self._listen = False

		await asyncio.sleep(1)

		self.writer.write(u.convv('CLOSE'))
		self.writer.close()

		# for i in self._tasks:
		# 	if not i.done() or not i.cancelled():
		# 		i.cancel()

	async def send(self):
		while self._send:
			try:
				msg = u.convv(' '.join([str(i) for _, i in self.pose.items()] + [str(i) for _, i in self.poseControllerR.items()] + [str(i) for _, i in self.poseControllerL.items()]))
				# msg = u.convv(' '.join([str(random.random()) for _ in range(35)]))
				self.writer.write(msg)
				await asyncio.sleep(self._sendDelay)

			except:
				self._send = False
				break

	async def getLocation(self):
		
		orangeHigh = (255, 0, 255)
		orangeLow = (0, 0, 200)


		vs = cv2.VideoCapture(4)

		px, py, pz = 0, 0, 0

		await asyncio.sleep(2)

		while self._track:
			try:
				# x, y = winxpgui.GetCursorPos()

				# self.ypr['yaw'] = ((960 - x)/960) * m.pi
				# self.ypr['pitch'] = ((960 - y)/960) * m.pi

				await asyncio.sleep(self._trackDelay)

				if keyboard.is_pressed('4'):
					self.offsets['roll'] -= self.moveStep
				elif keyboard.is_pressed('6'):
					self.offsets['roll'] += self.moveStep


				if keyboard.is_pressed('8'):
					self.offsets['yaw'] -= self.moveStep
				elif keyboard.is_pressed('5'):
					self.offsets['yaw'] += self.moveStep


				if keyboard.is_pressed('3'):
					self.offsets['pitch'] += self.moveStep
				elif keyboard.is_pressed('2'):
					self.offsets['pitch'] -= self.moveStep

				_, frame = vs.read()

				if frame is not None:
					frame = imutils.resize(frame, width=600)

					blurred = cv2.GaussianBlur(frame, (11, 11), 0)

					hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

					mask = cv2.inRange(hsv, orangeLow, orangeHigh)
					mask = cv2.erode(mask, None, iterations=1)
					mask = cv2.dilate(mask, None, iterations=3)

					cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
						cv2.CHAIN_APPROX_SIMPLE)
					cnts = imutils.grab_contours(cnts)

					if len(cnts) > 0:
						c = max(cnts, key=cv2.contourArea)
						((x, y), radius) = cv2.minEnclosingCircle(c)
						px, py, pz = round(x/640 - 0.5, 4), round(y/480 - 0.5, 4), round(radius/60, 4)
						py *= -1
						px *= -1
						pz *= -1

						self.pose['x'] = px
						self.pose['y'] = py + 1
						self.pose['z'] = pz

					# cv2.imshow('hentai', frame)
 
				if keyboard.is_pressed('7'):
					self.pose['x'] = 0
					self.pose['y'] = 1
					self.pose['z'] = 0

			except:
				self._track = False
				break
		vs.release()
		cv2.destroyAllWindows()

	async def yprListener(self):
		while self._listen:
			try:
				data = await u.newRead(self.reader)
				if not hasCharsInString(data.lower(), 'aqzwsxedcrfvtgbyhnujmikolp[]{}'):
					x, y, z = [float(i) for i in data.strip('\n').strip('\r').split(',')]

					# x -= 0.5
					# y += 0.5
					# z -= 0.5

					x, y = swapByOffset(x, y, z)

					self.ypr['roll'] = (z * m.pi)	# yaw
					self.ypr['yaw'] = (y * m.pi) * (-1)	# roll
					self.ypr['pitch'] = (x * m.pi)	#pitch

					# print (self.ypr)

					# for key, val in self.ypr.items():
					# 	if val < 0:
					# 		self.ypr[key] = 2*m.pi - abs(val)


					# print (quaternion2ypr(self.pose['rW'], self.pose['rX'], self.pose['rY'], self.pose['rZ']))

					cy = np.cos((self.ypr['roll'] + self.offsets['roll']) * 0.5)
					sy = np.sin((self.ypr['roll'] + self.offsets['roll']) * 0.5)
					cp = np.cos((self.ypr['pitch'] + self.offsets['pitch']) * 0.5)
					sp = np.sin((self.ypr['pitch'] + self.offsets['pitch']) * 0.5)
					cr = np.cos((self.ypr['yaw'] + self.offsets['yaw']) * 0.5)
					sr = np.sin((self.ypr['yaw'] + self.offsets['yaw']) * 0.5)

					self.pose['rW'] = round(cy * cp * cr + sy * sp * sr, 4)
					self.pose['rZ'] = round(cy * cp * sr - sy * sp * cr, 4)
					self.pose['rX'] = round(sy * cp * sr + cy * sp * cr, 4)
					self.pose['rY'] = round(sy * cp * cr - cy * sp * sr, 4)

				await asyncio.sleep(self._trackDelay)

			except Exception as e:
				print ('listener',e)
				self._listen = False
				break

	async def main(self):
		await self._socketInit()

		await asyncio.gather(
				self.send(),
				self.getLocation(),
				self.yprListener(),
				self.close(),
			)



t = Poser()

asyncio.run(t.main())