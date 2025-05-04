'''
    Script con servidor web que usa como base Redis
    para jugar a las damas a través de la web
'''

from quart import Quart, render_template, request, jsonify, websocket
import redis.asyncio # Usamos redis asíncrono
import redis.exceptions
import hypercorn.utils
from enum import Enum
import asyncio
import uuid
import json 
import random
from game import *

app = Quart(__name__)

redisHost = "127.0.0.1"
redisPort = 6379

serverHost = "0.0.0.0"
serverPort = 5000

# Inicializa el servidor web
@app.while_serving
async def lifespan():
    # Abrimos el cliente con Redis
    app.client: redis.Redis = redis.asyncio.Redis(
        host=redisHost, 
        port=redisPort,
        socket_connect_timeout=1,
        decode_responses=True
    )

    # Comprobamos que este activo Reddis
    await app.client.ping()
    await app.client.flushdb()

    # Corremos el servicio para manejar lógica de partidas
    app.add_background_task(matchEventQueue, app.client)

    yield

# Pagina web principal
@app.get("/")
async def index():
    return await render_template("index.html")

# Endpoint para manejar el crear partidas
@app.post("/create")
async def startGame():
    data = await request.get_json()

    # Aseguramos que la peticion tenga los campos correctos
    if data is None: return jsonify({"msg": "Invalid petition"}), 400
    user = data.get("name", None)
    if user is None: return jsonify({"msg": "Invalid petition"}), 400

    # Creamos una id de usuario única
    userId = f"user:{uuid.uuid4()}"

    # Creamos una sesión temporal y la guardamos en Redis
    await app.client.hset(userId, "name", user)
    await app.client.hset(userId, "connection", "waiting")

    # Id de la partida
    match = f"match:{uuid.uuid4()}"
    print(f"Creating {match}")

    # Tablero partida
    board = createCheckersBoard()
    p1n, p2n, p1q, p2q = encodeBoard(board)

    # Guardamos los datos de la partida en Redis
    await app.client.hset(match, "type", "match")
    await app.client.hset(match, "p1n", p1n)
    await app.client.hset(match, "p2n", p2n)
    await app.client.hset(match, "p1q", p1q)
    await app.client.hset(match, "p2q", p2q)
    await app.client.hset(match, "state", "waiting")

    if random.randint(0, 1): await app.client.hset(match, "p1", userId)
    else: await app.client.hset(match, "p2", userId)

    # Generamos el codigo de la partida
    while True:
        s = "ABCDEFGHIKJLMNOPQRSTUVWXYZ0123456789"
        code = "match:code:" + "".join(random.choices(s, k=6))
        
        # Nos aseguramos que el codigo sea único
        if await app.client.set(code, match, nx=True):
            await app.client.hset(match, "code", code)
            break

    # Asociar partida al jugador
    await app.client.hset(userId, "match", match)

    # Hacemos que las sesiones duren poco hasta que 
    # no se verifiquen que juegue una partida
    await app.client.expire(userId, 2)

    # Enviamos un mensaje de posible desconexión del cliente para dentro de 3 segs
    await sendQueueMsg(app.client, {
        "type": "disconnect",
        "match": match,
        "user": userId
    }, "match:queue", 3)

    # Devolvemos el token te autorización al cliente
    return jsonify({"token": userId})

# Endpoint para manejar el unirse a partidas
@app.post("/join")
async def joinGame():
    data = await request.get_json()

    # Aseguramos que la peticion tenga los campos correctos
    if data is None: return jsonify({"msg": "Invalid petition"}), 400

    user = data.get("name", None)
    code = data.get("code", None)

    if user is None: return jsonify({"msg": "Invalid petition"}), 400
    if code is None: return jsonify({"msg": "Invalid petition"}), 400

    # Buscamos si la partida asociada existe y si es valida
    match = await app.client.get(f"match:code:{code}")
    if match is None: return jsonify({"msg": "Invalid match code"}), 404
    if await app.client.hget(match, "state") != "waiting": return jsonify({"msg": "Match is invalid"}), 403  

    # Creamos una id de usuario única
    userId = f"user:{uuid.uuid4()}"

    # Introducimos al jugador en la partida
    p1, p2 = await app.client.hmget(match, ["p1", "p2"])
    if p1 is None and p2 is None: return jsonify({"msg": "Match is invalid"}), 403  

    if p1 is None:
        await app.client.hset(match, "p1", userId)
    else:
        await app.client.hset(match, "p2", userId)

    # Creamos una sesión temporal
    await app.client.hset(userId, "name", user)
    await app.client.hset(userId, "connection", "waiting")
    await app.client.hset(userId, "match", match)

    # Hacemos que las sesiones duren poco hasta que 
    # no se verifiquen que juegue una partida
    await app.client.expire(userId, 2)

    # Enviamos un mensaje de posible desconexión del cliente para dentro de 3 segs
    await sendQueueMsg(app.client, {
        "type": "disconnect",
        "match": match,
        "user": userId
    }, "match:queue", 3)

    return jsonify({"token": userId})

