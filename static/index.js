$(document).ready(function () {
	var socket = io.connect("http://" + document.domain + ":" + location.port)
	let paraTable = {}
	let sepRegex = /((^|\W)+[^ ]*)/g
	let state = 0
	let suggestionList = []
	let lastcommandStr = []
	let counterCommand = 0
	let inSelection = false
	let commandTable = {
		root: new Trie({}),
		enum: {},
	}
	var command_entry = $("#command_entry")
	var chat_input = $("#chat_input")
	var sccTrace = $("#scc_log")
	var adbLog = $("#adb_log")
	var sccLines = []
	var ADBcommand = ""
	var accBtn = $("#acc_btn")
	var ignBtn = $("#ign_btn")
	var wdBtn = $("#wd_btn")
	var opt2Btn = $("#opt2_btn")
	var pwronBtn = $("#pwron_btn")
	var enventBtn = ["acc_btn", "ign_btn", "wd_btn", "opt2_btn", "pwron_btn"]
	var serverStatus = $("#server_status")
	var status = $("#status")
	var powersourceStatus = $("#power_source")
	var volValue = $("#voltage_value")
	var curValue = $("#current_value")
	var isPwrSourceConnected = false
	var isACCconnected = true
	var isIGNconnected = true
	var isWDconnected = false
	var isOPT2connected = false
	var setPwrBtn = $("#set_voltage_btn")
	document.getElementById("acc_btn").style.backgroundColor = "green"
	document.getElementById("ign_btn").style.backgroundColor = "green"

	socket.on("connect", function () {
		serverStatus.text("Connected")
	})

	socket.on("disconnect", function () {
		serverStatus.text("Disconnected")
	})
	socket.on("appContent", function (content) {
		var encodedStr = encodeURIComponent(content)
		$("#output").append("<div>" + encodedStr + "</div>")
	})

	socket.on("message", function (message) {
		console.log("message from ttfis", message)
		$("#scc_log").append(
			"<div><pre>" + $("<div/>").text(message).html() + "</pre></div>",
		)
		document.getElementById("scc_log").scrollTop =
			document.getElementById("scc_log").scrollHeight
	})
	socket.on("chat_message", function (message) {})
	socket.on("status", function (status_) {
		status.text("\n\r" + status_)
	})
	for (var i = 0; i < enventBtn.length; i++) {
		if (i < 2)
			document.getElementById(enventBtn[i + 2]).style.backgroundColor = "red"
		socket.on(enventBtn[i], function (data) {
			console.log(enventBtn[i] + " event received with data: " + data)
		})
	}

	socket.on("powervalue", function (data) {
		volValue.text(data["voltage"] + " V")
		curValue.text(data["current"] + " A")
	})

	socket.on("return_from_arduino", function (data) {
		setPropertyForElement(data)
	})

	$("#power_source").click(function () {
		if (isPwrSourceConnected != true) socket.emit("resetpowersource")
	})
	socket.on("powersourceStatus", function (data) {
		isPwrSourceConnected = data
		isPwrSourceConnected == true
			? (document.getElementById("power_source").style.backgroundColor =
					"green")
			: (document.getElementById("power_source").style.backgroundColor = "red")
		isPwrSourceConnected == true
			? powersourceStatus.text("ON")
			: powersourceStatus.text("OFF")
	})
	setPwrBtn.click(function () {
		var voltage = 0
		if (isPwrSourceConnected == true) {
			if ($("#voltage_to_set").val() != "") {
				voltage = parseInt($("#voltage_to_set").val())
				console.log(voltage)
				if (voltage >= 0 && voltage <= 14) {
					voltage = voltage
					powersourceStatus.text("SETED VOLTAGE")
				}
			} else {
				voltage = 0
				powersourceStatus.text("INVALID VOLTAGE")
			}
			socket.emit("setvoltagValue", voltage)
			$("#voltage_to_set").val("")
		} else {
			socket.emit("status", "POWER OFF")
			console.log("POWER OFF")
			powersourceStatus.text("OFF")
		}
	})
	function updateLastCommand(command) {
		let commandList = sccCommandStr.match(sepRegex)
		console.log("commandList", commandList)
		commandList.pop()
		commandList.push(command)
		commandList = commandList.map((ele) => ele.trim())
		sccCommandStr = commandList.join(" ")
		command_entry.val(sccCommandStr)
		sccLines += sccCommandStr + "\n"
		console.log("sccLines", sccLines)
	}

	async function loadParaTable() {
		let data = await $.get("http://" + location.host + "/GetCommandSet/")
		// Insert base command
		for (let cmd in data["root"]) {
			commandTable["root"].insert(cmd)
		}

		// Insert enum name value
		for (let name in data["enum"]) {
			commandTable["enum"][name] = new Trie({})
			for (let value of data["enum"][name]) {
				commandTable["enum"][name].insert(value)
			}
		}

		// Update parameter table
		paraTable = data["root"]
	}

	function parseInput() {
		let nameList = sccCommandStr.match(sepRegex)
		let baseCommand = nameList[0]
		let latestName = nameList.at(-1).trim()
		let pos = nameList.length
		return [baseCommand, latestName, pos]
	}

	async function doAutoComplete(event) {
		if (9 == event.keyCode) {
			event.preventDefault()
			// get suggestion
			if (!inSelection) {
				suggestionList = []
				console.log("get suggestion")
				let [baseCommand, name, pos] = parseInput()
				if (pos === 1) {
					suggestionList = commandTable["root"].find(name)
					console.log("suggestionList ", suggestionList)
				} else if (paraTable[baseCommand]) {
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
			socket.emit("sccCommand", sccCommandStr)
			lastcommandStr.push(sccCommandStr)
			sccTrace.append(sccCommandStr + "\n")
			sccLines = ""
			sccCommandStr = ""
			command_entry.val("")
			counterCommand = 0
		}
		if (38 == event.keyCode) {
			if (lastcommandStr.length > counterCommand) counterCommand += 1
			else counterCommand = 0
			command_entry.val(lastcommandStr[counterCommand])
		}
		if (40 == event.keyCode) {
			if (lastcommandStr.length > counterCommand) counterCommand -= 1
			else counterCommand = lastcommandStr.length
			command_entry.val(lastcommandStr[counterCommand < 0 ? 0 : counterCommand])
		}
	}
	$("#chat_input").on("keydown", function (event) {
		if (13 == event.keyCode) {
			let message = chat_input.val()
			console.log(message)
			if (message === "clear" || message == "cls") {
				$("#chatbox").empty()
				chat_input.val("")
			} else {
				socket.emit("chat_message", chat_input.val())
				$("#chatbox").append(
					"<div>" +
						$("<div/>")
							.text("You: " + message)
							.html() +
						"</div>",
				)
				chat_input.val("")
			}
		}
	})
	let sccCommandStr = ""
	$("#command_entry").on("input", function () {
		sccCommandStr = $(this).val()
	})

	$("#command_entry").on("keydown", function (event) {
		doAutoComplete(event)
	})

	$("#cmd").focus()
	$("#cmd").keypress(function (e) {
		if (e.which == 13) {
			var cmd = $("#cmd").val()
			if (cmd === "clear" || cmd === "cls") {
				$("#output").empty()
			} else {
				$("#output").append("<div>> " + cmd + "\n \r" + "</div>")
				socket.emit("app_input", cmd)
			}
			$("#cmd").val("")
		}
	})
	loadParaTable()

	$("#export_scc").click(function () {
		console.log("click")
		const text = $("#scc_log").text()
		console.log(text)
		let blob = new Blob([text], {
			type: "text/plain",
		})
		let filename = `${new Date().toISOString()}_SCC_Log.pro`
		saveAs(blob, filename) // sử dụng hàm saveAs của FileSaver.js
	})

	$("#export_adb").click(function () {
		console.log("click")
		const text = $("#output").text()
		console.log(text)
		let blob = new Blob([text], {
			type: "text/plain",
		})
		let filename = `${new Date().toISOString()}_ADB_Log.txt`
		saveAs(blob, filename) // sử dụng hàm saveAs của FileSaver.js
	})

	$("#clear_scc").click(function () {
		$("#scc_log").text("")
		console.log("clear")
	})
	accBtn.click(function () {
		isACCconnected = !isACCconnected
		console.log("accBtn click", isACCconnected)
		socket.emit(
			"request_to_arduino",
			(data = { device: "acc_btn", is_connected: isACCconnected }),
		)
	})
	ignBtn.click(function () {
		isIGNconnected = !isIGNconnected
		console.log("ignBtn click", isIGNconnected)
		socket.emit(
			"request_to_arduino",
			(data = { device: "ign_btn", is_connected: isIGNconnected }),
		)
	})
	wdBtn.click(function () {
		isWDconnected = !isWDconnected
		console.log("wdBtn click", isWDconnected)
		socket.emit(
			"request_to_arduino",
			(data = { device: "wd_btn", is_connected: isWDconnected }),
		)
	})
	opt2Btn.click(function () {
		isOPT2connected = !isOPT2connected
		console.log("opt2Btn click", isOPT2connected)
		socket.emit(
			"request_to_arduino",
			(data = { device: "opt2_btn", is_connected: isOPT2connected }),
		)
	})

	setPropertyForElement = (data) => {
		var device = data.device
		var isSet = data.resp
		console.log("data", data, device)
		if (isSet) {
			console.log("green")
			document.getElementById(device).style.backgroundColor = "green"
		} else {
			console.log("red")
			document.getElementById(device).style.backgroundColor = "red"
		}
	}

	$("#flash_btn").click(function () {
		console.log("flash click")
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

	$("#trace_btn").click(function () {
		console.log("click")
		var file_data = $("#file-trc-input").prop("files")[0]
		var form_data = new FormData()
		console.log(form_data)
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
})
