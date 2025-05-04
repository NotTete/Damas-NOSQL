/*
    Script que contiene lógica para los botones del menu principal
    Autor: Jorge Hernández Palop
*/


const createButton = document.getElementById("createButton");
const joinButton = document.getElementById("joinButton");
const nameInput = document.getElementById("playerName");
const codeInput = document.getElementById("gameCode");

const endpoint = `${window.location.protocol}//${window.location.host}`;

const errorTextDiv = document.getElementById("errorText");
var errorTimerFunc = null;

// Vuelve invisible el mensaje de error
function clearErrogMsg() {
    errorTextDiv.classList.add("opacity-0");
    errorTimerFunc = null;
}

// Muestra un mensaje de error temporalmente
function setErrorMsg(msg) {
    if (errorTimerFunc != null) {
        clearTimeout(errorTimerFunc);
    }

    errorTextDiv.innerHTML = msg;
    errorTextDiv.classList.remove("opacity-0");
    errorTimerFunc = setTimeout(clearErrogMsg, 2000);
}

// Callback para el botón de crear partida
createButton.addEventListener('click', async function() {
    const name = nameInput.value;
    let sessionToken = null;

    if (name == "") {
        setErrorMsg("You must have a name");
        return;
    }

    // Le pedimos autentificación al servidor
    const response = await fetch(endpoint + "/create", {
        method: "POST",
        body: JSON.stringify({ name: name }),
        headers: {
            "Content-type": "application/json; charset=UTF-8"
        }
    });

    const data = await response.json();

    if (!response.ok) {
        const msg = `Error ${response.status}: ${data.msg}`
        setErrorMsg(msg);
        console.error(msg);
        return;
    }

    sessionToken = data["token"];
    if (sessionToken == null) {
        const msg = `Bad response: Token not found`
        setErrorMsg(msg);
        console.error(msg);
        return;
    }
    

    // Guardamos el token y nos conectamos a la partida
    sessionStorage.setItem("token", sessionToken);
    window.location.href = '/match'; 
});

// Callback para el botón de unirse a una partida
joinButton.addEventListener('click', async function() {
    const name = nameInput.value;
    const code = codeInput.value;
    let sessionToken = null;

    if (name == "") {
        setErrorMsg("You must have a name");
        return;
    }

    if (code == "") {
        setErrorMsg("You must insert a code");
        return;
    }

    // Nos autentificamos con el servidor
    const response = await fetch(endpoint + "/join", {
        method: "POST",
        body: JSON.stringify({ name: name, code: code }),
        headers: {
            "Content-type": "application/json; charset=UTF-8"
        }
    });

    const data = await response.json();

    if (!response.ok) {
        const msg = `Error ${response.status}: ${data.msg}`
        setErrorMsg(msg);
        console.error(msg);
        return;
    }

    sessionToken = data["token"];
    if (sessionToken == null) {
        const msg = `Bad response: Token not found`
        setErrorMsg(msg);
        console.error(msg);
        return;
    }

    // Guardamos el token y nos conectamos a la partida
    sessionStorage.setItem("token", sessionToken);
    window.location.href = '/match'; 
});