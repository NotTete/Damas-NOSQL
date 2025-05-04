/*
    Script que contiene par la comunicación 
    cliente-servidor por medio de web sockets

    Autor: Jorge Hernández Palop
*/

import {drawBoard, decodeBoard, decodeMoves, drawMoves} from "./board.js";

const token = sessionStorage.getItem("token")

const ws = new WebSocket(`ws://${window.location.host}/${token}/ws`, );
const mainDiv = document.getElementById("main-div");
const endpoint = `${window.location.protocol}//${window.location.host}`;

const canvas = document.getElementById("boardCanvas");
const ctx = canvas.getContext("2d");


let board = null; // Estado de tablero
let lastX = null; // Ultima coordenada X valida pulsada
let lastY = null; // Ultima coordenada Y valida pulsada
let moves = null; // Lista de movimientos posibles

let player = null; // Indica si eres el jugador "p1" o "p2"
let currentTurn = false; // Indica el turno

// Actualiza para la página para mostrar un error de autentificación
function handleBadAuth(data) {
    console.error(data.msg);
    ws.close();

    mainDiv.innerHTML = `
        <h1 class="fw-bold"><a href="/">Bad Authentification</a></h1>
        <h2><a href="/">${data.msg}</a></h2>
        <h1 class="mt-3"><a href="/">(╯°o°）╯︵ ┻━┻</a></h1>
    `;
}

// Actualiza para la página para mostrar una pantalla de victoria o derrota
function endGame(isWin, msg) {
    ws.close();
    let text = "You win";
    let emoji = "(づ｡◕‿‿◕｡)づ";

    if (!isWin) {
        text = "You lose";
        emoji = "(╯°o°）╯︵ ┻━┻";
    }

    mainDiv.innerHTML = `
        <h1 class="fw-bold"><a href="/">${text}</a></h1>
        <h2><a href="/">${msg}</a></h2>
        <h1 class="mt-3"><a href="/">${emoji}</a></h1>
    `;

    setTimeout(() => {
        setTimeout(function(){ window.location.href = endpoint; }, 5000);
    });
}

// Bucle principal del websocket donde se reciben mensajes
ws.addEventListener('message', function (event) {
    let data = JSON.parse(event.data);
    console.log(data);

    // Mala autorización
    if (data.type == "bad-auth") {
        handleBadAuth(data);
        return;
    
    // Mostrar el tablero
    } else if (data.type == "show-board") {
        board = decodeBoard(data);
        drawBoard(ctx, canvas.width, canvas.height, board.pieces, board.reverse);


    // Estado de esperar jugadores
    } else if (data.type == "waiting-player") {
        const elem = document.getElementById("status-div");
        elem.innerHTML = "<h2>Waiting for players...</h2>";
        let h = document.createElement("h2");
        h.id = "bottom-h2";
        h.innerHTML = `Room code: <b>${data.code}</b>`;
        mainDiv.append(h);

    // Final de la partida
    } else if (data.type == "end") {
        if (data.winner != "0") {
            endGame(true, "Congratulations for your victory!");
        } else {
            endGame(false, "Better luck next time...");
        }
        return;

    // Desconexión de la partida
    } else if (data.type == "player-disconnect") {
        endGame(true, "Your opponent disconnected");
        return;

    // Estado de iniciar la partida
    } else if (data.type == "match-start") {
        let elem = document.getElementById("status-div");
        elem.innerHTML = `<h2>Opponent: <b>${data.oponnentName}</b></h2>`;
        
        player = data.player;

        elem = document.getElementById("bottom-h2");
        if (player == "p1") {
            elem.innerHTML = "<b>Your turn</b>";
            currentTurn = true;
        } else {
            elem.innerHTML = "<b>Opponent's turn</b>";
        }

    // Mostrar movimientos posibles
    } else if(data.type == "moves") {
        moves = decodeMoves(data.moves);
        lastX = data.x;
        lastY = data.y;
        
        drawBoard(ctx, canvas.width, canvas.height, board.pieces, board.reverse);
        drawMoves(ctx, canvas.width, canvas.height, moves, board.reverse);

    // Cambio de turno
    } else if(data.type == "turn") {
        let who = data.who
        let elem = document.getElementById("bottom-h2");
        if (who == 1) {
            elem.innerHTML = "<b>Your turn</b>";
            currentTurn = true;
        } else {
            elem.innerHTML = "<b>Opponent's turn</b>";
            currentTurn = false;
        }
    }
});


// Eventos del canvas que envían mensajes al servidor
canvas.addEventListener('click', async function(event) {
    if(currentTurn) {
        var x = event.pageX - canvas.offsetLeft,
            y = event.pageY - canvas.offsetTop;
            console.log(x, y);
        x = Math.floor(x * 8 / canvas.width);
        y = Math.floor(y * 8 / canvas.height);
        
        // Invertir tablero para el jugador 2
        if (player == "p2") {
            x = 7 - x;
            y = 7 - y;
        }

        // Redibujamos el tablero
        drawBoard(ctx, canvas.width, canvas.height, board.pieces, board.reverse);

        // Vemos si el movimiento que hemos hecho es valido y lo confirmamos con el servidor para movernos
        if (moves != null) {
            for(let i = 0; i < moves.length; i++) {
                if(x == moves[i].x && y == moves[i].y) {
                    ws.send(JSON.stringify({"type": "move", "dx": x, "dy": y, "ox": lastX, "oy": lastY}));
                    lastX = null; lastY = null; moves = null;
                    currentTurn = false;
                    drawBoard(ctx, canvas.width, canvas.height, board.pieces, board.reverse);
                    return;
                }
            }
        }
        
        // Preguntamos al servidor por movimientos o los quitamos segun si clickeamos en la misma
        // pieza o no
        if (lastX != x || lastY != y) {
            console.log(x, y);
            ws.send(JSON.stringify({"type": "clicked", "x": x, "y": y}));
        } else {
            lastX = null; lastY = null; moves = null;
            drawBoard(ctx, canvas.width, canvas.height, board.pieces, board.reverse);
        }
    }
});

