let paraTable = {}
let sepRegex = /((^|\W)+[^ ]*)/g
let state = 0
let suggestionList = []
let ttfis_cmd_lines = ""
let ttfis_cmd = ""
let lastcommandStr = []
let recordedText = ""
let isRecording = false
let isPausing = false
let counterCommand = 0
let inSelection = false
let commandTable = {
	root: new Trie({}),
	enum: {},
}

function updateLastCommand(command) {
	let commandList = ttfis_cmd.match(sepRegex)
	commandList.pop()
	commandList.push(command)
	commandList = commandList.map((ele) => ele.trim())
	console.log("commandList", commandList)
	ttfis_cmd = commandList.join(" ").replace(/\n/g, "")
	$("#command_entry").val(ttfis_cmd)
	ttfis_cmd_lines += ttfis_cmd
}

async function loadParaTable() {
	let data = await $.get("http://" + location.host + "/getTTFisCmd/")
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
	let nameList = ttfis_cmd.match(sepRegex)
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
		console.log(ttfis_cmd)
		updateTtfiData(ttfis_cmd)
		socket.emit("submit_ttfis_cmd", ttfis_cmd)
		lastcommandStr.push(ttfis_cmd.replace(/\n/g, ""))
		ttfis_cmd_lines = ""
		ttfis_cmd = ""
		$("#command_entry").val("")
		counterCommand = 0
	}
	if (38 == event.keyCode) {
		if (lastcommandStr.length > counterCommand) counterCommand += 1
		else counterCommand = 0
		$("#command_entry").val(lastcommandStr[counterCommand])
		ttfis_cmd = lastcommandStr[counterCommand]
	}
	if (40 == event.keyCode) {
		if (lastcommandStr.length > counterCommand) counterCommand -= 1
		else counterCommand = lastcommandStr.length
		$("#command_entry").val(
			lastcommandStr[counterCommand < 0 ? 0 : counterCommand],
		)
		ttfis_cmd = lastcommandStr[counterCommand]
	}
}

function updateTtfiData(data) {
	if (isPausing) {
		// do not thing
	} else {
		$("#scc_trace").append(
			"<div><pre>" +
				$("<div/>")
					.text(data + "\r\n")
					.html() +
				"</pre></div>",
		)
		document.getElementById("scc_trace").scrollTop =
			document.getElementById("scc_trace").scrollHeight
		if (isRecording) {
			recordedText += data + "\r\n"
			console.log(recordedText)
		} else {
			recordedText = ""
		}
	}
}

function saveLog(testcase, result, counter_standby_test) {
	let text = $("#scc_trace").text()
	var fileName = `recorded_${testcase}_${result}_time_${counter_standby_test}.pro`
	var blob = new Blob([text], {
		type: "text/plain;charset=utf-8",
	})
	var formData = new FormData()
	formData.append("file", blob, fileName)

	fetch("/result", {
		method: "POST",
		body: formData,
	})
}
