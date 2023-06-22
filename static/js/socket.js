let socket = io.connect("http://" + document.domain + ":" + location.port)

loadParaTable()

socket.on("connect", () => {
	console.log("CONNECTED")
	socket.emit("get_sync_data")
})

socket.on("set_sync_data", (data) => {
	console.log(data)
	syncData(data)
})

socket.on("status", (status) => {
	console.log(status)
	$("#status").text(status)
})

socket.on("update_data_to_client", (data) => {
	let voltage = data.voltage
	let current = data.current
	$("#voltage").text(voltage)
	$("#current").text(current)
	if (voltage == 0 && current == 0) setCurrentPowerState("power_off")
	else if (voltage > 0 && current > 0) setCurrentPowerState("normal")
	else if (voltage > 0 && current == 0) setCurrentPowerState("stand_by")
})
socket.on("ttfis_data", (ttfis_data) => {
	updateTtfiData(ttfis_data)
})
