$(document).ready(function () {
	var sccLines = []
	var socket = io.connect("http://" + document.domain + ":" + location.port)
	var volValue = $("#volValue")
	var curValue = $("#curValue")
	var volValueToSet = $("#pwrVal_in")
	var serverStatus = $("#serverStatus")
	var sourceStatus = $("#sourceStatus")
	var setPwrBtn = $("#setPwr_btn")
	var popupStatus = $("#popupStatus")
	var popupTitle = $("#popupTitle")
	var commandEntry = $("#entry-zone")
	var executeBtn = $("#execute_btn")

	var isPwrSourceConnected = false

	socket.on("connect", function () {
		serverStatus.text("Connected")
	})

	socket.on("message", function (message_) {
		let bIsAtBottom = true
		let traceArea = $("#log_ttfis")[0]

		if (traceArea.scrollHeight > traceArea.clientHeight + traceArea.scrollTop) {
			bIsAtBottom = false
		}

		$scope.$apply(function () {
			let lines = sccLines.concat(message_.split("\n"))
			sccLines = lines
		})

		if (bIsAtBottom) {
			traceArea.scrollTop = traceArea.scrollHeight - traceArea.clientHeight
		}
	})

	socket.on("disconnect", function () {
		serverStatus.text("Disconnected")
	})

	socket.on("powervalue", function (data) {
		volValue.text(data["voltage"])
		curValue.text(data["current"])
	})

	socket.on("sourceStatus", function (data) {
		sourceStatus.text(data)
		if (data == "Power ON") {
			isPwrSourceConnected = true
		} else {
			isPwrSourceConnected = false
		}
	})

	socket.on("status", function (data) {
		openAlert("Status", data)
	})

	socket.on("setVolValue", function (data) {
		socket.emit("setVolValue", data)
	})

	$("#command-input").on("keydown", function (event) {
		if (event.keyCode == 13) {
			var command = $(this).val().replace(">", "")
			$(this).val(">")
			$("#command-area").append($("<div>").text(command))
			socket.emit("command", command)
			socket.emit("powervalue", command)
		}
	})
	setPwrBtn.click(function () {
		console.log("set")
		var voltage = 0
		if (isPwrSourceConnected == true) {
			if (volValueToSet.val() != "") {
				voltage = parseInt(volValueToSet.val())
				console.log(voltage)
				if (voltage >= 0 && voltage <= 14) {
					voltage = voltage
					openAlert(
						"Set power voltage SUCCESS",
						"Voltage now is " + volValueToSet.val(),
					)
				}
			} else {
				voltage = 0
				openAlert(
					"Set power voltage ERROR",
					"Voltage is INVALID MUST BETWEEN 0-14V!!",
				)
			}
			socket.emit("setVolValue", voltage)
			volValueToSet.val("")
		} else {
			openAlert("Set power voltage ERROR", "Power source is not CONNECTED")
		}
	})

	var popupBox = document.getElementById("popup_box")

	openAlert = (_title, _status) => {
		popupBox.style.display = "block"
		popupBox.style.visibility = "visible"
		popupTitle.text(_title)
		popupStatus.text(_status)
	}

	document
		.getElementById("closePopup_btn")
		.addEventListener("click", function () {
			popupBox.style.display = "none"
			popupBox.style.visibility = "hidden"
		})

	commandEntry.on("keyup", function (e) {
		if (e.key === "Enter" || e.keyCode === 13) {
			console.log("entry")
			commandEntry.val("")
			// todo: push command to emit and uses ttfis
		}
	})

	executeBtn.click(function () {
		console.log("click executeBtn")
		commandEntry.val("")
		// todo: push command to emit and uses ttfis
	})
})
