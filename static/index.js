$(document).ready(function () {
	var socket = io.connect("http://" + document.domain + ":" + location.port)
	let paraTable = {}
	let sepRegex = /((^|\W)+[^ ]*)/g
	let state = 0
	let suggestionList = []
	let inSelection = false
	let commandTable = {
		root: new Trie({}),
		enum: {},
	}
	var command_entry = $("#command_entry")
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
	var serverStatus = $("#status")
	var powersourceStatus = $("#power_source")
	var volValue = $("#voltage_value")
	var curValue = $("#current_value")
	var isPwrSourceConnected = false
	var isACCconnected = true
	var isIGNconnected = true
	var isWDconnected = false
	var isOPT2connected = false
	var isSet = false
	var setPwrBtn = $("#set_voltage_btn")
	socket.on("connect", function () {
		serverStatus.text("Connected")
	})

	socket.on("disconnect", function () {
		serverStatus.text("Disconnected")
	})

	socket.on("message", function (message) {
		sccTrace.append(message + "\n")
		console.log(message)
		document.getElementById("scc_log").scrollTop =
			document.getElementById("scc_log").scrollHeight
	})

	for (var i = 0; i < enventBtn.length; i++) {
		if (i < 2)
			document.getElementById(enventBtn[i + 2]).style.backgroundColor =
				"red"
		socket.on(enventBtn[i], function (data) {
			console.log(enventBtn[i] + " event received with data: " + data)
		})
	}

	socket.on("powervalue", function (data) {
		volValue.text(data["voltage"] + " V")
		curValue.text(data["current"] + " A")
	})

	socket.on("ret", function (data) {
		isSet = data
		console.log(isSet)
	})
	$("#power_source").click(function () {
		if (isPwrSourceConnected == false) socket.emit("turnPwrSource", true)
	})
	socket.on("powersourceStatus", function (data) {
		isPwrSourceConnected = data
		isPwrSourceConnected == true
			? (document.getElementById("power_source").style.backgroundColor =
					"green")
			: (document.getElementById("power_source").style.backgroundColor =
					"red")
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
		console.log("data", data["root"])
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
		console.log("paraTable", paraTable)
	}

	function parseInput() {
		let nameList = sccCommandStr.match(sepRegex)
		let baseCommand = nameList[0]
		let latestName = nameList.at(-1).trim()
		let pos = nameList.length
		return [baseCommand.toUpperCase(), latestName, pos]
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
						suggestionList =
							commandTable["enum"][enumName].find(name)
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
			console.log("ss", sccCommandStr)
			sccTrace.append(sccLines + "\n")
			sccLines = ""
			command_entry.val("")
		}
	}

	let sccCommandStr = ""
	$("#command_entry").on("input", function () {
		sccCommandStr = $(this).val()
	})

	$("#command_entry").on("keydown", function (event) {
		doAutoComplete(event)
	})
	$("#adb_log").on("keydown", function (event) {
		var text = adbLog.val().split("\n").pop()
		if (13 == event.keyCode) {
			if (text === "clear" || text === "cls") {
				console.log("clear")
				$("#adb_log").val("")
			} else {
				adbLog.text(text.split("\n"))
				ADBcommand = text.split("\n").pop()
				console.log("ADBcommand ", ADBcommand)
			}
		}
	})

	loadParaTable()

	$("#export_scc").click(function () {
		console.log("click")
		const text = $("#scc_log").val()
		console.log(text)
		let blob = new Blob([text], {
			type: "text/plain",
		})
		let filename = `${new Date().toISOString()}_SCC_Log.pro`
		saveAs(blob, filename) // sử dụng hàm saveAs của FileSaver.js
	})

	$("#export_adb").click(function () {
		console.log("click")
		const text = $("#adb_log").val()
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
	$("#flash_btn").click(function (file_type) {
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

	$("#trace_btn").click(function (file_type) {
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
})