# Endpoint para la página de las partidas
@app.get("/match")
async def match():
    return await render_template("match.html")

# Esta tarea se ejecuta en segundo plano y consiste en una cola
# de eventos de todas las partidas activas en la Redis
async def matchEventQueue(client: redis.Redis):
    while True:
        # Obtenemos el mensaje y vemos de quién, qué partida es y el tipo de mensaje
        message = await getQueueMsg(client, "match:queue")
        
        type = message.get("type", None)
        match = message.get("match", None)
        user = message.get("user", None)

        # Comprobamos que sea válido
        if type is None or match is None or user is None:
            continue
    
        # Mensaje recibido tras la desconexión de un usuario
        if type == "disconnect":

            # Comprobamos que el usuario verdaderamente se haya desconetado
            if await client.exists(user): continue

            # Vemos cual de los usuarios se ha desconectado para notificarselo al otro
            p1, p2 = await client.hmget(match, ["p1", "p2"])
            if p1 == user:
                # Borramos al usuario de la partida
                await client.hdel(match, "p1")
                p1 = None

                if p2 is not None:
                    # Enviamos un mensaje de desconexión al otro usuario por medio de una cola de eventos
                    await sendQueueMsg(client, {"type": "player-disconnect"}, f"{p2}:queue")

            if p2 == user:
                # Borramos al usuario de la partida
                await client.hdel(match, "p2")
                p2 = None

                if p1 is not None:
                    # Enviamos un mensaje de desconexión al otro usuario por medio de una cola de eventos
                    await sendQueueMsg(client, {"type": "player-disconnect"}, f"{p1}:queue");

            # Comprobamos que siga habiendo usuario en la partida si no la borramos
            if p1 is None and p2 is None:
                print(f"Closing {match}")
                entry = [match]

                # Si el codigo de la partida sigue existiendo tambien lo borramos
                code = await client.hget(match, "code")
                if code is not None: entry.append(code)

                await client.delete(*entry)


# Funciónn que interna que manda mensajes a colas de eventos.
async def __sendQueueMsg(client, data, queue, timer):
    # Segundos a esperar
    if timer != 0: await asyncio.sleep(timer)

    # Generamos una id para el mensaje
    msgID = f"match:{queue}:{uuid.uuid4()}"

    # Creamos una clave con los datos del mensaje
    await client.hset(msgID, mapping=data)

    # Los mensajes tendrán una vida máxima
    await client.expire(msgID, 5)

    # Añadimos la id del mensaje a la cola
    await client.lpush(queue, msgID)

# Función que manda mensajes a colas de eventos. Tambien permite programarlos para que se 
# envien pasados unos segundos
async def sendQueueMsg(client, data, queue, timer = 0):

    # Creamos una tarea aparte que ejecute la accción para no afectar al bucle principal
    asyncio.create_task(__sendQueueMsg(client, data, queue, timer))

# Función que lee activamente mensajes de una cola
async def getQueueMsg(client: redis.Redis, queue):
    while True:
        # Esperamos que haya algún elemento en la cola
        # por medio de espera bloqueante
        msgID = await client.brpop(queue)
        msgKey = msgID[1]
        
        # Obtenemos el mensaje y lo borramos de Redis
        data = await client.hgetall(msgKey)
        if data is not None:
            await client.delete(msgKey)
            return data

# Función de utilidad que dado un match devuelve el estado del tablero decodificado
async def getBoard(client, match):
    res =  await client.hmget(match, ["p1n", "p2n", "p1q", "p2q"])
    res = list(map(int, res))
    return decodeBoard(*res)

