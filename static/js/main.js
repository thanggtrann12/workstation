$(document).ready(function () {
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
	let counterCommand = 0
	let inSelection = false
	let isLock = false
	let power_state = false
	let target_status = "normal"
	let commandTable = {
		root: new Trie({}),
		enum: {},
	}
	let loggedInUsers = []
	/* end config for autocomplete */

	/* auto complete beign*/
	function updateLastCommand(command) {
		let commandList = sccCommandStr.match(sepRegex)
		commandList.pop()
		commandList.push(command)
		commandList = commandList.map((ele) => ele.trim())
		console.log("commandList", commandList)
		sccCommandStr = commandList.join(" ")
		$("#command_entry").val(commandList.toString().replace(/[,.]/g, " "))
		console.log("command:  ", $("#command_entry").value)
		sccLines += sccCommandStr.toString().replace(/[,.]/g, " ")
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
		console.log(event.keyCode)
		if (9 == event.keyCode) {
			event.preventDefault()
			// get suggestion
			if (!inSelection) {
				suggestionList = []
				let [baseCommand, name, pos] = parseInput()
				if (pos === 1) {
					suggestionList = commandTable["root"].find(name)
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
			event.preventDefault()
			socket.emit("sccCommand", sccCommandStr)
			lastcommandStr.push(sccCommandStr.replace(/[,.]/g, " "))
			put_trace_to_log_window(sccCommandStr.replace(/[,.]/g, " "))
			sccLines = ""
			sccCommandStr = ""
			$("#command_entry").val("")
			counterCommand = 0
		}
		if (38 == event.keyCode) {
			if (lastcommandStr.length > counterCommand) counterCommand += 1
			else counterCommand = 0
			$("#command_entry").val(lastcommandStr[counterCommand])
			sccCommandStr = lastcommandStr[counterCommand]
		}
		if (40 == event.keyCode) {
			if (lastcommandStr.length > counterCommand) counterCommand -= 1
			else counterCommand = lastcommandStr.length
			$("#command_entry").val(
				lastcommandStr[counterCommand < 0 ? 0 : counterCommand],
			)
			sccCommandStr = lastcommandStr[counterCommand]
		}
	}
	let sccCommandStr = ""
	$("#command_entry").on("input", function () {
		sccCommandStr = $(this).val().toUpperCase()
	})
	$("#command_entry").on("keydown", function (event) {
		if (power_state) doAutoComplete(event)
	})
	// Update parameter table

	/* auto complete end*/

	/* hardware stub begin */

	var myVariable = localStorage.getItem("myVariable")
	$("#power_button").click(function () {
		power_state = !power_state
		console.log(power_state)
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
					$("#set_voltage_button").css("color", "#A6E22E")
					socket.emit("status", "Set voltage success!!")
				}
			} else {
				voltage = 0
				$("#set_voltage_button").css("color", "red")
				socket.emit("status", "Power is down, cannot set!!")
			}
			socket.emit("setvoltagValue", voltage)
			$("#input_voltage").val("")
		} else {
			$("#set_voltage_button").css("color", "red")
			console.log("POWER OFF")
			$("#input_voltage").val("")
		}
		socket.emit("status", "Ready")
	})
	var isChatopen = false
	$("#note_button").click(function () {
		console.log("chat")
		isChatopen = !isChatopen
		isChatopen == false
			? ($("#chat_popup").css("display", "none"),
			  $("#note_label").css("color", "white"),
			  $("#note_button").css("color", "white"))
			: ($("#chat_popup").css("display", "block"),
			  $("#note_label").css("color", "#A6E22E"),
			  $("#note_button").css("color", "#A6E22E"))
	})
	var chat_message = ""
	$("#chat_entry").on("input", function () {
		chat_message = $(this).val()
	})

	$("#chat_entry").on("keydown", function (event) {
		if (event.keyCode == 13) {
			event.preventDefault()
			if (chat_message === "clear") {
				$("#note_box").empty()
				$("#chat_entry").val("")
			} else {
				document.getElementById("note_box").scrollTop =
					document.getElementById("note_box").scrollHeight
				$("#note_box").append(
					"<div><pre>" +
						$("<div/>")
							.text(chat_message + "\n")
							.html() +
						"</pre></div>",
				)
				$("#chat_entry").val("")
			}
			chat_message = ""
		}
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
		console.log("ign_button")
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
		console.log(button_id, button_label, state)
		if (state == true) {
			$("#" + button_id).css("color", "#A6E22E")
			$("#" + button_label).css("color", "#A6E22E")
		} else {
			$("#" + button_id).css("color", "red")
			$("#" + button_label).css("color", "red")
		}
	}
	/* hardware stub end */
	/* flash and trace upload  begin*/
	$("#flash_button").click(function () {
		var file_data = $("#file-dnl-input").prop("files")[0]
		console.log("flash..")
		if (file_data == undefined || file_data == null) {
			$("#status").text("Files is empty")
		}
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
		console.log("trace ...")
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
		if (isPausing) {
			// do not thing
		} else {
			$("#scc_trace").append(
				"<div><pre>" +
					$("<div/>")
						.text("\r\n" + message)
						.html() +
					"</pre></div>",
			)
			document.getElementById("scc_trace").scrollTop =
				document.getElementById("scc_trace").scrollHeight
			if (isRecording) {
				recordedText += message
			} else {
				recordedText = ""
			}
		}
	}

	$("#clear_scc").click(function () {
		$("#scc_trace").empty()
	})

	$("#export_scc").click(function () {
		console.log("export")
		{
			const text = $("#scc_trace").text()
			let blob = new Blob([text], {
				type: "text/plain",
			})
			let filename = `${new Date().toISOString()}_SCC_Log.pro`
			saveAs(blob, filename)
		}
	})
	$("#log_out_button").click(function () {
		console.log("loggedInUsers[0]", loggedInUsers[0])
		let index = loggedInUsers.indexOf(session_id)
		if (index > -1) {
			loggedInUsers.splice(index, 1)
		}
		socket.emit("lock", false)
		window.location.href = "/logout"
	})
	var isRecording = false
	var recordedText = ""

	$("#record_scc").change(function () {
		if (this.checked) {
			isRecording = true
		} else {
			isRecording = false
			var fileName = "recorded_text.txt"
			var blob = new Blob([recordedText], {
				type: "text/plain;charset=utf-8",
			})
			saveAs(blob, fileName)
		}
	})
	var isPausing = false
	$("#pause_scc").change(function () {
		if (this.checked) {
			isPausing = true
		} else {
			isPausing = false
		}
	})
	/* log stub end */
	/* socket event handling begin */

	socket.on("connect", function () {
		console.log("connect")
		const lockstatus = JSON.parse(localStorage.getItem("lockstatus"))
		if (lockstatus != null) {
			if (lockstatus.lock != undefined && lockstatus.session != undefined) {
				isLock = lockstatus.lock
				if (lockstatus.session == session_id) {
					loggedInUsers[0] = lockstatus.session
					$("#lock_button").css("display", "block")
					console.log("admin lock")
					socket.emit("lock", isLock)
					isLock
						? $("#lock_button").text("Unlock")
						: $("#lock_button").text("Lock")
				} else if (loggedInUsers[0] == "") {
					loggedInUsers[0] = lockstatus.session
				}
			}
		}
		socket.emit("lock", isLock)
		isLock == true
			? $("#lock_status").text("Locked")
			: $("#lock_status").text("Unlock")
	})
	socket.on("disconnect", function () {
		console.log("disconnect")
	})
	socket.on("is_power_turn_on", function (status) {
		power_state = status
		console.log("is_power_turn_on", power_state)
		if (power_state == true) {
			$("#power_button").css("color", "#A6E22E")
			$("#power_button").text("ON")
			$("#power_label").css("color", "#A6E22E")
		} else {
			$("#power_button").css("color", "red")
			$("#power_button").text("OFF")
			$("#power_label").css("color", "red")
		}
	})

	socket.on("message", function (message) {
		console.log("trace", message)
		put_trace_to_log_window(message)
	})

	socket.on("return_from_arduino", function (data) {
		console.log("data from return_from_arduino", data)
		setStateHardware(data["pin"], data["label"], data["state"])
	})

	socket.on("status", function (status) {
		$("#status").text(status)
		console.log($("#status").val())
	})

	socket.on("power_source_data", function (data) {
		$("#current_voltage").text(data["voltage_returned"])
		$("#current_ampe").text(data["current_returned"])
		if (data["current_returned"] == 0) {
			$("#ign_button").css("color", "red")
			$("#ign_label").css("color", "red")
			$("#acc_button").css("color", "red")
			$("#acc_label").css("color", "red")
			updata_target_status("standby")
		} else {
			updata_target_status("normal")
		}
	})

	socket.on("force_ul", function () {
		console.log("force call")
		// $("#lock_button").css("display", "none")
		// $("[id]").removeClass("disable-click")
		if (loggedInUsers[0] == session_id) {
			showInformPopup()
		}
	})
	socket.on("list_user", function (user_loggined) {
		loggedInUsers = user_loggined
		console.log("loggedInUsers", loggedInUsers)
	})
	/* handling user login end*/
	socket.on("lock", function (lock_status) {
		isLock = lock_status
		console.log("session_id", session_id, "lock_status", lock_status)
		localStorage.setItem(
			"lockstatus",
			JSON.stringify({
				lock: lock_status,
				session: loggedInUsers[0],
			}),
		)
		if (loggedInUsers[0] == session_id) {
			console.log("admin call lock")
			$("[id]").css("pointer-events", "pointer")
		}
		if (loggedInUsers[0] != session_id) {
			if (isLock) {
				console.log("lock")

				$("[id]").addClass("disable-click")
				$("#lock_button").removeClass("disable-click")
				$("#lock_button").text("Force Unlock")
				$("#note_button").removeClass("disable-click")
				$("#note_label").removeClass("disable-click")
				$("#chat_entry").removeClass("disable-click")
			} else {
				console.log("unlock")
				$("[id]").removeClass("disable-click")
			}
		}
		if (loggedInUsers[0] == undefined) {
			loggedInUsers[0] = "admin"
		}
		isLock == true
			? $("#lock_status").text(
					"Locked by: " + loggedInUsers[0].toString().toUpperCase(),
			  )
			: $("#lock_status").text("Unlock")
	})

	$("#lock_button").click(function () {
		console.log("lock", session_id, loggedInUsers[0])
		if (loggedInUsers[0] == session_id) {
			isLock = !isLock
			$("#lock_button").css("display", "block")
			console.log("admin lock")
			socket.emit("lock", isLock)
			isLock == true
				? $("#lock_button").text("Unlock")
				: $("#lock_button").text("Lock")
		} else {
			if ($("#lock_button").text() === "Force Unlock" && isLock == true) {
				socket.emit("force_ul")
				console.log("Force Unlock")
			}
		}
		localStorage.setItem(
			"lockstatus",
			JSON.stringify({
				lock: isLock,
				session: loggedInUsers[0],
			}),
		)
		isLock == true
			? $("#lock_status").text(
					"Locked by  " +
						loggedInUsers[0].toString().toUpperCase().toUpperCase(),
			  )
			: $("#lock_status").text("Unlock")
	})

	let timeoutId
	let defaultTime = 5
	var countdownTime = 0

	$("#confirmButton").click(function () {
		if (loggedInUsers[0] == session_id) {
			$("#lock_button").text("Lock")
			hideInformPopup()
		} else {
			$("#lock_button").css("display", "none")
			$("[id]").removeClass("disable-click")
		}

		isLock = false
		localStorage.setItem(
			"lockstatus",
			JSON.stringify({
				lock: isLock,
				session: loggedInUsers[0],
			}),
		)
		socket.emit("lock", isLock)
	})
	$("#rejectButton").click(function () {
		localStorage.setItem(
			"lockstatus",
			JSON.stringify({
				lock: isLock,
				session: loggedInUsers[0],
			}),
		)
		socket.emit("lock", true)
		hideInformPopup()
	})
	function startCountdown() {
		countdownTime--
		$("#countdown").text(countdownTime.toString())
		$("#timer").text(countdownTime.toString())
		if (countdownTime == 0) {
			$("#lock_button").css("display", "none")
			$("[id]").removeClass("disable-click")
			isLock = false
			localStorage.setItem(
				"lockstatus",
				JSON.stringify({
					lock: isLock,
					session: loggedInUsers[0],
				}),
			)

			socket.emit("lock", isLock)
			hideInformPopup()
		} else {
			timeoutId = setTimeout(startCountdown, 1000)
		}
	}

	function stopCountdown() {
		clearTimeout(timeoutId)
	}

	function showInformPopup() {
		countdownTime = defaultTime
		$("#countdown").text(countdownTime.toString())
		$("#timer").text(countdownTime.toString())
		$("#force_popup").css("display", "block")
		startCountdown()
	}

	function hideInformPopup() {
		$("#force_popup").css("display", "none")
		stopCountdown()
	}
	shortToBat = (periDevice) => {
		socket.emit("shortToBat", periDevice)
	}
	shortToGround = (periDevice) => {
		socket.emit("shortToGround", periDevice)
	}

	$("#save_note").click(function () {
		{
			const text = $("#note_box").text()
			let blob = new Blob([text], {
				type: "text/plain",
			})
			let filename = `${new Date().toISOString()}_note${session_id}.pro`
			saveAs(blob, filename)
		}
	})
	// $("#send_note").click(function () {
	// 	{
	// 		const text = $("#note_box").text()
	// 		let blob = new Blob([text], {
	// 			type: "text/plain",
	// 		})
	// 		let filename = `${new Date().toISOString()}_note${session_id}.pro`
	// 		saveAs(blob, filename)
	// 	}
	// })

	$("#standby_buton").click(function () {
		socket.emit("status", "Set target into standby mode")
		socket.emit("request_to_arduino", {
			pin: "acc_button",
			state: false,
			label: "acc_label",
		})
		socket.emit("request_to_arduino", {
			pin: "ign_button",
			state: false,
			label: "ign_label",
		})
		target_status = "wait"
	})

	updata_target_status = (status) => {
		if (status === "standby") {
			$("#target_status").css("color", "red")
			$("#ign_button").css("color", "red")
			$("#ign_label").css("color", "red")
			$("#acc_button").css("color", "red")
			$("#acc_label").css("color", "red")
			isIGN_on = false
			isACC_on = false
			target_status = "standby"
		}
		if (status === "normal") {
			$("#target_status").css("color", "green")
			target_status = "normal"
		}
		$("#target_status").text(status.toUpperCase())
	}
})
