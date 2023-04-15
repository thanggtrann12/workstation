;(function ($) {
	"use strict"
	// begin of file
	var spinner = function () {
		setTimeout(function () {
			if ($("#spinner").length > 0) {
				$("#spinner").removeClass("show")
			}
		}, 1)
	}
	spinner()
	loadParaTable()
	// config socket io
	var socket = io.connect("http://" + document.domain + ":" + location.port)
	/* config for autocomplete */
	let paraTable = {}
	let sepRegex = /((^|\W)+[^ ]*)/g
	let state = 0
	let suggestionList = []
	let sccLines = ""
	let lastcommandStr = []
	let sccCommandStr = ""
	let dataDoautoComplete = []
	let counterCommand = 0
	let inSelection = false
	let commandTable = {
		root: new Trie({}),
		enum: {},
	}
	/* end config for autocomplete */

	/* auto complete beign*/
	async function loadParaTable() {
		dataDoautoComplete = await $.get(
			"http://" + location.host + "/GetCommandSet/",
		)
		// Insert base command
		for (let cmd in dataDoautoComplete["root"]) {
			commandTable["root"].insert(cmd)
		}
		console.log(dataDoautoComplete)
		// Insert enum name value
		for (let name in dataDoautoComplete["enum"]) {
			commandTable["enum"][name] = new Trie({})
			for (let value of dataDoautoComplete["enum"][name]) {
				commandTable["enum"][name].insert(value)
			}
		}
	}
	function updateLastCommand(command) {
		let commandList = sccCommandStr.match(sepRegex)
		console.log("commandList", commandList)
		commandList.pop()
		commandList.push(command)
		commandList = commandList.map((ele) => ele.trim())
		sccCommandStr = commandList.join(" ")
		sccLines += sccCommandStr + "\n"
		$("#command_entry").val(sccCommandStr)
		console.log("sccLines", sccLines)
	}

	paraTable = dataDoautoComplete["root"]

	async function doAutoComplete(event) {
		console.log(event.keyCode)
		if (9 == event.keyCode) {
			event.preventDefault()
			// get suggestion
			if (!inSelection) {
				suggestionList = []
				console.log("get suggestion")
				let [baseCommand, name, pos] = parseInput()
				console.log("parseInput", [baseCommand, name, pos])
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
			suggestionList = []
			inSelection = false
			state = 0
		}
		if (13 == event.keyCode) {
			socket.emit("sccCommand", sccCommandStr)
			lastcommandStr.push(sccCommandStr)
			put_trace_to_log_window(sccCommandStr + "\n")
			sccLines = ""
			sccCommandStr = ""
			$("#command_entry").val("")
			counterCommand = 0
		}
		if (38 == event.keyCode) {
			if (lastcommandStr.length > counterCommand) counterCommand += 1
			else counterCommand = 0
			$("#command_entry").val(lastcommandStr[counterCommand])
		}
		if (40 == event.keyCode) {
			if (lastcommandStr.length > counterCommand) counterCommand -= 1
			else counterCommand = lastcommandStr.length
			$("#command_entry").val(
				lastcommandStr[counterCommand < 0 ? 0 : counterCommand],
			)
		}
	}
	$("#command_entry").on("keydown", function (event) {
		doAutoComplete(event)
	})
	function parseInput() {
		let nameList = sccCommandStr.match(sepRegex)
		let baseCommand = nameList[0]
		let latestName = nameList.at(-1).trim()
		let pos = nameList.length
		return [baseCommand, latestName, pos]
	}
	// Update parameter table

	/* auto complete end*/

	/* hardware stub begin */
	var power_state = false

	$("#power_button").click(function () {
		power_state = !power_state
		socket.emit("power_state", power_state)
	})

	$("#set_voltage_button").click(function () {
		var voltage = 0
		if (power_state == true) {
			if ($("#input_voltage").val() != "") {
				voltage = parseInt($("#input_voltage").val())
				console.log(voltage)
				if (voltage >= 0 && voltage <= 14) {
					voltage = voltage
					$("#set_voltage_button").css("color", "green")
				}
			} else {
				voltage = 0
				$("#set_voltage_button").css("color", "red")
			}
			socket.emit("setvoltagValue", voltage)
			$("#input_voltage").val("")
		} else {
			$("#set_voltage_button").css("color", "red")
			console.log("POWER OFF")
			$("#input_voltage").val("")
		}
	})

	var sleep_state = false
	$("#sleep_button").click(function () {
		sleep_state = !sleep_state
		if (sleep_state == true) {
			$("#sleep_button").css("color", "green")
			$("#sleep_label").text("NORMAL")
			$("#sleep_label").css("color", "green")
		} else {
			$("#sleep_button").css("color", "lightgrey")
			$("#sleep_label").text("SLEEP")
			$("#sleep_label").css("color", "lightgrey")
		}
		socket.emit("power_state", sleep_state)
	})
	var isACC_on = true
	$("#acc_button").click(function () {
		isACC_on = !isACC_on
		socket.emit("request_to_arduino", {
			pin: "acc_button",
			state: isACC_on,
			label: "acc_label",
		})
	})
	var isWD_on = false
	$("#wd_off_button").click(function () {
		isWD_on = !isWD_on
		socket.emit("request_to_arduino", {
			pin: "wd_off_button",
			state: isWD_on,
			label: "wd_off_label",
		})
	})
	var isIGN_on = true
	$("#ign_button").click(function () {
		isIGN_on = !isIGN_on
		socket.emit("request_to_arduino", {
			pin: "ign_button",
			state: isIGN_on,
			label: "ign_label",
		})
	})
	var isOPT2_on = false
	$("#opt2_button").click(function () {
		isOPT2_on = !isOPT2_on
		socket.emit("request_to_arduino", {
			pin: "opt2_button",
			state: isOPT2_on,
			label: "opt2_label",
		})
	})

	function setStateHardware(button_id, button_label, state) {
		if (state == true) {
			$("#" + button_id).css("color", "green")
			$("#" + button_label).css("color", "green")
		} else {
			$("#" + button_id).css("color", "red")
			$("#" + button_label).css("color", "red")
		}
	}
	/* hardware stub end */
	/* flash and trace upload  begin*/
	$("#flash_button").click(function () {
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

	$("#trace_button").click(function () {
		var file_trc_data = $("#file-trc-input").prop("files")[0]
		var form_data = new FormData()
		form_data.append("file-trc", file_trc_data)
		$.ajax({
			url: "/upload",
			type: "POST",
			data: form_data,
			processData: false,
			contentType: false,
			success: function (response) {},
		})
	})

	/* flash and trace upload end*/

	/* log stub begin */
	function put_trace_to_log_window(message) {
		$("#scc_trace").append(
			"<div><pre>" + $("<div/>").text(message).html() + "</pre></div>",
		)
		document.getElementById("scc_trace").scrollTop =
			document.getElementById("scc_trace").scrollHeight
	}

	$("#clear_scc").click(function () {
		$("#scc_trace").empty()
	})

	$("#export_scc").click(function () {
		{
			const text = $("#scc_log").text()
			let blob = new Blob([text], {
				type: "text/plain",
			})
			let filename = `${new Date().toISOString()}_SCC_Log.pro`
			saveAs(blob, filename)
		}
	})
	/* log stub end */
	/* socket event handling begin */

	socket.on("connect", function () {
		console.log("connect")
	})
	socket.on("disconnect", function () {
		console.log("disconnect")
	})
	socket.on("powersourceStatus", function (status) {
		power_state = status
		if (power_state == true) {
			$("#power_button").css("color", "green")
			$("#power_label").text("ON")
			$("#power_label").css("color", "green")
		} else {
			$("#power_button").css("color", "red")
			$("#power_label").text("OFF")
			$("#power_label").css("color", "red")
		}
	})

	socket.on("appContent", function (content) {
		var encodedStr = encodeURIComponent(content)
		$("#output").append("<div>" + encodedStr + "</div>")
	})

	socket.on("message", function (message) {
		put_trace_to_log_window(message)
	})

	socket.on("return_from_arduino", function (data) {
		console.log("data from return_from_arduino", data)
		setStateHardware(data["pin"], data["label"], data["state"])
	})

	socket.on("status", function (status) {
		$("status").text(status)
	})

	socket.on("powervalue", function (data) {
		$("#current_voltage").text(data["voltage"])
		$("#current_ampe").text(data["current"])
	})
	/* socket event handling end */

	// end of file
})(jQuery)
