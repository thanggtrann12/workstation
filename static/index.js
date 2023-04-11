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
	var traceArea = $("#log_ttfis")
	var isSet = true
	var isPwrSourceConnected = false
	var isACCconnected = true
	var isIGNconnected = true
	var isWDconnected = false
	var isOPT2connected = false
	var inSelection = false
	socket.on("connect", function () {
		serverStatus.text("Connected")
	})

	socket.on("message", function (message) {
		sccLines.append(message + "\n")
		traceArea.val(sccLines)
		console.log(message)
		document.getElementById("log_ttfis").scrollTop =
			document.getElementById("log_ttfis").scrollHeight
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
		socket.emit("message", data)
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
	var enventBtn = ["acc_btn", "ign_btn", "wd_btn", "opt2_btn"]
	// Đăng ký callback cho từng event
	for (var i = 0; i < eventList.length; i++) {
		if (i < 2)
			document.getElementById(enventBtn[i + 2]).style.backgroundColor = "red"
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

	$("#clear_scc").click(function () {
		document.getElementById("log_ttfis").value = ""
		console.log("clear")
	})

	$("#export_scc").click(function () {
		const text = traceArea.value
		let blob = new Blob([text], {
			type: "text/plain",
		})
		let downloader = $("#downloaderId")[0]
		downloader.href = window.URL.createObjectURL(blob)
		downloader.download = `${new Date().toISOString()}_Terminal_log.pro`
		downloader.click()
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
			traceArea.append(commandEntry.val() + "\n")
			commandEntry.val("")
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
		setPropertyForElement("ACC", "acc_btn", ["green", "red"], isACCconnected)
	})
	ignBtn.click(function () {
		console.log("ignBtn click")
		isIGNconnected = !isIGNconnected

		setPropertyForElement("IGN", "ign_btn", ["green", "red"], isIGNconnected)
	})
	wdBtn.click(function () {
		console.log("wdBtn click")
		isWDconnected = !isWDconnected
		setPropertyForElement("WD", "wd_btn", ["green", "red"], isWDconnected)
	})
	opt2Btn.click(function () {
		console.log("opt2Btn click")
		isOPT2connected = !isOPT2connected
		setPropertyForElement("OPT2", "opt2_btn", ["green", "red"], isOPT2connected)
	})

	setPropertyForElement = (onEvent, element, backgroundColor, condition) => {
		console.log("set property", element, backgroundColor[0])
		// socket.emit("ret", "hello")
		if (isPwrSourceConnected != true) {
			socket.emit(onEvent, (data = condition))
			if (condition == true) {
				if (isSet == true) {
					document.getElementById(element).style.backgroundColor =
						backgroundColor[0]
				} else {
					document.getElementById(element).style.backgroundColor =
						backgroundColor[1]
				}
			} else {
				if (isSet == true) {
					document.getElementById(element).style.backgroundColor =
						backgroundColor[1]
				} else {
					document.getElementById(element).style.backgroundColor =
						backgroundColor[0]
				}
			}
		}
	}

	$("#upload-dnl").click(function (file_type) {
		console.log("click")
		var file_data = $("#file-dnl-input").prop("files")[0]
		var form_data = new FormData()
		form_data.append("file-dnl", file_data)
		$.ajax({
			url: "/upload",
			type: "POST",
			data: form_data,
			processData: false,
			contentType: false,
			success: function (response) {},
		})
	})

	$("#upload-trc").click(function (file_type) {
		console.log("click")
		var file_data = $("#file-trc-input").prop("files")[0]
		var form_data = new FormData()
		form_data.append("file-trc", file_data)
		$.ajax({
			url: "/upload",
			type: "POST",
			data: form_data,
			processData: false,
			contentType: false,
			success: function (response) {},
		})
	})
	var sepRegex = /((^|\W)+[^ ]*)/g
	var state = 0
	// const paraTable = data["root"]

	parseInput = () => {
		let nameList = sccCommandStr.match(sepRegex)
		let baseCommand = nameList[0]
		let latestName = nameList.at(-1).trim()
		let pos = nameList.length
		return [baseCommand, latestName, pos]
	}
	function updateLastCommand(command) {
		let commandList = sccCommandStr.match(sepRegex)
		commandList.pop()
		commandList.push(command)
		commandList = commandList.map((ele) => ele.trim())
		sccCommandStr = commandList.join(" ")
	}
	function DoAutoComplete(event) {
		if (9 == event.keyCode) {
			event.preventDefault()
			// get suggestion
			if (!inSelection) {
				suggestionList = []
				let [baseCommand, name, pos] = parseInput()
				console.log(baseCommand)
				if (pos === 1) {
					suggestionList = commandTable["root"].find(name)
				} else if (paraTable[baseCommand]) {
					// pos - 2 is to compensate the base command and zero-index array
					let enumName = paraTable[baseCommand][pos - 2]
					if (enumName) {
						suggestionList = commandTable["enum"][enumName].find(name)
					}
				}
				inSelection = true
			}

			// cycle through suggestion
			if (suggestionList.length != 0) {
				updateLastCommand(suggestionList[state])
				state = (state + 1) % suggestionList.length
			}
		} else {
			inSelection = false
			state = 0
		}

		if (13 == event.keyCode) {
			console.log(sccCommandStr)
		}
	}
})
