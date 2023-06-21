const socket = io.connect("http://" + document + ":" + location.port)

socket.on("connect", () => {
	socket.emit("get_sync_data")
})

socket.on("set_sync_data", (data) => {
	setHardWarebuttonsStateAndColor(data)
})

socket.on("current_power", (current_state) => {
	setHardWarebuttonsStateAndColor(current_state)
})
