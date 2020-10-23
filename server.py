import socket
from _thread import *
import _pickle as pickle
import time
import random
import math


S = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
S.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

PORT = 5555

BALL_RADIUS = 5
START_RADIUS = 7

ROUND_TIME = 60 * 5

MASS_LOSS_TIME = 7

W, H = 1600, 830

HOST_NAME = socket.gethostname()
SERVER_IP = socket.gethostbyname(HOST_NAME)

try:
    S.bind((SERVER_IP, PORT))
except socket.error as e:
    print(str(e))
    print("[SERVER] Server could not start")
    quit()

S.listen() 

print(f"[SERVER] Server Started with local ip {SERVER_IP}")

players = {}
balls = []
connections = 0
_id = 0
colors = [(255,0,0), (255, 128, 0), (255,255,0), (128,255,0),(0,255,0),(0,255,128),(0,255,255),(0, 128, 255), (0,0,255), (0,0,255), (128,0,255),(255,0,255), (255,0,128),(128,128,128), (0,0,0)]
start = False
stat_time = 0
game_time = "Starting Soon"
nxt = 1



def release_mass(players):

	for player in players:
		p = players[player]
		if p["score"] > 8:
			p["score"] = math.floor(p["score"]*0.95)


def check_collision(players, balls):
	
	to_delete = []
	for player in players:
		p = players[player]
		x = p["x"]
		y = p["y"]
		for ball in balls:
			bx = ball[0]
			by = ball[1]

			dis = math.sqrt((x - bx)**2 + (y-by)**2)
			if dis <= START_RADIUS + p["score"]:
				p["score"] = p["score"] + 0.5
				balls.remove(ball)


def player_collision(players):
	
	sort_players = sorted(players, key=lambda x: players[x]["score"])
	for x, player1 in enumerate(sort_players):
		for player2 in sort_players[x+1:]:
			p1x = players[player1]["x"]
			p1y = players[player1]["y"]

			p2x = players[player2]["x"]
			p2y = players[player2]["y"]

			dis = math.sqrt((p1x - p2x)**2 + (p1y-p2y)**2)
			if dis < players[player2]["score"] - players[player1]["score"]*0.85:
				players[player2]["score"] = math.sqrt(players[player2]["score"]**2 + players[player1]["score"]**2) # adding areas instead of radii
				players[player1]["score"] = 0
				players[player1]["x"], players[player1]["y"] = get_start_location(players)
				print(f"[GAME] " + players[player2]["name"] + " ATE " + players[player1]["name"])


def create_balls(balls, n):
	
	for i in range(n):
		while True:
			stop = True
			x = random.randrange(0,W)
			y = random.randrange(0,H)
			for player in players:
				p = players[player]
				dis = math.sqrt((x - p["x"])**2 + (y-p["y"])**2)
				if dis <= START_RADIUS + p["score"]:
					stop = False
			if stop:
				break

		balls.append((x,y, random.choice(colors)))


def get_start_location(players):
	
	while True:
		stop = True
		x = random.randrange(0,W)
		y = random.randrange(0,H)
		for player in players:
			p = players[player]
			dis = math.sqrt((x - p["x"])**2 + (y-p["y"])**2)
			if dis <= START_RADIUS + p["score"]:
				stop = False
				break
		if stop:
			break
	return (x,y)


def threaded_client(conn, _id):

	global connections, players, balls, game_time, nxt, start


	data = conn.recv(16)
	name = data.decode("utf-8")
	print("[LOG]", name, "connected to the server.")

	color = colors[current_id]
	x, y = get_start_location(players)
	players[current_id] = {"x":x, "y":y,"color":color,"score":0,"name":name}  


	conn.send(str.encode(str(current_id)))

	while True:

		if start:
			game_time = round(time.time()-start_time)
		
			if game_time >= ROUND_TIME:
				start = False
			else:
				if game_time // MASS_LOSS_TIME == nxt:
					nxt += 1
					release_mass(players)
					print(f"[GAME] {name}'s Mass depleting")
		try:
			data = conn.recv(32)

			if not data:
				break

			data = data.decode("utf-8")
			
			if data.split(" ")[0] == "move":
				split_data = data.split(" ")
				x = int(split_data[1])
				y = int(split_data[2])
				players[current_id]["x"] = x
				players[current_id]["y"] = y

				if start:
					check_collision(players, balls)
					player_collision(players)

				if len(balls) < 150:
					create_balls(balls, random.randrange(100,150))
					print("[GAME] Generating more orbs")

				send_data = pickle.dumps((balls,players, game_time))

			elif data.split(" ")[0] == "id":
				send_data = str.encode(str(current_id)) 

			elif data.split(" ")[0] == "jump":
				send_data = pickle.dumps((balls,players, game_time))
			else:
				send_data = pickle.dumps((balls,players, game_time))
			conn.send(send_data)

		except Exception as e:
			print(e)
			break  

		time.sleep(0.001)

	print("[DISCONNECT] Name:", name, ", Client Id:", current_id, "disconnected")

	connections -= 1 
	del players[current_id]  
	conn.close()
create_balls(balls, random.randrange(200,250))

print("[GAME] Setting up level")
print("[SERVER] Waiting for connections")


while True:
	
	host, addr = S.accept()
	print("[CONNECTION] Connected to:", addr)

	if addr[0] == SERVER_IP and not(start):
		start = True
		start_time = time.time()
		print("[STARTED] Game Started")


	connections += 1
	start_new_thread(threaded_client,(host,_id))
	_id += 1
print("[SERVER] Server offline")