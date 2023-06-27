let socket = io.connect("http://" + document.domain + ":" + location.port)

// loadParaTable()

socket.on("connect", () => {
	console.log("CONNECTED")
	socket.emit("request_sync_data")
})

socket.on("sync_data", (data) => {
	syncData(data.arduino)
	setPowerState(data.power_state == true ? "Power is ON" : "Power is OFF")
})

socket.on("status", (status) => {
	$("#status").text(status)
})

socket.on("ttfis_data", (ttfis_data) => {
	updateTtfiData(ttfis_data)
})
socket.on("response_from_arduino", (response) => {
	setArduinoRelayButtonStateAndColor(response)
})

socket.on("lock", (locked) => {
	setLock(locked)
})
