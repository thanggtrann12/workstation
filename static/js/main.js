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
	let E_OK = 0
	let E_NOK = 1
	let isStandby = false
	let isShutdown = false
	const TIMER_5_MINS = 300000
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

	$("#power_button").click(function () {
		power_state = !power_state
		console.log(power_state)
		socket.emit("power_state", power_state)
		if (power_state == true) {
			$("#ign_button").css("color", "#A6E22E")
			$("#ign_label").css("color", "#A6E22E")
			$("#acc_button").css("color", "#A6E22E")
			$("#acc_label").css("color", "#A6E22E")
		}
	})

	$("#set_voltage_button").click(function () {
		var voltage = parseInt($("#input_voltage").val())
		socket.emit("setVoltage", voltage)
		$("#input_voltage").val("")
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

	var accState = false
	var wdState = false
	var ignState = false
	var opt2State = false

	function handleClick(buttonId, pin) {
		console.log("click:  ", buttonId, pin)
		$(buttonId).click(function () {
			var state = false
			switch (pin) {
				case "acc":
					state = !accState
					accState = state
					break
				case "wd":
					state = !wdState
					wdState = state
					break
				case "ign":
					state = !ignState
					ignState = state
					break
				case "opt2":
					state = !opt2State
					opt2State = state
					break
			}
			var stateValue = state ? E_OK : E_NOK
			socket.emit("request_to_arduino", { pin: pin, state: stateValue })
			socket.on("return_from_arduino", function (response) {
				if (response.ret === E_OK) {
					if (state) {
						$("#" + response.pin + "_button").css(
							"color",
							"#A6E22E",
						)
						$("#" + response.pin + "_label").css("color", "#A6E22E")
					} else {
						$("#" + response.pin + "_button").css("color", "red")
						$("#" + response.pin + "_label").css("color", "red")
					}
				}
			})
		})
	}

	handleClick("#acc_button", "acc")
	handleClick("#wd_button", "wd")
	handleClick("#ign_button", "ign")
	handleClick("#opt2_button", "opt2")

	socket.on("sync_data_from_arduino", function (data) {
		console.log(data[1], data[4], data[7], data[10])
		parseInt(data[1]) === 0 ? (accState = true) : (accState = false)
		parseInt(data[4]) === 0 ? (ignState = true) : (ignState = false)
		parseInt(data[7]) === 0 ? (wdState = true) : (wdState = false)
		parseInt(data[10]) === 0 ? (opt2State = true) : (opt2State = false)

		var pinMapping = {
			1: "acc",
			4: "ign",
			7: "wd",
			10: "opt2",
		}

		for (var i = 1; i < data.length; i += 3) {
			var digit = parseInt(data[i])
			var pin = pinMapping[i]

			if (digit === 0) {
				$("#" + pin + "_button").css("color", "#A6E22E")
				$("#" + pin + "_label").css("color", "#A6E22E")
			} else {
				$("#" + pin + "_button").css("color", "red")
				$("#" + pin + "_label").css("color", "red")
			}
		}
	})
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
		console.log("change")
		if (this.checked) {
			isRecording = true
		} else {
			isRecording = false
			var fileName = `recorded_text_${new Date().toISOString()}.pro`
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
		socket.emit("get_all_data")
		const lockstatus = JSON.parse(localStorage.getItem("lockstatus"))
		if (lockstatus != null) {
			if (
				lockstatus.lock != undefined &&
				lockstatus.session != undefined
			) {
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

	socket.on("message", function (message) {
		console.log("trace", message)
		put_trace_to_log_window(message)
	})

	socket.on("status", function (status) {
		$("#status").text(status)
		console.log($("#status").val())
	})

	socket.on("update_power_data", function (data) {
		$("#current_voltage").text(data["voltage_returned"])
		$("#current_ampe").text(data["current_returned"])
		if (data["voltage_returned"] != 0 && data["current_returned"] == 0) {
			updata_target_status("StandBy")
			isStandby = true
			isShutdown = true
		} else {
			isShutdown = false
			isStandby = false
			updata_target_status("Normal")
		}
	})

	socket.on("force_ul", function () {
		console.log("force call")
		if (loggedInUsers[0] == session_id) {
			showInformPopup()
		}
	})
	socket.on("list_user", function (user_loggined) {
		loggedInUsers = user_loggined
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
			force_timer = setTimeout(startCountdown, 1000)
		}
	}

	function showInformPopup() {
		countdownTime = defaultTime
		$("#countdown").text(countdownTime.toString())
		$("#timer").text(countdownTime.toString())
		$("#force_popup").css("display", "block")
		startCountdown()
	}
	function stopCountdown() {
		clearTimeout(timeoutId)
	}
	function hideInformPopup() {
		$("#force_popup").css("display", "none")
		stopCountdown(force_timer)
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
	$("#standby_buton").click(function () {
		$("#scc_trace").empty()
		handleTestCase("Set target into standby mode", "stand_by", "red")
		standby_timer.start()
	})

	$("#wakeup_buton").click(function () {
		handleTestCase("Wake up target", "wake_up", "#A6E22E")
		isShutdown = false
	})

	$("#shutdown_buton").click(function () {
		$("#scc_trace").empty()
		handleTestCase("Shutdown target", "stand_by", "red")
		shutdown_timer.start()
	})

	function handleTestCase(statusText, socketEvent, color) {
		if (power_state) {
			$("#status").text(statusText)
			socket.emit(socketEvent)
			$("#acc_label, #ign_label, #acc_button, #ign_button").css(
				"color",
				color,
			)
			var checkbox = document.getElementById("record_scc")
			checkbox.checked = true
			isRecording = true
		} else {
			$("#status").text("Power off. Turn the power on first")
		}
	}

	updata_target_status = (status) => {
		if (power_state) {
			if (status === "Normal") {
				$("#power_button, #power_label").css("color", "#A6E22E")
				$("#target_status").css("color", "#A6E22E")
			} else {
				$("#power_button, #power_label").css("color", "red")
				$("#target_status").css("color", "red")
			}
			$("#target_status").text(status.toUpperCase())
		} else {
			$("#target_status").text("SHUTDOWN")
			$("#target_status").css("color", "red")
		}
	}

	class Timer {
		constructor(duration, callback, condition, action) {
			this.duration = duration
			this.callback = callback
			this.action = action
			this.condition = condition
			this.timerId = null
			this.intervalId = null
		}

		start() {
			this.timerId = setTimeout(() => {
				clearInterval(this.intervalId) // Clear the interval when the main timer expires
				if (!this.condition()) {
					this.callback()
				}
			}, this.duration)
			this.intervalId = setInterval(() => {
				if (this.condition()) {
					console.log("condition met")
					this.action()
					var checkbox = document.getElementById("record_scc")
					checkbox.checked = false
					isRecording = false
					var fileName = `recorded_text_${new Date().toISOString()}.pro`
					var blob = new Blob([recordedText], {
						type: "text/plain;charset=utf-8",
					})
					var formData = new FormData()
					formData.append("file", blob, fileName)

					fetch("/result", {
						method: "POST",
						body: formData,
					})

					clearTimeout(this.timerId) // Clear the main timer if the condition is met
					clearInterval(this.intervalId)
				}
			}, 100) // Adjust the interval duration as needed
		}

		stop() {
			clearTimeout(this.timerId)
			clearInterval(this.intervalId)
		}
	}

	const shutdown_timer = new Timer(
		TIMER_5_MINS,
		() => {
			if (!isShutdown) {
				put_trace_to_log_window(
					"5 minutes over!!! Cannot shutdown !!! -> [FAILED]",
				)
			}
		},
		() => {
			return isShutdown
		},
		() => {
			put_trace_to_log_window("Shutdown!!! -> [PASSED]")
		},
	)

	const standby_timer = new Timer(
		TIMER_5_MINS,
		() => {
			if (!isStandby) {
				put_trace_to_log_window(
					"5 minutes over!!! Cannot stand by !!! -> [FAILED]",
				)
			}
		},
		() => {
			return isStandby
		},
		() => {
			put_trace_to_log_window("StandBy!!! -> [PASSED]")
		},
	)
})
