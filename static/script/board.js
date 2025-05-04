/*
    Script que contiene lógica para dibujar tableros
    Autor: Jorge Hernández Palop
*/

const endpoint = `${window.location.protocol}//${window.location.host}`;


// Representa una pieza del tablero
export class Piece {
    constructor(x, y, isWhite, isQueen = false) {
        this.x = x;
        this.y = y;
        this.color =  isWhite ? "Crimson" : "CornflowerBlue";
        this.isQueen = isQueen;
    }
};

// Dibuja la cuadrícula del tablero
function drawBoardBase(ctx, width, height, reverse = false) {

    let dx = width / 8;
    let dy = height / 8;

    let fillColors = ["white", "black"];
    for (let i = 0; i < 8; i++) {
        for(let j = 0; j < 8; j++) {
            ctx.fillStyle=fillColors[(i + j) % 2];
            ctx.fillRect(i * dx, j * dy, dx, dy);
        }
    }

    ctx.lineWidth = 2;
    ctx.strokeStyle="black";
    ctx.strokeRect(0, 0, width, height)
}


// Dibuja una pieza en el tablero
function drawPiece(ctx, width, height, piece, reverse) {

    let dx = width / 8;
    let dy = height / 8;
    
    let x = piece.x;
    let y = piece.y;

    if (reverse) {
        x = 7 - x;
        y = 7 - y;
    }
        
    let px = dx * (0.5 + x);
    let py = dy * (0.5 + y);

    let factor = 0.75;
    let rx = dx / 2 * factor;
    let ry = dy / 2 * factor;


    ctx.beginPath();
    ctx.ellipse(px, py, rx, ry, 0, 0, Math.PI * 2);
    ctx.fillStyle = piece.color;
    ctx.fill();
    ctx.strokeStyle = piece.color != "Crimson" ? "#286ce6" : "#b01030";
    ctx.lineWidth = 10;
    ctx.stroke();

    if (piece.isQueen) {
        let factor = 0.5;
        let qx = dx * factor;
        let qy = dy * factor;
        
        px = dx * x + (dx - qx) / 2;
        py = dx * y + (dy - qy) / 2;
        ctx.drawImage(crown, px, py, qx, qy);
    }
}

// Dibujas una lista de posibles movimientos que puede hacer el jugador
export function drawMoves(ctx, width, height, moves, reverse) {
    moves.forEach(move => {
        drawMove(ctx, width, height, move.x, move.y, reverse);
    });
}

// Dibuja un solo movimiento
function drawMove(ctx, width, height, x, y, reverse) {

    let dx = width / 8;
    let dy = height / 8;

    if (reverse) {
        x = 7 - x;
        y = 7 - y;
    }
        
    x = dx * (0.5 + x);
    y = dy * (0.5 + y);

    let factor = 0.25;
    let rx = dx / 2 * factor;
    let ry = dy / 2 * factor;

    ctx.beginPath();
    ctx.ellipse(x, y, rx, ry, 0, 0, Math.PI * 2);
    ctx.fillStyle = reverse ? "#b01030" : "#286ce6";
    ctx.fill();
}

// Dibuja todo el tablero
export function drawBoard(ctx, width, height, pieces, reverse = false) {
    drawBoardBase(ctx, width, height, reverse);
    pieces.forEach(piece => {
        drawPiece(ctx, width, height, piece, reverse);
    });
}

// Decodifica los movimientos que se pueden hacer
export function decodeMoves(moves) {
    let res = [];
    for(let i = 0; i < 32; i++) {
        let j = 2 * i;
        let y = Math.floor(j / 8);
        let x = j % 8 + (y % 2 == 1);
        if(moves & (1 << i)) res.push({x:x, y:y});
    }
    return res;
}

// Decodifica los datos del tablero
export function decodeBoard(data) {

    let p1n = parseInt(data.p1n);
    let p2n = parseInt(data.p2n);
    let p1q = parseInt(data.p1q);
    let p2q = parseInt(data.p2q);
    let reverse = data.player == "p2";
    
    let pieces = [];

    for(let i = 0; i < 32; i++) {
        let j = 2 * i;
        let y = Math.floor(j / 8);
        let x = j % 8 + (y % 2 == 1);
        
        if(p1n & (1 << i)) pieces.push(new Piece(x, y, true, false));
        if(p2n & (1 << i)) pieces.push(new Piece(x, y, false, false));
        if(p1q & (1 << i)) pieces.push(new Piece(x, y, true, true));
        if(p2q & (1 << i)) pieces.push(new Piece(x, y, false, true));
    }

    return {pieces: pieces, reverse: reverse};
}

const crown = new Image();
crown.src = `${endpoint}/static/img/crown.svg`;