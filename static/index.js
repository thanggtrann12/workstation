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
	var accBtn = $("#acc_btn")
	var ignBtn = $("#ign_btn")
	var wdBtn = $("#wd_btn")
	var opt2Btn = $("#opt2_btn")
	var isSet = true
	var isPwrSourceConnected = false
	var isACCconnected = false
	var isIGNconnected = false
	var isWDconnected = false
	var isOPT2connected = false

	socket.on("connect", function () {
		serverStatus.text("Connected")
	})

	socket.on("message", function (message_) {
		let bIsAtBottom = true
		let traceArea = $("#log_ttfis")[0]

		if (
			traceArea.scrollHeight >
			traceArea.clientHeight + traceArea.scrollTop
		) {
			bIsAtBottom = false
		}

		$scope.$apply(function () {
			let lines = sccLines.concat(message_.split("\n"))
			sccLines = lines
		})

		if (bIsAtBottom) {
			traceArea.scrollTop =
				traceArea.scrollHeight - traceArea.clientHeight
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
	socket.on("ret", function (data) {
		isSet = data
		console.log(isSet)
	})
	socket.on("setVolValue", function (data) {
		console.log(data)
		socket.emit("setVolValue", data)
	})

	var eventList = ["ACC", "IGN", "WD", "OPT2"]
	var enventBtn = ["acc_btn", "wd_btn", "ign_btn", "opt2_btn"]
	// Đăng ký callback cho từng event
	for (var i = 0; i < eventList.length; i++) {
		document.getElementById(enventBtn[i]).style.backgroundColor = "red"
		socket.on(eventList[i], function (data) {
			console.log(eventList[i] + " event received with data: " + data)
		})
	}

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
		var voltage = 0
		if (isPwrSourceConnected != true) {
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
			openAlert(
				"Set power voltage ERROR",
				"Power source is not CONNECTED",
			)
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

	accBtn.click(function () {
		console.log("accBtn click")
		isACCconnected = !isACCconnected
		setPropertyForElement(
			"ACC",
			"acc_btn",
			["green", "red"],
			isACCconnected,
		)
	})
	ignBtn.click(function () {
		console.log("ignBtn click")
		isIGNconnected = !isIGNconnected

		setPropertyForElement(
			"IGN",
			"ign_btn",
			["green", "red"],
			isIGNconnected,
		)
	})
	wdBtn.click(function () {
		console.log("wdBtn click")
		isWDconnected = !isWDconnected
		setPropertyForElement("WD", "wd_btn", ["green", "red"], isWDconnected)
	})
	opt2Btn.click(function () {
		console.log("opt2Btn click")
		isOPT2connected = !isOPT2connected
		setPropertyForElement(
			"OPT2",
			"opt2_btn",
			["green", "red"],
			isOPT2connected,
		)
	})

	setPropertyForElement = (onEvent, element, backgroundColor, condition) => {
		console.log("set property", element, backgroundColor[0])
		// socket.emit("ret", "hello")
		if (isPwrSourceConnected != true) {
			socket.emit(onEvent, (data = condition))
			if (condition == true) {
				if (isSet == true) {
					openAlert("Turn " + onEvent, "ON")
					document.getElementById(element).style.backgroundColor =
						backgroundColor[0]
				} else {
					openAlert("Fail to turn " + onEvent, "ON")
					document.getElementById(element).style.backgroundColor =
						backgroundColor[1]
				}
			} else {
				if (isSet == true) {
					openAlert("Turn " + onEvent, "OFF")
					document.getElementById(element).style.backgroundColor =
						backgroundColor[1]
				} else {
					openAlert("Fail to turn " + onEvent, "OFF")
					document.getElementById(element).style.backgroundColor =
						backgroundColor[0]
				}
			}
		}
	}
})