# Función de utilidad que se encargar de enviar
# el estado del tablero a los jugadores
async def broadcastBoard(client, match):
    # Leemos el tablero
    p1, p2, p1n, p2n, p1q, p2q =  await client.hmget(match, ["p1", "p2", "p1n", "p2n", "p1q", "p2q"])
    
    data = {
        "type": "show-board",
        "p1n": p1n,
        "p2n": p2n,
        "p1q": p1q,
        "p2q": p2q,
    }

    # Enviamos el tablero a los jugadores
    if p1 is not None:
        data["player"] = "p1"
        await sendQueueMsg(client, data, f"{p1}:queue")
    if p2 is not None:
        data = data.copy()
        data["player"] = "p2"
        await sendQueueMsg(client, data, f"{p2}:queue")

# Corrutina que se encargar de leer mensajes de una cola de cliente
# para enviarlos por medio de un websocket
async def socketSender(client, token):
    while True:
        data = await getQueueMsg(client, f"{token}:queue")
        await websocket.send(json.dumps(data))

# Corrutina que se encargar de leer mensajes enviados
# por el websocket del cliente
async def socketReceiver(client, token):

    # Cargamos el codigo de partida y los de los jugadores
    match = await client.hget(token, "match")
    p1, p2 = await client.hmget(match, ["p1", "p2"])

    # Determinamos que jugador es
    player = None
    if p1 == token:
        player = "p1"
    elif p2 == token:
        player = "p2"

    sgn = 2 * (player == "p2") - 1

    # Bucle principal
    while True:
        # Esperamos recibir datos
        data = await websocket.receive()

        # Si no teníamos alguno de los dos jugadores lo obtenemos
        if p1 is None: p1 = await client.hget(match, "p1")
        if p2 is None: p2 = await client.hget(match, "p2")

        # Cargamos el json con el mensaje del websocket
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            continue
        print(data)

        type = data.get("type", None)

        # El usuario ha pulsado una ficha. Si puede moverla le mandamos los movimientos posibles
        if type == "clicked" and await client.hget(match, "state") == player:

            # Obtenemos los datos
            x = int(data["x"])
            y = int(data["y"])
            board = await getBoard(client, match)

            # Verificamos que la ficha sea del jugador
            if board[y][x] * sgn > 0:
                # Obtenemos los movimientos posibles y los codificamos
                moves = getPossibleMoves(board, x, y, sgn)
                movesEncoded = encodeMoves(*moves)

                # Solo enviamos si existen movimientos posibles
                if movesEncoded != 0:
                    await sendQueueMsg(client, {"type": "moves", "moves": movesEncoded, "x": x, "y": y}, f"{token}:queue")

        # El jugador quiere mover una ficha                    
        elif type == "move" and await client.hget(match, "state") == player:

            # Obtenemos los datos
            dx = int(data["dx"])
            dy = int(data["dy"])
            ox = int(data["ox"])
            oy = int(data["oy"])

            # Obtenemos los movimientos posibles
            moves = getPossibleMoves(board, ox, oy, sgn)
            for mx, my in moves:
                # Comprobamos si el movimiento existe
                if mx == dx and my == dy:

                    # Ejecutamos el movimiento
                    board, eat = move(board, ox, oy, dx, dy)
                    p1n, p2n, p1q, p2q = encodeBoard(board)

                    # Actualizamos los datos
                    await app.client.hset(match, "p1n", p1n)
                    await app.client.hset(match, "p2n", p2n)
                    await app.client.hset(match, "p1q", p1q)
                    await app.client.hset(match, "p2q", p2q)
                    await broadcastBoard(client, match)

                    # Comprobamos si alguien ha ganado
                    winner = win(board)
                    if winner != 0:
                        # Notificamos a los usuarios sobre el final de la partida
                        await sendQueueMsg(client, {"type": "end", "winner": int("p1" == player)}, f"{p1}:queue")
                        await sendQueueMsg(client, {"type": "end", "winner": int("p2" == player)}, f"{p2}:queue")
                        return

                    # Si el movimiento no ha sido comer una pieza cambiamos los turnos
                    if not eat:
                        l = ["p1", "p2"]
                        await app.client.hset(match, "state", l[player == "p1"])

                    # Enviamos el nuevo turno a los jugadores
                    if player == "p1":
                        await sendQueueMsg(client, {"type": "turn", "who": int(eat)}, f"{p1}:queue")
                        await sendQueueMsg(client, {"type": "turn", "who": int(not eat)}, f"{p2}:queue")
                    else:
                        await sendQueueMsg(client, {"type": "turn", "who": int(not eat)}, f"{p1}:queue")
                        await sendQueueMsg(client, {"type": "turn", "who": int(eat)}, f"{p2}:queue")

# End point que permite a los usuarios conectarse
# con un websocket por medio del token suministrado
# previamente
@app.websocket("/<string:token>/ws")
async def ws(token: str):

    # Verificamos que el token sea valido
    if len(token) <= 4 or token[:4] != "user" or not await app.client.exists(token):
        response = {
            "type": "bad-auth",
            "msg": "The token is invalid."
        }
        await websocket.send(json.dumps(response)), 403
        return

    # La sessión ya está activa. No puede haber duplicados
    if await app.client.hget(token, "connection") == "active":
        response = {
            "type": "bad-auth",
            "msg": "Already logged in."
        }
        await websocket.send(json.dumps(response)), 403
        return        

    try:
        # Aceptamos el websocket y prolongamos la duración de la sesión a 1h
        await websocket.accept()
        await app.client.expire(token, 3600)
        await app.client.hset(token, "connection", "active")

        # Enviamos al cliente que todo está correcto
        response = {
            "type": "ok-auth",
            "msg": "You are logged in."
        }
        await websocket.send(json.dumps(response))
    
        # Enviamos información del tablero y el código de la partida
        match = await app.client.hget(token, "match");
        code = (await app.client.hget(match, "code")).split(":")[-1];
        await broadcastBoard(app.client, match)
        await sendQueueMsg(app.client, {"type": "waiting-player", "code": code}, f"{token}:queue")

        # Obtenemos los dos jugadores de la partida y vemos que jugador es el cliente
        p1, p2, matchState = await app.client.hmget(match, ["p1", "p2", "state"]);
        if p1 == token: player = "p1"
        else: player = "p2"

        # Comprobamos si la partida debería de empezar
        if p1 is not None and p2 is not None and matchState == "waiting":
            
            # Obtenemos los nombres de los jugadores
            p1Name = await app.client.hget(p1, "name");
            p2Name = await app.client.hget(p2, "name");
            
            # Cambiamos el estado de la partida
            await app.client.hset(match, "state", "p1");

            # Enviamos a los jugadores que la partida ya ha comenzado
            await sendQueueMsg(app.client, {"type": "match-start", "oponnentName": p2Name, "player": "p1"}, f"{p1}:queue")
            await sendQueueMsg(app.client, {"type": "match-start", "oponnentName": p1Name, "player": "p2"}, f"{p2}:queue")
        
        # La partida ya ha comenzado y se trata de una reconexión como por ejemplo presiona F5.
        elif matchState == "p1" or matchState == "p2":

            # Obtenemos los nombres de los jugadores
            p1Name = await app.client.hget(p1, "name");
            p2Name = await app.client.hget(p2, "name");

            # Enviamos que la partida ha comenzado al jugador y de quién es el turno
            await sendQueueMsg(app.client, {
                "type": "match-start", 
                "oponnentName": p1Name if player == "p2" else p2Name, "player": player
            }, f"{token}:queue")

            await sendQueueMsg(app.client, {"type": "turn", "who": int(matchState == player)}, f"{token}:queue")

        # Arrancamos las corrutinas para la comunicación entre Redis-Cliente 
        # por medio de los websockets y las colas de eventos
        receiver = asyncio.create_task(socketReceiver(app.client, token))
        sender = asyncio.create_task(socketSender(app.client, token))
        await asyncio.gather(sender, receiver)

    # El socket se ha cerrado
    except asyncio.CancelledError:
        print(f"Exiting {token}")

        # Cerramos explícitamente el socket
        await websocket.close(200)

        # Expiramos la sesión del usario en 2 segundos si no se reconecta
        await app.client.hset(token, "connection", "waiting")
        await app.client.expire(token, 2)

        # Enviamos un mensaje de desconexión del usuario en 3 segundos
        match = await app.client.hget(token, "match")
        if match is not None:
            await sendQueueMsg(app.client, {
                "type": "disconnect",
                "match": match,
                "user": token
            }, "match:queue", 3)

if __name__ == "__main__":
    try:
        # Arrancamos el servidor
        app.run(debug=False, host=serverHost, port=serverPort)
    except hypercorn.utils.LifespanFailureError:
        print(f"\33[31m\33[1mERROR\33[0m No se ha podido establecer conexión con redis en {redisHost}:{redisPort}.")
        exit(-1)
